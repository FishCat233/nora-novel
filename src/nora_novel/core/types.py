from typing import Union, Optional, TypedDict, Literal

from openai.types.chat import ChatCompletionMessage
from pydantic import BaseModel


type ChatMessage = Union[ChatCompletionMessage, CommonChatMessage, ToolCallMessage]


class CommonChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = ""
    tool_calls: Optional[list] = None


class ToolCallMessage(BaseModel):
    role: Literal["tool"] = "tool"
    content: str = ""
    tool_call_id: Optional[str] = None
    tool_call_name: Optional[str] = None


class ToolCall(TypedDict):
    id: str
    name: str
    arguments: dict
