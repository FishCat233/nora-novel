from typing import Union, Optional

from openai.types.chat import ChatCompletionMessage
from pydantic import BaseModel

type ChatMessage = Union[ChatCompletionMessage, CustomMessage]


class CustomMessage(BaseModel):
    role: str
    content: Optional[str] = ""
    tool_call_id: Optional[str] = None
