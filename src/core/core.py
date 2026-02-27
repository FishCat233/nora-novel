from typing import Iterable
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam


def simple_chat(c: OpenAI, question: str):
    response = c.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2",
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content


def simple_stream_chat(c: OpenAI, messages: Iterable[ChatCompletionMessageParam]):
    stream = c.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2",
        messages=messages,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
