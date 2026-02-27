from src.core.core import simple_stream_chat
from openai import OpenAI
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# ===== initialize =====

client: OpenAI = OpenAI(
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    base_url="https://api.siliconflow.cn/v1",
)

## ======== Page =======

st.title("Nora Novel")

# chat demo

# 初始化聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 输入框
if prompt := st.chat_input("输入你的消息..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.write_stream(
            simple_stream_chat(
                client, list(st.session_state.messages)
            )  # 防止传输时被修改
        )

    st.session_state.messages.append({"role": "assistant", "content": response})
