import logging
import os


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
        query: str, in_content: bool = False, recursive: bool = True
    ) -> list[str]:
        """
        搜索目录下的条目
        Args:
            query: 搜索关键词或 Wiki Path (如“哈基米”、“角色::哈基米::能力”）
            in_content: 是否在内容中搜索
            recursive: 是否递归搜索
        Returns: 匹配的文件路径列表
        """

        results = []
        path = Wiki.data_path

        if not os.path.exists(path):
            return results

        system_query_path = query.lower().replace("::", os.sep).strip()

        for root, dirs, files in os.walk(path):
            for file in files:
                if not file.endswith((".md", ".txt")):
                    continue
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, path)

                display_path = relative_path.replace(os.sep, "::")

                # 搜索文件名
                if system_query_path.lower() in relative_path.lower():
                    results.append(display_path)
                    continue

                # 搜索内容
                if in_content:
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            if query.lower() in f.read().lower():
                                results.append(display_path)
                    except Exception as e:
                        print(f"无法读取文件 {full_path}: {e}")
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
        paths: list[str] = Wiki.search_wiki(title, in_content=False, recursive=True)

        if len(paths) == 0:
            return "ERROR: 未找到条目"

        paths = [path.replace("::", os.sep) for path in paths]
        return Wiki.get_wiki_page_by_path(paths[0])

    @staticmethod
    def get_wiki_page_by_path(path: str) -> str:
        """
        获取指定路径的条目内容
        Args:
            path: 条目 Wiki 路径（带扩展名）
        Returns: 条目内容
        """
        path = path.replace("::", os.sep)

        try:
            with open(os.path.join(Wiki.data_path, path), "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logging.error(f"无法读取文件 {path}: {e}")
            return "ERROR: 无法读取文件"

    @staticmethod
    def list_wiki_pages() -> list[str]:
        paths = Wiki.search_wiki("", in_content=False, recursive=True)
        return [path.replace(os.sep, "::") for path in paths]

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


if __name__ == "__main__":
    print(Wiki.get_wiki_page_by_title("哈基米::编制者.md"))

    result = {}

    paths: list[str] = Wiki.search_wiki("哈基米", False, True)
    for path in paths:
        result[path] = Wiki.get_wiki_page_by_path(path)

    print(result)
