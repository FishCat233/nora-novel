from abc import ABC, abstractmethod
from openai import OpenAI
import streamlit as st


class IView(ABC):
    @abstractmethod
    def display(self):
        pass


class MainView(IView):
    def __init__(self):
        self.agent = st.session_state.agent

    def display(self):
        self.initialize()
        self.load_messages()
        self.chat_input()

    def initialize(self):
        # 显示页面标题
        st.title("Nora Novel")

    def load_messages(self):
        """加载聊天历史"""

        for message in self.agent.messages:
            if message.role == "user":
                with st.chat_message("user"):
                    st.markdown(message.content)
            else:
                with st.chat_message("assistant"):
                    st.markdown(message.content)

    def chat_input(self):
        """输入框"""
        if prompt := st.chat_input("输入你的消息..."):
            self.agent.chat(
                prompt
            )  # TODO: 基于返回值可以做增量更新显示，不过会省略中间的工具调用过程. 后面再弄把.

            # 刷新聊天记录
            self.load_messages()
