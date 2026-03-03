import streamlit as st

from nora_novel.core.agent import NoraAgent
import nora_novel.utils as utils
from nora_novel.core.types import CommonChatMessage


def chat_history(agent: NoraAgent):
    for message in agent.messages:
        if message.role == "user":
            chat_user(message.content)

        elif message.role == "assistant":
            thought, response = utils.split_thought_response(message.content)

            call_info: list[tuple[str, str]] = None  # noqa
            if isinstance(message, CommonChatMessage):
                call_info = (
                    [
                        (call["function"]["name"], call["function"]["arguments"])
                        for call in message.tool_calls
                        if call
                    ]
                    if message.tool_calls
                    else []
                )

            chat_assistant(thought, response, call_info)

        elif message.role == "tool":
            chat_tool(message.content)


def chat_user(content: str):
    with st.chat_message("user"):
        st.markdown(content)


def chat_assistant(thought: str, response: str, call_infos: list[(str, str)]):
    """
    显示助手消息，包括思考部分和回答部分。
    Args:
        thought: 思考部分内容
        response: 回答部分内容
        call_infos: 列表，内容是 (工具名 str, 参数 str) 类型元组

    Returns:
    """

    with st.chat_message("assistant"):
        if thought:
            with st.expander("🤔 已浅度思考不知道多少秒", expanded=False):
                st.markdown(thought)

        if response:
            st.markdown(response)

        if call_infos:
            for name, arg in call_infos:
                with st.expander(
                    f"🔧 调用工具: {name}",
                    expanded=False,
                ):
                    st.markdown(f"*参数: {arg}*")


def chat_tool(result_content: str):
    with st.expander("⚙️ 调用结果", expanded=False):
        # 显示工具调用结果
        st.markdown(f"*调用结果: {result_content}*")
