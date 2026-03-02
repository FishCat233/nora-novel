import json
from abc import ABC, abstractmethod
from openai import OpenAI
import streamlit as st

from src.core.pipeline_tool import PIPELINE
from src.core.core import NoraAgent
from src.core.types import CustomMessage
from src.storage.wiki import Wiki
import src.utils as utils


class IView(ABC):
    @abstractmethod
    def display(self):
        pass


class MainView(IView):
    def __init__(self):
        self.agent: NoraAgent = st.session_state.agent

    def display(self):
        self.initialize()
        self.sidebar()
        self.load_messages()
        self.chat_input()

    def initialize(self):
        # 显示页面标题
        st.title("Nora Novel")

    def sidebar(self):
        with st.sidebar:
            st.header("Pipeline Module")

            categories: dict[str, list] = {}
            for module_id, module in PIPELINE.items():
                categories.setdefault(module.category, []).append((module_id, module))

            selected_module_id = None

            for category, module_list in categories.items():
                st.subheader(category.capitalize())
                for module_id, module in module_list:
                    if st.button(
                        module.name,
                        key=f"module_button_{module_id}",
                        help=module.description,
                        use_container_width=True,
                        type="primary"
                        if module_id == st.session_state.current_module_id
                        else "secondary",
                    ):
                        selected_module_id = module_id

            if (
                selected_module_id
                and selected_module_id != st.session_state.current_module_id
            ):
                # 切换工具
                st.session_state.current_module_id = selected_module_id
                new_tool = PIPELINE[selected_module_id]

                st.session_state.agent.setup_pipeline(new_tool)

                st.session_state.agent.messages.append(
                    CustomMessage(
                        role="user",
                        content=f"（系统：已切换到【{new_tool.name}】模式。接下来请按该模式的要求继续。）",
                    )
                )

                st.session_state.pending_tool_call = []
                st.rerun()

    def load_messages(self):
        """加载聊天历史"""

        for message in self.agent.messages:
            if message.role == "user":
                with st.chat_message("user"):
                    st.markdown(message.content)
            elif message.role == "assistant":
                # 如果是 tool_calls 则显示 tool_calls
                with st.chat_message("assistant"):
                    thought, response = utils.split_thought_response(message.content)

                    if thought:
                        with st.expander("🤔 已浅度思考不知道多少秒", expanded=False):
                            st.markdown(thought)

                    if response:
                        st.markdown(response)

                    if message.tool_calls:
                        for tool_call in message.tool_calls:
                            with st.expander(
                                f"🔧 调用工具: {tool_call.function.name}",
                                expanded=False,
                            ):
                                st.markdown(f"*参数: {tool_call.function.arguments}*")
            elif message.role == "tool":
                with st.expander("⚙️ 调用结果", expanded=False):
                    # 显示工具调用结果
                    st.markdown(f"*调用结果: {message.content}*")

    def chat_input(self):
        """输入框"""
        # 如果在等待工具回复
        if len(st.session_state.pending_tool_call) > 0:
            self.handle_pending_tool_call()

        # 如果在等待用户会话
        if prompt := st.chat_input("输入你的消息..."):
            result = self.agent.step(prompt)

            if result == "finished":
                pass

            # agent 调用工具
            if isinstance(result, list):
                for tool_call in result:
                    st.session_state.pending_tool_call.append(tool_call)

            st.rerun()

    def handle_pending_tool_call(self):
        def use_ui_tool_call(calls):
            calls.pop(0)

            # 如果列表空了，让 llm 继续思考
            if not tool_calls:
                res = self.agent.step()
                if isinstance(res, list):
                    calls.extend(res)

            st.rerun()

        while st.session_state.pending_tool_call:
            tool_calls: list = st.session_state.pending_tool_call

            tool_call = tool_calls[0]

            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # 如果需要 ui 则先调用 ui
            if name == "ask_user":
                prompt = args["prompt"]

                with st.form(f"tool_ask_user_form_{tool_call.id}"):
                    answer = st.text_area(
                        prompt,
                        key=f"tool_{tool_call.id}",
                        height=150,
                        placeholder="请输入你的回复...",
                    )
                    submitted = st.form_submit_button("回复")

                    if submitted:
                        self.agent.messages.append(
                            CustomMessage(
                                role="tool",
                                content=answer,
                                tool_call_id=tool_call.id,
                                tool_call_name=tool_call.function.name,
                            )
                        )
                        use_ui_tool_call(tool_calls)
                return
            elif name == "update_wiki_page":
                # 修改条目前跟用户确认
                st.warning(f"⚠️ Agent 请求修改维基页面: **{args.get('path')}**")
                st.code(args.get("content"), language="markdown")  # 显示修改内容

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(
                        "确认修改", key=f"confirm_{tool_call.id}", type="primary"
                    ):
                        # 执行实际的修改逻辑
                        self.agent.use_tool_call(tool_call)
                        tool_calls.pop(0)
                        st.rerun()
                with col2:
                    if st.button("拒绝修改", key=f"deny_{tool_call.id}"):
                        # 告诉 Agent 用户拒绝了
                        self.agent.messages.append(
                            CustomMessage(
                                role="tool",
                                content="ERROR: 用户拒绝了修改",
                                tool_call_id=tool_call.id,
                                tool_call_name=tool_call.function.name,
                            )
                        )
                        use_ui_tool_call(tool_calls)
                return
            elif name == "remove_wiki_page":
                # 删除前跟用户进行确认
                st.warning(f"⚠️ Agent 请求删除维基页面: **{args.get('path')}**")
                st.code(
                    Wiki.get_wiki_page_by_path(args.get("path")), language="markdown"
                )  # 显示删除内容

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(
                        "确认删除", key=f"confirm_{tool_call.id}", type="primary"
                    ):
                        # 执行实际的修改逻辑
                        self.agent.use_tool_call(tool_call)
                        use_ui_tool_call(tool_calls)
                with col2:
                    if st.button("拒绝删除", key=f"deny_{tool_call.id}"):
                        # 告诉 Agent 用户拒绝了
                        self.agent.messages.append(
                            CustomMessage(
                                role="tool",
                                content="ERROR: 用户拒绝了删除",
                                tool_call_id=tool_call.id,
                                tool_call_name=tool_call.function.name,
                            )
                        )
                        use_ui_tool_call(tool_calls)

                return  # 必须 Return，等待用户点击按钮
            else:
                # 调用工具
                self.agent.use_tool_call(tool_call)
                tool_calls.pop(0)

        result = self.agent.step()
        if isinstance(result, list):
            # 处理 agent 工具调用后还需要继续调用工具的情况
            st.session_state.pending_tool_call.extend(result)
        st.rerun()
