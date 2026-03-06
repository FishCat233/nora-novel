import streamlit as st
from nora_novel.storage.wiki import Wiki


class WikiManagerView:
    def __init__(self):
        self.wiki = Wiki.get_instance()

    def display(self):
        st.title("Wiki 管理")

        # 功能选择
        tab1, tab2, tab3, tab4 = st.tabs(
            ["页面列表", "查看页面", "创建页面", "编辑页面"]
        )

        with tab1:
            self._display_page_list()

        with tab2:
            self._display_view_page()

        with tab3:
            self._display_create_page()

        with tab4:
            self._display_edit_page()

    def _display_page_list(self):
        st.header("Wiki 页面列表")

        pages = Wiki.list_wiki_pages()

        if not pages:
            st.info("暂无 Wiki 页面")
            return

        for page in pages:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"- {page}")
            with col2:
                if st.button("删除", key=f"delete_{page}"):
                    result = Wiki.remove_wiki_page(page)
                    st.success(result)
                    st.rerun()

    def _display_view_page(self):
        st.header("查看 Wiki 页面")

        pages = Wiki.list_wiki_pages()

        if not pages:
            st.info("暂无 Wiki 页面")
            return

        selected_page = st.selectbox("选择页面", pages)

        if selected_page:
            content = Wiki.get_wiki_page_by_path(selected_page)
            st.markdown("### 页面内容")
            st.markdown(content)

    def _display_create_page(self):
        st.header("创建 Wiki 页面")

        page_path = st.text_input("页面路径 (例如: 角色::哈基米)")
        content = st.text_area("页面内容", height=300)

        if st.button("创建页面"):
            if not page_path:
                st.error("请输入页面路径")
            elif not content:
                st.error("请输入页面内容")
            else:
                # 确保路径以 .md 结尾
                if not page_path.endswith(".md"):
                    page_path += ".md"

                result = Wiki.update_wiki_page(page_path, content)
                st.success(result)
                st.rerun()

    def _display_edit_page(self):
        st.header("编辑 Wiki 页面")

        pages = Wiki.list_wiki_pages()

        if not pages:
            st.info("暂无 Wiki 页面")
            return

        selected_page = st.selectbox("选择页面", pages, key="edit_page")

        if selected_page:
            current_content = Wiki.get_wiki_page_by_path(selected_page)
            new_content = st.text_area("页面内容", current_content, height=300)

            if st.button("保存修改"):
                result = Wiki.update_wiki_page(selected_page, new_content)
                st.success(result)
                st.rerun()
