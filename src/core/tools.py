import json
from typing import Type
from pydantic import BaseModel, ConfigDict

from ..storage.wiki import Wiki


class GetCurrentTimeParams(BaseModel):
    time_format: str

    model_config = ConfigDict(extra="forbid")


class AskUserParams(BaseModel):
    prompt: str

    model_config = ConfigDict(extra="forbid")


class SearchWikiParams(BaseModel):
    query: str
    in_content: bool = False
    recursive: bool = True

    model_config = ConfigDict(extra="forbid")


class GetWikiPageByTitle(BaseModel):
    title: str

    model_config = ConfigDict(extra="forbid")


class GetWikiPageByPath(BaseModel):
    path: str
    model_config = ConfigDict(extra="forbid")


class ListWikiPagesParams(BaseModel):
    model_config = ConfigDict(extra="forbid")


tool_registry = {}
tools = []


@staticmethod
def register_tool(schema_model: Type[BaseModel]):
    """
    注册工具到仓库
    Args:
        schema_model: 工具的参数 BaseModel
        tool_type: 工具类型，目前支持 function 和 human_callback

    Returns: wrapper
    """

    def wrapper(func):
        tool_registry[func.__name__] = func

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
            return json.dumps(tool_registry[name](**arguments), ensure_ascii=False)

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
    @register_tool(AskUserParams)
    def ask_user(prompt: str) -> str:
        """
        向用户提问
        Args:
            prompt: 提问内容

        Returns: 用户回答
        """
        pass

    @staticmethod
    @register_tool(SearchWikiParams)
    def search_wiki(
        query: str, in_content: bool = False, recursive: bool = False
    ) -> dict[str, str]:
        """
        搜索用户小说 Wiki 中的条目，以获得更多信息。
        Args:
            query: 搜索关键词或 Wiki 路径
            in_content: 是否在内容中搜索，默认为 False
            recursive: 是否递归搜索，默认为 True
        Returns: 符合条件的条目路径和其全部内容
        """

        result = {}

        paths: list[str] = Wiki.search_wiki(query, in_content, recursive)
        for path in paths:
            result[path] = Wiki.get_wiki_page_by_path(path)

        return result

    @staticmethod
    @register_tool(GetWikiPageByTitle)
    def get_wiki_page_by_title(title: str) -> str:
        """
        获取用户小说 Wiki 中指定标题的条目内容
        Args:
            title: 条目标题

        Returns: 条目内容
        """
        return Wiki.get_wiki_page_by_title(title)

    @staticmethod
    @register_tool(ListWikiPagesParams)
    def list_wiki_pages() -> list[str]:
        """
        列出用户小说 Wiki 中的所有条目路径
        Returns: 条目路径列表
        """
        return Wiki.list_wiki_pages()
