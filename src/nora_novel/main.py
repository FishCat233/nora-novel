import os
import sys

import yaml


def main():
    import streamlit as st
    import streamlit_authenticator as stauth

    from openai import OpenAI
    from dotenv import load_dotenv
    import logging

    from nora_novel.view import main_view
    from nora_novel.view.wiki_manager import WikiManagerView
    from nora_novel.view.wiki_manager_simple import SimpleWikiManager
    from nora_novel.view.sidebar import show_load_confirmation
    from nora_novel.view.chat_history import show_regenerate_confirmation
    from nora_novel.core.pipeline_tool import PIPELINE
    from nora_novel.core.agent import NoraAgent
    from nora_novel.storage.wiki import Wiki
    from nora_novel.storage.snapshot import SnapshotStorage

    load_dotenv()

    # ===== initialize =====

    logging.basicConfig(level=logging.DEBUG)

    st.set_page_config(page_title="Nora Novel", page_icon="✒️")

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

    if "snapshot_storage" not in st.session_state:
        st.session_state.snapshot_storage = SnapshotStorage.get_instance()

    if "pending_tool_call" not in st.session_state:
        st.session_state.pending_tool_call = []

    if "page" not in st.session_state:
        st.session_state.page = "chat"

    logging.debug(f"最后一条消息: {st.session_state.agent.messages[-1]}")

    logging.info(
        f"使用 Wiki 路径：{Wiki.data_path}, 下面有 {len(Wiki.list_wiki_pages())} 个条目"
    )

    logging.info(f"当前有 {len(st.session_state.pending_tool_call)} 个待处理的工具调用")

    # 显示确认对话框（如果有）
    show_load_confirmation()
    show_regenerate_confirmation()

    ## ======== Page =======

    with open(os.getenv("AUTH_CONFIG_PATH")) as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    try:
        authenticator.login(
            max_concurrent_users=1,
            max_login_attempts=100,
            single_session=True,
            captcha=True,
        )
    except Exception as e:
        st.error(e)

    if st.session_state.get("authentication_status"):
        authenticator.logout("退出登录", "sidebar")

        if st.session_state.page == "wiki_manager":
            # 显示 Wiki 管理页面
            # wiki_manager = WikiManagerView()
            # wiki_manager.display()
            simple_wiki_manager = SimpleWikiManager()
            simple_wiki_manager.display()

        else:
            main_view(st.session_state.agent)
    elif st.session_state.get("authentication_status") is False:
        st.error("用户名或密码错误")
    elif st.session_state.get("authentication_status") is None:
        st.warning("请输入用户名和密码")


if __name__ == "__main__":
    if not __package__:
        # 如果 __package__ 为空，则说明当前脚本不是作为模块导入的
        package_source_path = os.path.dirname(os.path.dirname(__file__))
        sys.path.append(package_source_path)
    main()
