from typing import Union, Optional, TypedDict, Literal

from openai.types.chat import ChatCompletionMessage
from pydantic import BaseModel


type ChatMessage = Union[ChatCompletionMessage, CommonChatMessage, ToolCallMessage]


class CommonChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = ""
    tool_calls: Optional[list["ToolCallJson"]] = None


class ToolCallMessage(BaseModel):
    role: Literal["tool"] = "tool"
    content: str = ""
    tool_call_id: Optional[str] = None
    tool_call_name: Optional[str] = None


class _FunctionCall(TypedDict):
    name: str
    arguments: str


class ToolCallJson(TypedDict):
    id: str
    type: Literal["function"]

    function: _FunctionCall
