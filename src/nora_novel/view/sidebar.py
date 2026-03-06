import streamlit as st

from nora_novel.core.pipeline_tool import PIPELINE
from nora_novel.core.types import CommonChatMessage


def chat_sidebar():
    with st.sidebar:
        # Wiki 管理入口
        if st.button("Wiki 管理", key="wiki_manager", use_container_width=True):
            st.session_state.page = "wiki_manager"
            st.rerun()
        
        st.header("Pipeline Module")

        categories: dict[str, list] = {}
        for module_id, module in PIPELINE.items():
            categories.setdefault(module.category, []).append((module_id, module))

        selected_module_id = None

        for category, module_list in categories.items():
            st.subheader(category.capitalize())
            for module_id, module in module_list:
                if st.button(
                    module.name,
                    key=f"module_button_{module_id}",
                    help=module.description,
                    use_container_width=True,
                    type="primary"
                    if module_id == st.session_state.current_module_id
                    else "secondary",
                ):
                    selected_module_id = module_id

        if (
            selected_module_id
            and selected_module_id != st.session_state.current_module_id
        ):
            # 切换工具
            st.session_state.current_module_id = selected_module_id
            new_tool = PIPELINE[selected_module_id]

            st.session_state.agent.setup_pipeline(new_tool)

            st.session_state.agent.messages.append(
                CommonChatMessage(
                    role="user",
                    content=f"（系统：已切换到【{new_tool.name}】模式。接下来请按该模式的要求继续。）",
                )
            )

            st.session_state.pending_tool_call = []
            st.rerun()