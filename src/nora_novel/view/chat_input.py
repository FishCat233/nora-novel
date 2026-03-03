import json
import streamlit as st
from nora_novel.core.agent import NoraAgent
import nora_novel.utils as utils
from nora_novel.core.types import ToolCallMessage
from nora_novel.storage.wiki import Wiki


def chat_part(agent: NoraAgent):
    """输入框"""

    # 如果在等待工具回复
    if len(st.session_state.pending_tool_call) > 0:
        _handle_pending_tool_call(agent)

    # 如果在等待用户会话
    if prompt := st.chat_input("输入你的消息..."):
        result = agent.step(prompt)

        if result == "finished":
            pass

        # agent 调用工具
        if isinstance(result, list):
            for tool_call in result:
                st.session_state.pending_tool_call.append(tool_call)

        st.rerun()


def _handle_pending_tool_call_stream(agent: NoraAgent, tool_calls):
    while tool_calls:
        tool_call = tool_calls.pop(0)
        name = tool_call["function"]["name"]
        args = tool_call["function"]["arguments"]
        tool_call_id = tool_call["id"]

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
                    agent.messages.append(
                        ToolCallMessage(
                            role="tool",
                            content=answer,
                            tool_call_id=tool_call.id,
                            tool_call_name=tool_call.function.name,
                        )
                    )
                    use_ui_tool_call(tool_calls)


def _handle_pending_tool_call(agent: NoraAgent):
    def use_ui_tool_call(calls):
        calls.pop(0)

        # 如果列表空了，让 llm 继续思考
        if not tool_calls:
            res = agent.step()
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
                    agent.messages.append(
                        ToolCallMessage(
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
                if st.button("确认修改", key=f"confirm_{tool_call.id}", type="primary"):
                    # 执行实际的修改逻辑
                    agent._execute_tool_call(tool_call)
                    tool_calls.pop(0)
                    st.rerun()
            with col2:
                if st.button("拒绝修改", key=f"deny_{tool_call.id}"):
                    # 告诉 Agent 用户拒绝了
                    agent.messages.append(
                        ToolCallMessage(
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
                if st.button("确认删除", key=f"confirm_{tool_call.id}", type="primary"):
                    # 执行实际的修改逻辑
                    agent._execute_tool_call(tool_call)
                    use_ui_tool_call(tool_calls)
            with col2:
                if st.button("拒绝删除", key=f"deny_{tool_call.id}"):
                    # 告诉 Agent 用户拒绝了
                    agent.messages.append(
                        ToolCallMessage(
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
            agent._execute_tool_call(tool_call)
            tool_calls.pop(0)

    result = agent.step()
    if isinstance(result, list):
        # 处理 agent 工具调用后还需要继续调用工具的情况
        st.session_state.pending_tool_call.extend(result)
    st.rerun()


def chat_view_stream(agent: NoraAgent):
    # 当前轮到用户交互
    if prompt := st.chat_input("输入你的消息..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            thought_placeholder = st.empty()
            answer_placeholder = st.empty()

            answer_buffer = ""
            tool_calls = []

            # 解析流
            for event in agent.step_stream(prompt):
                if event["type"] == "content":
                    answer_buffer += event["data"]
                    answer_placeholder.markdown(answer_buffer)
                elif event["type"] == "tool_calls":
                    tool_calls.append(event["data"])
                elif event["type"] == "final":
                    pass

            # 结束回答后，解析思考和回答部分
            thought, answer = utils.split_thought_response(answer_buffer)
            if thought:
                thought_placeholder.expander(
                    "🤔 已浅度思考不知道多少秒", expanded=False
                ).markdown(thought)
            if answer:
                answer_placeholder.markdown(answer)
            else:
                answer_placeholder.empty()

            # 解析工具调用
            if tool_calls:
                # 显示工具
                for tc in tool_calls:
                    with st.expander(
                        f"🔧 调用工具: {tc["function"]["name"]}", expanded=False
                    ):
                        st.markdown(f"*参数: {tc["function"]["arguments"]}*")

                # 处理工具
                handle_pending_tool_call_stream(tool_calls)
