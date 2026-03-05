import json
import logging

import streamlit as st

from nora_novel.core.agent import NoraAgent
from nora_novel.core.types import CommonChatMessage, ToolCallMessage
from nora_novel.storage.wiki import Wiki
import nora_novel.utils as utils
from nora_novel.view.chat_history import chat_history
from nora_novel.view.chat_input import chat_input_stream
from nora_novel.view.sidebar import chat_sidebar


def main_view(agent: NoraAgent):
    st.title("Nora Novel")

    logging.warning(f"CURRENT MESSAGES: {agent.messages}")

    chat_history(agent)

    chat_sidebar()

    chat_input_stream(agent)
