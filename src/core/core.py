from openai import OpenAI


def simple_chat(c: OpenAI, question: str):
    response = c.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2",
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content
