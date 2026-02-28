import json
from abc import ABC, abstractmethod
from openai import OpenAI
import streamlit as st

from src.core.core import NoraAgent
from src.core.types import CustomMessage


class IView(ABC):
    @abstractmethod
    def display(self):
        pass


class MainView(IView):
    def __init__(self):
        self.agent: NoraAgent = st.session_state.agent

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
            elif message.role == "assistant":
                # 如果是 tool_calls 则显示 tool_calls
                with st.chat_message("assistant"):
                    st.markdown(message.content)

                    if message.tool_calls:
                        for tool_call in message.tool_calls:
                            st.markdown(
                                f"*调用工具: {tool_call.function.name}, 参数: {tool_call.function.arguments}*"
                            )
            elif message.role == "tool":
                # 显示工具调用结果
                with st.chat_message("user"):
                    st.markdown(f"*调用结果: {message.content}*")

    def chat_input(self):
        """输入框"""
        # 如果在等待工具回复
        if st.session_state.pending_tool_call:
            self.handle_pending_tool_call()

        # 如果在等待用户会话
        if prompt := st.chat_input("输入你的消息..."):
            result = self.agent.step(prompt)

            if result == "finished":
                pass

            # agent 调用工具
            if isinstance(result, list):
                for tool_call in result:
                    st.session_state.pending_tool_call = tool_call

            st.rerun()

    def handle_pending_tool_call(self):
        tool_call = st.session_state.pending_tool_call

        name = st.session_state.pending_tool_call.function.name
        args = json.loads(st.session_state.pending_tool_call.function.arguments)

        # 如果需要 ui 则先调用 ui
        if name == "ask_user":
            prompt = args["prompt"]
            answer = st.text_input(prompt)
            if answer:
                self.agent.messages.append(
                    CustomMessage(
                        role="tool",
                        content=answer,
                        tool_call_id=tool_call.id,
                        tool_call_name=tool_call.function.name,
                    )
                )
                st.session_state.pending_tool_call = None
                self.agent.step()
                st.rerun()
        else:
            # 调用工具
            self.agent.use_tool_call(tool_call)
            st.session_state.pending_tool_call = None
            self.agent.step()
            st.rerun()

    @staticmethod
    def human_callback(tool_name: str, args):
        if tool_name == "ask_user":
            return st.text_input(args["prompt"])
        else:
            raise NotImplementedError(f"Unknown tool: {tool_name}")
