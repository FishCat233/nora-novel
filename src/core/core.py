import logging
import json
from typing import Optional, Callable, Any

from openai import OpenAI

from .pipeline_tool import PipelineTool
from .tools import Tool, tools
from .types import ChatMessage, CustomMessage


class NoraAgent:
    def __init__(self, client: OpenAI, system_prompt=None, inital_message=None):
        if inital_message is None:
            inital_message = []

        self.client: OpenAI = client
        self.system_prompt = system_prompt
        self.messages: list[ChatMessage] = [
            CustomMessage(role="system", content=self.system_prompt)
        ] + inital_message
        self.allow_tools = None

    def setup_pipeline(self, pipeline: PipelineTool) -> "NoraAgent":
        self.system_prompt = pipeline.system_prompt

        has_system_prompt = False
        for message in self.messages:
            if message.role == "system":
                has_system_prompt = True
                message.content = self.system_prompt
        if not has_system_prompt:
            self.messages.insert(
                0, CustomMessage(role="system", content=self.system_prompt)
            )

        self.allow_tools = [
            t for t in tools if t["function"]["name"] in pipeline.allowed_tools
        ]

        return self

    def chat(self, prompt: str) -> Optional[ChatMessage]:
        """
        进行 ReAct 对话，解决用户的问题。

        会话过程中会记录 message
        Args:
            prompt: 提示词

        Returns: 最终回复
        """
        self.messages.append(CustomMessage(role="user", content=prompt))

        for _ in range(15):
            message = self._single_step()

            # 把 assistant 消息加入历史
            self.messages.append(message)

            # 检查工具调用
            if not message.tool_calls:
                return message

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                # 如果是 function 类型的工具
                result = Tool.dispatch(name, args)

                self.messages.append(
                    CustomMessage(
                        role="tool",
                        content=str(result),
                        tool_call_id=tool_call.id,
                        tool_call_name=tool_call.function.name,
                    )
                )

        logging.error("超出轮次数量.")

        return None

    def step(self, prompt=None):
        """
        单步运行 agent
        Args:
            prompt:

        Returns: "finished" 表示不调用工具（结束回答），否则为调用的工具名

        """

        if prompt:
            self.messages.append(CustomMessage(role="user", content=prompt))

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
            self.messages.append(CustomMessage(role="user", content=prompt))

        generator = self._single_step_stream()
        final_message: Optional[CustomMessage] = None
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

    def use_tool_call(
        self,
        tool_call,
        prefix_hook: Callable[[Any], bool] = None,
        postfix_hook: Callable[[Any], bool] = None,
    ) -> None:
        """
        使用工具完成 tool_call，并将结果加入到 messages 中
        Args:
            tool_call: tool_call
            prefix_patch: 在读取 tool_calls 调用工具前执行，传入 tool_call, 返回值表示是否继续调用工具
            postfix_patch: 在调用工具后添加消息前执行，传入 tool_call, 返回值表示是否继续调用工具

        Returns: None
        """
        if prefix_hook and not prefix_hook(tool_call):
            return

        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        result = Tool.dispatch(name, args)

        if postfix_hook and not postfix_hook(result):
            return

        self.messages.append(
            CustomMessage(
                role="tool",
                content=str(result),
                tool_call_id=tool_call.id,
                tool_call_name=tool_call.function.name,
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
            max_tokens=5120,
            extra_body={"thinking_budget": 2048},
        )

        collected_content = ""
        collected_tool_calls = {}
        final_message = None

        for chunk in response:
            delta = chunk.choices[0].delta

            if delta.content:
                collected_content += delta.content
                yield {"type": "content", "data": delta.content}

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

        final_message = CustomMessage(
            role="assistant",
            content=collected_content,
            tool_calls=tool_calls if tool_calls else None,
        )

        yield {
            "type": "final",
            "data": final_message,
        }
