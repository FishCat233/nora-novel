from abc import ABC, abstractmethod
from openai import OpenAI
import streamlit as st

from ..core.core import simple_stream_chat


class IView(ABC):
    @abstractmethod
    def display(self):
        pass


class MainView(IView):
    def __init__(self, client: OpenAI):
        self.client = client

    def display(self):
        self.initialize()
        self.load_messages_history()
        self.chat_input()

    def initialize(self):
        # 初始化聊天记录
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # 显示页面标题
        st.title("Nora Novel")

    def load_messages_history(self):
        """加载聊天历史"""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    def chat_input(self):
        """输入框"""
        if prompt := st.chat_input("输入你的消息..."):
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                response = st.write_stream(
                    simple_stream_chat(
                        self.client, list(st.session_state.messages)
                    )  # 防止传输时被修改
                )

            st.session_state.messages.append({"role": "assistant", "content": response})
