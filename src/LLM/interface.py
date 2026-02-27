from abc import ABC
from typing import Optional
from openai import OpenAI


class ILLM(ABC):
    _client: Optional[OpenAI] = None

    _api_key: str = ""
    _base_url: str = ""

    @property
    def client(self) -> Optional[OpenAI]:
        return self._client

    @staticmethod
    def Setup(api_key: str = "", base_url: str = ""):
        if api_key != "":
            _api_key = api_key
        if base_url != "":
            _base_url = base_url
        _client = OpenAI(
            api_key=ILLM._api_key,
            base_url=ILLM._base_url,
        )


class ChatableILLM(ILLM):
    def Chat(
        self,
        model: str,
        prompt: str,
        args: dict = {},
    ) -> str:
        if self._client is None:
            raise ValueError("client is not setup")
        response = self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **args,
        )
        return response.choices[0].message.content
