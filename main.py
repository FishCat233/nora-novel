import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import src.view as view
import logging

from src.core.pipeline_tool import PIPELINE
from src.core.core import NoraAgent
from src.storage.wiki import Wiki

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

logging.info(
    f"使用 Wiki 路径：{Wiki.data_path}, 下面有 {len(Wiki.list_wiki_pages())} 个条目"
)

st.set_page_config(page_title="Nora Novel", page_icon="✒️")

## ======== Page =======

view = view.MainView()

view.display()
