from src.core.core import simple_stream_chat
from openai import OpenAI
import streamlit as st
import os
from dotenv import load_dotenv
import src.view as view
import logging

load_dotenv()

# ===== initialize =====

logging.basicConfig(level=logging.DEBUG)

client: OpenAI = OpenAI(
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    base_url="https://api.siliconflow.cn/v1",
)

## ======== Page =======

view = view.MainView(client)

view.display()
