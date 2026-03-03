import json
from dataclasses import dataclass
import logging
from typing import Optional, Literal, Union

from openai import OpenAI

from .pipeline_tool import PipelineTool
from .tools import Tool, tools
from .types import ChatMessage, ToolCallJson, CommonChatMessage, ToolCallMessage


# TODO: 写恶心了🤢 重写吧


type StreamEvent = Union[StreamContentEvent, StreamFinalEvent]


@dataclass
class StreamContentEvent:
    data: str
    type: Literal["content"] = "content"


@dataclass
class StreamFinalEvent:
    data: CommonChatMessage
    type: Literal["final"] = "final"


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

        self.pending_tool: list[ToolCallJson] = []

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
        final_event: Optional[StreamFinalEvent] = None

        for event in generator:
            if isinstance(event, StreamFinalEvent):
                final_event = event
                continue
            else:
                yield event

        if final_event is None:
            raise RuntimeError("No final event")

        self.messages.append(final_event.data)

        if final_event.data.tool_calls:
            self.pending_tool.extend(final_event.data.tool_calls)

        yield final_event

    def execute_tool_call(
        self, tool_call: ToolCallJson, skip_content: str = None
    ) -> None:
        """
        使用工具完成 tool_call，并将结果加入到 messages 中，然后消耗 pending_list 中的 tool_call
        Args:
            tool_call: tool_call
            skip_content: 如果不为空，则使用此内容替换工具的调用内容

        Returns: None
        """
        if skip_content:
            self.messages.append(
                ToolCallMessage(
                    role="tool",
                    content=skip_content,
                    tool_call_id=tool_call["id"],
                    tool_call_name=tool_call["function"]["name"],
                )
            )
            self.pending_tool.remove(tool_call)
            return

        name = tool_call["function"]["name"]
        args = json.loads(tool_call["function"]["arguments"])

        result = Tool.dispatch(name, args)

        self.messages.append(
            ToolCallMessage(
                role="tool",
                content=str(result),
                tool_call_id=tool_call["id"],
                tool_call_name=name,
            )
        )
        self.pending_tool.remove(tool_call)

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

    def _single_step_stream(self):
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
            stream=True,
            max_tokens=5120,
            extra_body={"thinking_budget": 2048},
        )

        collected_content = ""
        collected_tool_calls = {}

        for chunk in response:
            delta = chunk.choices[0].delta

            logging.debug(f"收到 chunk: {delta}")

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
                            collected_tool_calls[idx]["arguments"] += (
                                tool_chunk.function.arguments
                            )

            if chunk.choices[0].finish_reason:
                break

        tool_calls: list[ToolCallJson] = []
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
