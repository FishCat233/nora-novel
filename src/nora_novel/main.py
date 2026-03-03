import os
import sys


def main():
    import streamlit as st
    from openai import OpenAI
    from dotenv import load_dotenv
    import logging

    from nora_novel.view import main_view
    from nora_novel.core.pipeline_tool import PIPELINE
    from nora_novel.core.agent import NoraAgent
    from nora_novel.storage.wiki import Wiki

    load_dotenv()

    # ===== initialize =====

    logging.basicConfig(level=logging.DEBUG)

    client: OpenAI = OpenAI(
        api_key=os.getenv("SILICONFLOW_API_KEY"),
        base_url="https://api.siliconflow.cn/v1",
    )

    if "current_module_id" not in st.session_state:
        st.session_state.current_module_id = "common_helper"

    if "agent" not in st.session_state:
        default_modeule = PIPELINE["common_helper"]
        st.session_state.agent = NoraAgent(
            client, system_prompt=default_modeule.system_prompt
        ).setup_pipeline(default_modeule)

    if "wiki" not in st.session_state:
        st.session_state.wiki = Wiki.get_instance()

    if "pending_tool_call" not in st.session_state:
        st.session_state.pending_tool_call = []

    logging.debug(f"最后一条消息: {st.session_state.agent.messages[-1]}")

    logging.info(
        f"使用 Wiki 路径：{Wiki.data_path}, 下面有 {len(Wiki.list_wiki_pages())} 个条目"
    )

    logging.info(f"当前有 {len(st.session_state.pending_tool_call)} 个待处理的工具调用")

    st.set_page_config(page_title="Nora Novel", page_icon="✒️")

    ## ======== Page =======

    main_view(st.session_state.agent)


if __name__ == "__main__":
    if not __package__:
        # 如果 __package__ 为空，则说明当前脚本不是作为模块导入的
        package_source_path = os.path.dirname(os.path.dirname(__file__))
        sys.path.append(package_source_path)
    main()
