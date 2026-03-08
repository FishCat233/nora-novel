import streamlit as st
from nora_novel.storage.wiki import Wiki


def sidebar():
    with st.sidebar:
        st.header("Navigation")
        # 添加返回聊天页面的按钮
        if st.button(
            "返回聊天",
            key="back_to_chat",
            use_container_width=True,
        ):
            st.session_state.page = "chat"
            st.rerun()

        st.header("Operation")
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()
        if st.button("📄 新建文件", use_container_width=True):
            st.session_state.new_file_mode = True
            st.rerun()
        if st.button("📁 新建文件夹", use_container_width=True):
            st.session_state.new_folder_mode = True
            st.rerun()

        st.header("Explorer")

        # 文件树
        tree(filter=st.session_state.get("search_term", ""))


def search_input():
    col, cor = st.columns([4, 1])
    with col:
        search_term = st.text_input("🔍 搜索文件", placeholder="输入文件名或路径...")
    with cor:
        if st.button("🔍 搜索", use_container_width=True):
            st.session_state.search_term = search_term
            st.rerun()


def tree(filter: str = ""):
    """显示文件树"""
    st.subheader("文件列表")

    pages = Wiki.list_wiki_pages()

    # 搜索过滤
    if filter:
        pages = [p for p in pages if filter.lower() in p.lower()]

    if not pages:
        st.info("暂无 Wiki 页面")
        return

    # 构建树形结构
    tree = _build_file_tree(pages)

    # 渲染树
    for name, item in tree.items():
        _render_tree_item(name, item)


def _build_file_tree(pages):
    """将文件路径构建为树形结构"""
    tree = {}

    for page in pages:
        parts = page.split("::")
        current_level = tree

        for i, part in enumerate(parts):
            if part not in current_level:
                if i == len(parts) - 1:  # 文件
                    current_level[part] = {"type": "file", "path": page}
                else:  # 文件夹
                    current_level[part] = {"type": "folder", "children": {}}

            if i < len(parts) - 1:
                current_level = current_level[part]["children"]

    return tree


def _render_tree_item(name, item, level=-1, prefix=""):
    """递归渲染树形项目"""
    if item["type"] == "file":
        # 文件显示
        col0, col1 = st.columns([4, 1])
        with col0:
            if st.button(
                f"📄 {name}", key=f"file_{item['path']}", use_container_width=True
            ):
                st.session_state.selected_file = item["path"]
                st.session_state.edit_mode = False
        with col1:
            if st.button("🗑️", key=f"delete_{item['path']}"):
                if st.session_state.get("selected_file") == item["path"]:
                    st.session_state.selected_file = None
                result = Wiki.remove_wiki_page(item["path"])
                st.success(result)
                st.rerun()
    else:
        # 文件夹显示
        with st.expander(f"📁 {name}", expanded=True):
            for child_name, child_item in item["children"].items():
                _render_tree_item(child_name, child_item, level + 0)


class SimpleWikiManager:
    def __init__(self):
        self.wiki = Wiki.get_instance()

    def display(self):
        st.title("Wiki 管理")

        sidebar()

        # 搜索框
        search_input()

        # 主界面布局
        self._display_editor()

    def _display_editor(self):
        """显示编辑器"""
        # 新建文件模式
        if st.session_state.get("new_file_mode"):
            self._display_new_file()
            return

        # 新建文件夹模式
        if st.session_state.get("new_folder_mode"):
            self._display_new_folder()
            return

        # 文件编辑模式
        selected_file = st.session_state.get("selected_file")

        if not selected_file:
            st.info("👈 请在左侧选择文件进行编辑")
            return

        st.subheader(f"编辑: {selected_file}")

        # 读取文件内容
        content = Wiki.get_wiki_page_by_path(selected_file)

        # 编辑模式切换
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(
                "📝 进入编辑模式",
                use_container_width=True,
                disabled=st.session_state.get("edit_mode", False),
            ):
                st.session_state.edit_mode = True
                st.rerun()
        with col2:
            if st.button(
                "👁️ 退出编辑模式",
                use_container_width=True,
                disabled=not st.session_state.get("edit_mode", False),
            ):
                st.session_state.edit_mode = False
                st.rerun()

        # 编辑或查看内容
        if st.session_state.get("edit_mode"):
            new_content = st.text_area(
                "编辑内容", content, height=400, key=f"editor_{selected_file}"
            )

            col_save, col_cancel = st.columns([1, 1])
            with col_save:
                if st.button("💾 保存", use_container_width=True):
                    result = Wiki.update_wiki_page(selected_file, new_content)
                    st.success(result)
                    st.session_state.edit_mode = False
                    st.rerun()
            with col_cancel:
                if st.button("❌ 取消", use_container_width=True):
                    st.session_state.edit_mode = False
                    st.rerun()
        else:
            st.markdown("### 内容预览")
            st.markdown(content)

    def _display_new_file(self):
        """新建文件界面"""
        st.subheader("新建文件")

        file_path = st.text_input("文件路径", placeholder="例如: 角色::哈基米::能力")
        content = st.text_area("文件内容", height=300, placeholder="输入文件内容...")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ 创建", use_container_width=True):
                if not file_path:
                    st.error("请输入文件路径")
                else:
                    if not file_path.endswith(".md"):
                        file_path += ".md"
                    result = Wiki.update_wiki_page(file_path, content)
                    st.success(result)
                    st.session_state.new_file_mode = False
                    st.session_state.selected_file = file_path
                    st.rerun()
        with col2:
            if st.button("❌ 取消", use_container_width=True):
                st.session_state.new_file_mode = False
                st.rerun()

    def _display_new_folder(self):
        """新建文件夹界面"""
        st.subheader("新建文件夹")

        # 在 Wiki 中，文件夹通过创建占位文件实现
        folder_path = st.text_input("文件夹路径", placeholder="例如: 角色::新角色")

        st.info("💡 提示: 在 Wiki 系统中，文件夹通过创建 README.md 文件来标识")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ 创建文件夹", use_container_width=True):
                if not folder_path:
                    st.error("请输入文件夹路径")
                else:
                    # 创建文件夹的 README 文件
                    readme_path = f"{folder_path}::README.md"
                    result = Wiki.update_wiki_page(
                        readme_path,
                        f"# {folder_path.split('::')[-1]}\\n\\n这是一个文件夹。",
                    )
                    st.success(f"文件夹创建成功: {result}")
                    st.session_state.new_folder_mode = False
                    st.rerun()
        with col2:
            if st.button("❌ 取消", use_container_width=True):
                st.session_state.new_folder_mode = False
                st.rerun()
