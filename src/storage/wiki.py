import logging
import os
from typing import Literal


class Wiki:
    _instance: "Wiki" = None  # noqa
    data_path = os.path.abspath(os.getenv("WIKI_PATH", "./data/"))  # 从环境变量里面拿

    def __init__(self):
        if not Wiki._instance:
            Wiki._instance = self
            return
        raise RuntimeError("Call Wiki.get_instance() instead")

    @staticmethod
    def get_instance() -> "Wiki":
        if not Wiki._instance:
            Wiki._instance = Wiki()
        return Wiki._instance

    @staticmethod
    def search_wiki(
        query: str,
        in_content: bool = False,
        recursive: bool = True,
        mode: Literal["and", "or", "single"] = "or",
    ) -> list[str]:
        """
        搜索目录下的条目
        Args:
            query: 搜索关键词或 Wiki Path (如“哈基米”、“角色::哈基米::能力”）
            in_content: 是否在内容中搜索
            recursive: 是否递归搜索
            mode: 搜索模式，当使用多关键词模式时会使用“|”符号分割 query 为多个关键词。and 表示所有关键词都要匹配，or 表示只要有一个关键词匹配即可，
                single 表示不进行多关键词搜索。默认为 or
        Returns: 匹配的文件 Wiki 路径列表
        """

        results = []
        path = Wiki.data_path

        if not os.path.exists(path):
            return results

        # 处理关键词
        if mode != "single":
            keywords = [kw.strip() for kw in query.split("|") if kw.strip()]
            if not keywords:  # 分割关键词后为空
                return results
        else:
            keywords = [query]

        processed_keywords = [
            (keywords, Wiki.system_path_to_wiki_path(kw.lower())) for kw in keywords
        ]

        # 遍历搜索
        for root, dirs, files in os.walk(path):
            for file in files:
                if not file.endswith((".md", ".txt")):
                    continue
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, path)

                display_path = relative_path.replace(os.sep, "::")

                keyword_matches = [False] * len(keywords)

                for i, (wiki_kw, rel_path) in enumerate(processed_keywords):
                    # 搜索文件名
                    if rel_path in relative_path:
                        keyword_matches[i] = True
                        if mode == "or":  # or 模式下满足就可以跳出了
                            break
                        continue

                    # 搜索内容
                    if in_content and not keyword_matches[i]:
                        try:
                            with open(full_path, "r", encoding="utf-8") as f:
                                if query.lower() in f.read().lower():
                                    keyword_matches[i] = True
                        except Exception as e:
                            print(f"无法读取文件 {full_path}: {e}")

                if mode == "and" and all(keyword_matches):
                    results.append(display_path)
                elif any(keyword_matches):
                    results.append(display_path)

            if not recursive:
                break

        return results

    @staticmethod
    def get_wiki_page_by_title(title: str) -> str:
        """
        获取用户小说 Wiki 中指定标题的条目内容。

        如果有多条则只会返回第一条。
        Args:
            title: 条目标题

        Returns: 条目内容
        """
        paths: list[str] = Wiki.search_wiki(
            title, in_content=False, recursive=True, mode="single"
        )

        if len(paths) == 0:
            return "ERROR: 未找到条目"

        return Wiki.get_wiki_page_by_path(paths[0])

    @staticmethod
    def get_wiki_page_by_path(path: str) -> str:
        """
        获取指定路径的条目内容
        Args:
            path: 条目 Wiki 路径（带扩展名）
        Returns: 条目内容
        """
        path = Wiki.wiki_path_to_system_path(path)

        try:
            with open(os.path.join(Wiki.data_path, path), "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logging.error(f"无法读取文件 {path}: {e}")
            return "ERROR: 无法读取文件"

    @staticmethod
    def list_wiki_pages() -> list[str]:
        paths = Wiki.search_wiki("", in_content=False, recursive=True, mode="single")
        return [Wiki.wiki_path_to_system_path(path) for path in paths]

    @staticmethod
    def update_wiki_page(path: str, content: str, append: bool = False) -> str:
        """
        更新指定路径的条目内容
        Args:
            path: Wiki 条目路径
            content: 新内容
            append: 是否是追加内容
        Returns: str
        """
        path = path.replace("::", os.sep)
        full_path = os.path.join(Wiki.data_path, path)

        parent_dir = os.path.dirname(full_path)

        try:
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            mode = "a" if append else "w"
            with open(full_path, mode, encoding="utf-8") as f:
                f.write(content)

            return f"成功更新页面: {path}"
        except Exception as e:
            return f"更新失败: {str(e)}"

    @staticmethod
    def wiki_path_to_system_path(wiki_path: str) -> str:
        return wiki_path.replace("::", os.sep)

    @staticmethod
    def system_path_to_wiki_path(system_path: str) -> str:
        return system_path.replace(os.sep, "::")


if __name__ == "__main__":
    print(Wiki.list_wiki_pages())

    print(Wiki.get_wiki_page_by_title("哈基米::编制者.md"))

    result = {}

    paths: list[str] = Wiki.search_wiki("哈基米", False, True)
    for path in paths:
        result[path] = Wiki.get_wiki_page_by_path(path)

    print(result)
