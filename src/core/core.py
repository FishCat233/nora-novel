import logging
import json
from typing import Optional

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

    def use_tool_call(self, tool_call) -> None:
        """
        使用工具完成 tool_call，并将结果加入到 messages 中
        Args:
            tool_call: tool_call

        Returns: None
        """
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        result = Tool.dispatch(name, args)

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
        Args:
            prompt: 提示词

        Returns: message
        """
        response = self.client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3.2",
            messages=self.messages,
            tools=self.allow_tools
            if self.allow_tools
            else tools,  # 如果没有限制工具，则默认可以使用所有工具
            max_tokens=4096,
            extra_body={"thinking_budget": 1024},
        )

        return response.choices[0].message
