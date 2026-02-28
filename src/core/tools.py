from typing import Type, Union, Literal
from pydantic import BaseModel, ConfigDict


class GetCurrentTimeParams(BaseModel):
    time_format: str

    model_config = ConfigDict(extra="forbid")


class AskUserParams(BaseModel):
    prompt: str

    model_config = ConfigDict(extra="forbid")


tool_registry = {}
tool_meta = {}
tools = []

type ToolType = Union[
    Literal["function"],  # 函数工具，如检查时间
    Literal["human_callback"],  # 用户回调工具，如询问用户
]


@staticmethod
def register_tool(schema_model: Type[BaseModel], tool_type: ToolType = "function"):
    """
    注册工具到仓库
    Args:
        schema_model: 工具的参数 BaseModel
        tool_type: 工具类型，目前支持 function 和 human_callback

    Returns: wrapper
    """

    def wrapper(func):
        tool_registry[func.__name__] = func
        tool_meta[func.__name__] = {
            "type": tool_type,
        }

        tools.append(
            {
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": func.__doc__,
                    "parameters": schema_model.model_json_schema(),
                },
            }
        )

        return func

    return wrapper


class Tool:
    @staticmethod
    def dispatch(name: str, arguments: dict):
        if name in tool_registry:
            return tool_registry[name](**arguments)

        raise ValueError(f"Unknown tool: {name}")

    @staticmethod
    @register_tool(GetCurrentTimeParams)
    def get_current_time(time_format: str) -> str:
        """
        获取当前时间
        Args:
            time_format: 时间格式，例如 "%Y-%m-%d %H:%M:%S" 对应 "2026-02-28 14:36:02"。
                更多格式请参照 python strftime 函数

        Returns: 当前时间 strftime 格式化后的字符串
        """
        import datetime

        try:
            now = datetime.datetime.now()
            return now.strftime(time_format)
        except ValueError:
            return "Invalid time format"

    @staticmethod
    @register_tool(AskUserParams, tool_type="human_callback")
    def ask_user(prompt: str) -> str:
        """
        向用户提问
        Args:
            prompt: 提问内容

        Returns: 用户回答
        """
        pass
