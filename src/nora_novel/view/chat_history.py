import streamlit as st

from nora_novel.core.agent import NoraAgent
import nora_novel.utils as utils
from nora_novel.core.types import CommonChatMessage


def chat_history(agent: NoraAgent):
    for idx, message in enumerate(agent.messages):
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

            # 传递消息索引用于重新生成
            chat_assistant(thought, response, call_info, message_idx=idx)

        elif message.role == "tool":
            chat_tool(message.content)


def chat_user(content: str):
    with st.chat_message("user"):
        st.markdown(content)


def chat_assistant(
    thought: str, response: str, call_infos: list[(str, str)], message_idx: int = None
):
    """
    显示助手消息，包括思考部分和回答部分。
    Args:
        thought: 思考部分内容
        response: 回答部分内容
        call_infos: 列表，内容是 (工具名 str, 参数 str) 类型元组
        message_idx: 消息在 agent.messages 中的索引，用于重新生成

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

        # 重新生成按钮（放在右上角）
        if message_idx is not None:
            _show_regenerate_button(message_idx)


def _show_regenerate_button(message_idx: int):
    """显示重新生成按钮"""
    # 使用列布局将按钮放在右侧
    cols = st.columns([6, 1])
    with cols[1]:
        if st.button(
            "🔄",
            key=f"regenerate_{message_idx}",
            help="重新生成此回复",
        ):
            st.session_state.regenerate_idx = message_idx
            st.rerun()


def show_regenerate_confirmation():
    """显示重新生成确认对话框"""
    if "regenerate_idx" not in st.session_state:
        return False

    message_idx = st.session_state.regenerate_idx

    @st.dialog("确认重新生成")
    def confirm_dialog():
        st.warning(
            "⚠️ 重新生成将删除此回复及之后的所有消息，并基于之前的上下文重新生成。"
        )
        st.info(f"要重新生成的消息索引: **{message_idx}**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 确认重新生成", use_container_width=True, type="primary"):
                _execute_regenerate(message_idx)
                del st.session_state.regenerate_idx
                st.rerun()

        with col2:
            if st.button("❌ 取消", use_container_width=True):
                del st.session_state.regenerate_idx
                st.rerun()

    confirm_dialog()
    return True


def _execute_regenerate(message_idx: int):
    """执行重新生成操作"""
    try:
        agent = st.session_state.agent

        # 截断消息历史，保留该消息之前的所有消息
        # 注意：需要保留系统消息（索引0）
        new_messages = []
        for i, msg in enumerate(agent.messages):
            if i == 0 or i < message_idx:
                new_messages.append(msg)

        # 更新 agent 的消息历史
        agent.messages = new_messages

        # 清除待处理工具调用
        st.session_state.pending_tool_call = []

        # 设置标记，让 chat_input 知道需要重新生成
        st.session_state.need_regenerate = True

        st.success("✅ 已准备重新生成，正在调用模型...")

    except Exception as e:
        st.error(f"❌ 重新生成准备失败: {e}")


def chat_tool(result_content: str):
    with st.expander("⚙️ 调用结果", expanded=False):
        # 显示工具调用结果
        st.markdown(f"*调用结果: {result_content}*")
