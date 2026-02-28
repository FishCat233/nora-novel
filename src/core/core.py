import logging
import json
from typing import Optional, Callable

from openai import OpenAI

from .tools import Tool, tools, tool_meta
from .types import ChatMessage, CustomMessage


class NoraAgent:
    def __init__(self, client: OpenAI, inital_message=None):
        if inital_message is None:
            inital_message = []

        self.client: OpenAI = client
        self.messages: list[ChatMessage] = inital_message

    def chat(
        self, prompt: str, human_callback: Optional[Callable] = None
    ) -> Optional[ChatMessage]:
        """
        进行 ReAct 对话，解决用户的问题。

        会话过程中会记录 message
        Args:
            prompt: 提示词
            human_callback: 回调函数，在需要用户参与 loop 时调用。

        Returns: 最终回复
        """
        self.messages.append(CustomMessage(role="user", content=prompt))

        for _ in range(10):
            message = self._single_step()

            # 把 assistant 消息加入历史
            self.messages.append(message)

            # 检查工具调用
            if not message.tool_calls:
                return message

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                if tool_meta[name]["type"] == "human_callback":
                    # 如果是 human_callback 类型的工具
                    if not human_callback:
                        logging.error("没有提供人类回调函数.")
                        return None

                    result = human_callback(name, args)
                else:
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
            tools=tools,
            max_tokens=1024,
        )

        return response.choices[0].message


def simple_chat(c: OpenAI, question: str) -> list:
    response = c.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2",
        messages=[{"role": "user", "content": question}],
        tools=tools,
        max_tokens=1024,
    )

    for tool_call in response.choices[0].message.tool_calls or []:
        if tool_call.function.name == "get_current_time":
            args = json.load(tool_call.function.arguments)
            result = Tool.get_current_time(args["time_format"])

    return response.choices[0].message.content


def simple_stream_chat(c: OpenAI, messages):
    stream = c.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2",
        messages=messages,
        tools=tools,
        max_tokens=1024,
        stream=True,
    )

    for chunk in stream:
        if not chunk.choices:
            continue
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
        # if chunk.choices[0].delta.reasoning_content:
        #     yield chunk.choices[0].delta.reasoning_content
