import logging
import json
from typing import Optional

from openai import OpenAI

from .tools import Tool, tools
from .types import ChatMessage, CustomMessage


class NoraAgent:
    def __init__(self, client: OpenAI, inital_message=None):
        if inital_message is None:
            inital_message = []

        self.client: OpenAI = client
        self.messages: list[ChatMessage] = inital_message

    def chat(self, prompt: str) -> Optional[ChatMessage]:
        """
        进行 ReAct 对话，解决用户的问题。

        会话过程中会记录 message
        Args:
            prompt: 提示词

        Returns: 最终回复
        """
        self.messages.append(CustomMessage(role="user", content=prompt))

        for _ in range(10):
            message = self.single_step()

            # 把 assistant 消息加入历史
            self.messages.append(message)

            # 检查工具调用
            if not message.tool_calls:
                return message

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                result = Tool.dispatch(name, args)
                self.messages.append(
                    CustomMessage(
                        role="tool", content=str(result), tool_call_id=tool_call.id
                    )
                )

        logging.error("超出轮次数量.")

        return None

    def single_step(self):
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
