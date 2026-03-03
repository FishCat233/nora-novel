from dataclasses import dataclass
import logging
from typing import Optional, Callable, Literal, Union, Generator, Any, TypedDict

from openai import OpenAI

from .pipeline_tool import PipelineTool
from .tools import Tool, tools
from .types import ChatMessage, ToolCall, CommonChatMessage, ToolCallMessage


# TODO: 写恶心了🤢 重写吧


@dataclass
class ToolCallHook:
    time: Literal["before", "after"]
    func: Callable[
        ["NoraAgent", ToolCall], bool
    ]  # 返回 True 表示继续执行，返回 False 表示终止执行


type StreamEvent = Union[StreamContentEvent, StreamFinalEvent]


class StreamContentEvent(TypedDict):
    type: Literal["content"]
    data: str


class StreamFinalEvent(TypedDict):
    type: Literal["final"]
    data: CommonChatMessage


class NoraAgent:
    def __init__(self, client: OpenAI, system_prompt=None, inital_message=None):
        if inital_message is None:
            inital_message = []

        self.client: OpenAI = client
        self.system_prompt = system_prompt
        self.messages: list[ChatMessage] = [
            CommonChatMessage(role="system", content=self.system_prompt)
        ] + inital_message
        self.allow_tools = None

        self._tool_call_hook: dict[str, ToolCallHook] = {}

    def setup_pipeline(self, pipeline: PipelineTool) -> "NoraAgent":
        self.system_prompt = pipeline.system_prompt

        has_system_prompt = False
        for message in self.messages:
            if message.role == "system":
                has_system_prompt = True
                message.content = self.system_prompt
        if not has_system_prompt:
            self.messages.insert(
                0, CommonChatMessage(role="system", content=self.system_prompt)
            )

        self.allow_tools = [
            t for t in tools if t["function"]["name"] in pipeline.allowed_tools
        ]

        return self

    def add_tool_call_hook(self, name: str, hook: ToolCallHook):
        self._tool_call_hook[name] = hook

    def remove_tool_call_hook(self, name: str) -> Optional[ToolCallHook]:
        return self._tool_call_hook.pop(name, None)

    def step(self, prompt=None):
        """
        单步运行 agent
        Args:
            prompt:

        Returns: "finished" 表示不调用工具（结束回答），否则为调用的工具名

        """

        if prompt:
            self.messages.append(CommonChatMessage(role="user", content=prompt))

        message = self._single_step()

        # 把 assistant 消息加入历史
        self.messages.append(message)

        if not message.tool_calls:
            return "finished"

        return message.tool_calls

    def step_stream(self, prompt=None):
        """
        流式 step
        Args:
            prompt: 提示词

        Returns: 生成器
        """

        if prompt:
            self.messages.append(CommonChatMessage(role="user", content=prompt))

        generator = self._single_step_stream()
        final_message: Optional[CommonChatMessage] = None
        for event in generator:
            if event["type"] == "final":
                final_message = event["data"]
            else:
                yield event

        self.messages.append(final_message)

        if final_message.tool_calls:
            yield {"type": "tool_calls", "data": final_message.tool_calls}
        else:
            yield {"type": "final"}

    def _execute_tool_call(self, tool_call: ToolCall) -> None:
        """
        使用工具完成 tool_call，并将结果加入到 messages 中
        Args:
            tool_call: tool_call

        Returns: None
        """
        prefix_hook = [
            hook for hook in self._tool_call_hook.values() if hook.time == "before"
        ]
        postfix_hook = [
            hook for hook in self._tool_call_hook.values() if hook.time == "after"
        ]

        if prefix_hook:
            for hook in prefix_hook:
                if not hook.func(self, tool_call):
                    return

        name = tool_call["name"]
        args = tool_call["arguments"]

        result = Tool.dispatch(name, args)

        if postfix_hook:
            for hook in postfix_hook:
                if not hook.func(self, tool_call):
                    return

        self.messages.append(
            ToolCallMessage(
                role="tool",
                content=str(result),
                tool_call_id=tool_call["id"],
                tool_call_name=tool_call["name"],
            )
        )

    def _single_step(self):
        """
        进行单步对话。

        Returns: message
        """
        response = self.client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2",
            messages=self.messages,
            tools=self.allow_tools
            if self.allow_tools
            else tools,  # 如果没有限制工具，则默认可以使用所有工具
            max_tokens=5120,
            extra_body={"thinking_budget": 2048},
        )

        logging.info(f"使用 Token: {response.usage.total_tokens}")

        return response.choices[0].message

    def _single_step_stream(self) -> Generator[StreamEvent, Any, None]:
        """
        流式单步对话生成器。
        Yields:
            event(dict): 包含 type 和 data 的片段
                - {'type': 'content', 'data': str}   # 文本内容
                - {'type': 'final', 'data': dict} # 结束会话后的完整的消息
        Returns: 事件的生成器
        """
        response = self.client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2",
            messages=self.messages,
            tools=self.allow_tools
            if self.allow_tools
            else tools,  # 如果没有限制工具，则默认可以使用所有工具
            max_tokens=5120,
            extra_body={"thinking_budget": 2048},
        )

        collected_content = ""
        collected_tool_calls = {}

        for chunk in response:
            delta = chunk.choices[0].delta

            if delta.content:
                collected_content += delta.content
                yield StreamContentEvent(
                    type="content",
                    data=delta.content,
                )

            if delta.tool_calls:
                for tool_chunk in delta.tool_calls:
                    idx = tool_chunk.index
                    if idx not in collected_tool_calls:
                        collected_tool_calls[idx] = {
                            "id": tool_chunk.id,
                            "name": tool_chunk.function.name,
                            "arguments": tool_chunk.function.arguments or "",
                        }
                    else:
                        if tool_chunk.function.arguments:
                            collected_tool_calls[idx]["arguments"] = (
                                tool_chunk.function.arguments
                            )

            if chunk.choices[0].finish_reason:
                break

        tool_calls = []
        for tc in collected_tool_calls.values():
            tool_calls.append(
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                }
            )

        final_message = CommonChatMessage(
            role="assistant",
            content=collected_content,
            tool_calls=tool_calls if tool_calls else None,
        )

        yield StreamFinalEvent(
            type="final",
            data=final_message,
        )
