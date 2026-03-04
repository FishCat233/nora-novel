import logging
import os
from typing import Literal, List, Optional


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
    def _parse_search_query(query: str, mode: str) -> List[str]:
        """根据 mode 解析查询字符串为关键词列表。"""
        if mode == "single":
            return [query]
        # mode in ("and", "or")
        # parts = [kw.strip() for kw in query.split("|") if kw.strip()]
        parts = [kw for kw in query.split("|")]
        return parts

    @staticmethod
    def _matches_filename(rel_path: str, kw_data: List[tuple]) -> bool:
        """检查文件名（小写）是否包含任一个关键词的系统路径形式。"""
        rel_lower = rel_path.lower()
        for _, sys_kw in kw_data:
            if sys_kw in rel_lower:
                return True
        return False

    @staticmethod
    def _read_file_content_lower(file_path: str) -> Optional[str]:
        """读取文件内容并返回小写版本，失败时返回 None。"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().lower()
        except Exception:
            # 可以记录日志，但为了简洁，这里静默失败
            return None

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
            query: 搜索关键词或 Wiki Path (如关键词“哈基米”、Wiki路径“角色::哈基米::能力”、多关键词“哈基米|叮咚鸡”）
            in_content: 是否在内容中搜索
            recursive: 是否递归搜索
            mode: 搜索模式，当使用多关键词模式时会使用“|”符号分割 query 为多个关键词。and 表示所有关键词都要匹配，or 表示只要有一个关键词匹配即可，
                single 表示不进行多关键词搜索。默认为 or
        Returns: 匹配的文件 Wiki 路径列表
        """

        root_path = Wiki.data_path
        if not os.path.exists(root_path):
            return []

        # ---------- 1. 解析关键词 ----------
        keywords = Wiki._parse_search_query(query, mode)

        # 注意，如果是空关键词则默认扫描全部
        if not keywords:  # 无有效关键词时直接返回空
            return []

        # 将每个关键词转换为用于文件名匹配的「系统路径形式」（小写，且 :: 替换为 os.sep）
        # 例如 "角色::哈基米" -> "角色/哈基米" (Windows 下是 "角色\\哈基米")
        kw_data = [(kw, Wiki.wiki_path_to_system_path(kw.lower())) for kw in keywords]

        matched_paths = []

        # ---------- 2. 遍历文件 ----------
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if not file.endswith((".md", ".txt")):
                    continue

                full_path = os.path.join(root, file)
                # 相对于 data_path 的路径（用于文件名匹配和生成 Wiki 路径）
                rel_path = os.path.relpath(full_path, root_path)
                wiki_path = rel_path.replace(os.sep, "::")  # 最终返回的格式

                # 提前判断是否可能匹配：如果既不在文件名中搜索，也不在内容中搜索，则跳过
                if not in_content and not Wiki._matches_filename(rel_path, kw_data):
                    continue

                # ---------- 3. 检查文件 ----------
                # 记录每个关键词的匹配状态
                keyword_matches = [False] * len(keywords)

                # 先检查文件名（快速筛选）
                for i, (kw, sys_kw) in enumerate(kw_data):
                    if sys_kw in rel_path.lower():
                        keyword_matches[i] = True
                        # 在 or 模式下，只要有一个匹配就可以提前跳出（但仍需读取内容？）
                        # 但内容可能使其他关键词也匹配？or 模式只需任意一个匹配，所以一旦文件名匹配，可以提前标记为匹配
                        # 但为了后续可能的内容匹配（虽然不影响 or 结果），我们继续检查其他关键词？其实可以 break，因为最终 any() 就够了。
                        # 为了代码简单，我们继续循环，但不会影响最终结果。
                        # 注意：如果 mode == "and"，必须所有关键词都匹配，文件名匹配后仍需检查内容。

                # 如果需要检查内容，且还有未匹配的关键词（and 模式可能需要检查所有；or 模式下如果文件名已有一个匹配，内容检查不是必须的，但我们可以做，结果一样）
                if in_content and not all(
                    keyword_matches
                ):  # 如果所有关键词都已匹配，无需读内容
                    content_lower = Wiki._read_file_content_lower(full_path)
                    if content_lower is not None:
                        for i, (kw, _) in enumerate(kw_data):
                            if not keyword_matches[i] and kw.lower() in content_lower:
                                keyword_matches[i] = True
                                # 如果是 or 模式且已有一个匹配，可以提前结束内容检查？但继续不影响
                                if mode == "or" and any(keyword_matches):
                                    break

                # ---------- 4. 判断是否匹配 ----------
                if mode == "and" and all(keyword_matches):
                    matched_paths.append(wiki_path)
                elif mode == "or" and any(keyword_matches):
                    matched_paths.append(wiki_path)
                elif mode == "single" and any(
                    keyword_matches
                ):  # single 模式等同于 or（但不会拆分关键词）
                    matched_paths.append(wiki_path)

            if not recursive:
                break

        return matched_paths

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
        return paths

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

            return f"成功更新页面: {Wiki.system_path_to_wiki_path(path)}"
        except Exception as e:
            return f"更新失败: {str(e)}"

    def remove_wiki_page(path: str) -> str:
        """
        删除指定路径的条目内容
        Args:
            path: Wiki 条目路径
        Returns: str
        """
        path = path.replace("::", os.sep)
        full_path = os.path.join(Wiki.data_path, path)

        try:
            os.remove(full_path)
            return f"成功删除页面: {path}"
        except Exception as e:
            return f"删除失败: {str(e)}"

    @staticmethod
    def wiki_path_to_system_path(wiki_path: str) -> str:
        return wiki_path.replace("::", os.sep)

    @staticmethod
    def system_path_to_wiki_path(system_path: str) -> str:
        return system_path.replace(os.sep, "::")


if __name__ == "__main__":
    print(Wiki.list_wiki_pages())

    print(Wiki.get_wiki_page_by_title("Wiki::维护手册.md"))

    result = {}

    paths: list[str] = Wiki.search_wiki("哈基米", False, True)
    for path in paths:
        result[path] = Wiki.get_wiki_page_by_path(path)

    print(result)
