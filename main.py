import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import src.view as view
import logging

from src.core.core import NoraAgent
from src.storage.wiki import Wiki

load_dotenv()

# ===== initialize =====

logging.basicConfig(level=logging.DEBUG)

client: OpenAI = OpenAI(
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    base_url="https://api.siliconflow.cn/v1",
)

if "agent" not in st.session_state:
    st.session_state.agent = NoraAgent(client)

if "wiki" not in st.session_state:
    st.session_state.wiki = Wiki.get_instance()

if "pending_tool_call" not in st.session_state:
    st.session_state.pending_tool_call = []

## ======== Page =======

view = view.MainView()

view.display()
