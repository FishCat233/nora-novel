import json
import logging
from typing import Any, Generator

import streamlit as st
from nora_novel.core.agent import (
    NoraAgent,
    StreamFinalEvent,
    StreamContentEvent,
    ToolCallJson,
)
import nora_novel.utils as utils
from nora_novel.core.types import ToolCallMessage
from nora_novel.storage.wiki import Wiki
from nora_novel.storage.snapshot import SnapshotStorage


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


def _handle_tool_call(agent: NoraAgent, tool_call: ToolCallJson):
    def call_agent_check():
        if agent.pending_tool:
            # 还有工具要处理，则先显示其他的工具 ui 进行处理
            st.rerun()

        # 工具处理完了，叫 llm 重新烧烤
        logging.debug("工具调用完成，重新烧烤中")
        stream = agent.step_stream()
        chat_output_stream(agent, stream)
        st.rerun()

    logging.info(f"Agent 调用工具: {tool_call}")

    call_id = tool_call["id"]
    call_name = tool_call["function"]["name"]
    call_args = json.loads(tool_call["function"]["arguments"])

    if call_name == "ask_user":
        prompt = call_args["prompt"]

        need_check = False
        with st.form(f"tool_ask_user_form_{tool_call}"):
            answer = st.text_area(
                prompt,
                key=f"tool_{call_id}",
                height=150,
                placeholder="请输入你的回复...",
            )
            submitted = st.form_submit_button("回复")

            if submitted:
                agent.execute_tool_call(tool_call, answer)
                need_check = True
        if need_check:
            call_agent_check()
        return

    elif call_name == "update_wiki_page":
        # 修改条目前跟用户确认
        st.warning(f"⚠️ Agent 请求修改维基页面: **{call_args.get('path')}**")
        st.code(call_args.get("content"), language="markdown")  # 显示修改内容

        col1, col2 = st.columns(2)
        need_check = False
        with col1:
            if st.button("确认修改", key=f"confirm_{call_id}", type="primary"):
                # 执行实际的修改逻辑
                agent.execute_tool_call(tool_call)
                need_check = True
        with col2:
            if st.button("拒绝修改", key=f"deny_{call_id}"):
                # 告诉 Agent 用户拒绝了
                agent.execute_tool_call(tool_call, "ERROR: 用户拒绝了修改")
                call_agent_check()
                need_check = True
        if need_check:
            call_agent_check()
        return

    elif call_name == "remove_wiki_page":
        # 删除前跟用户进行确认
        st.warning(f"⚠️ Agent 请求删除维基页面: **{call_args.get('path')}**")
        st.code(
            Wiki.get_wiki_page_by_path(call_args.get("path")), language="markdown"
        )  # 显示删除内容

        col1, col2 = st.columns(2)
        need_check = False
        with col1:
            if st.button("确认删除", key=f"confirm_{call_id}", type="primary"):
                # 执行实际的修改逻辑
                agent.execute_tool_call(tool_call)
                need_check = True
        with col2:
            if st.button("拒绝删除", key=f"deny_{call_id}"):
                # 告诉 Agent 用户拒绝了
                agent.execute_tool_call(tool_call, "ERROR: 用户拒绝了删除")
                need_check = True
        if need_check:
            call_agent_check()
        return

    else:
        # 调用了不需要 ui 的工具
        agent.execute_tool_call(tool_call)

    call_agent_check()


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
                    agent.execute_tool_call(tool_call)
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
                    agent.execute_tool_call(tool_call)
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
            agent.execute_tool_call(tool_call)
            tool_calls.pop(0)

    result = agent.step()
    if isinstance(result, list):
        # 处理 agent 工具调用后还需要继续调用工具的情况
        st.session_state.pending_tool_call.extend(result)
    st.rerun()


def chat_input_stream(agent: NoraAgent):
    # 处理重新生成请求
    if st.session_state.get("need_regenerate"):
        st.session_state.need_regenerate = False
        # 直接调用 Agent 生成新回复
        stream = agent.step_stream()
        chat_output_stream(agent, stream)

        # 处理工具
        if agent.pending_tool:
            _handle_tool_call(agent, agent.pending_tool[0])
        return

    # 当前有工具在处理，则先处理工具
    if agent.pending_tool:
        _handle_tool_call(agent, agent.pending_tool[0])

    # 用户文本框
    if prompt := st.chat_input("输入你的消息..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        stream = agent.step_stream(prompt)

        chat_output_stream(agent, stream)

        # 处理工具
        if agent.pending_tool:
            _handle_tool_call(agent, agent.pending_tool[0])


def chat_output_stream(
    agent: NoraAgent,
    stream: Generator[StreamContentEvent | StreamFinalEvent, Any, None],
):
    """流式输出处理函数"""
    with st.chat_message("assistant"):
        # 创建占位符
        thought_placeholder = st.empty()
        answer_placeholder = st.empty()
        tool_placeholder = st.empty()

        # 用于收集内容的缓冲区
        content_buffer = ""
        tool_calls_buffer = []

        # 实时流式显示
        for event in stream:
            if isinstance(event, StreamContentEvent):
                # 累积内容
                content_buffer += event.data

                # 实时解析并显示（分离思考部分和回答部分）
                thought, answer = utils.split_thought_response(content_buffer)

                # 显示思考部分（如果有）
                if thought:
                    thought_placeholder.expander(
                        "🤔 已浅度思考不知道多少秒", expanded=False
                    ).markdown(thought)

                # 实时显示回答部分
                if answer:
                    answer_placeholder.markdown(answer)

            elif isinstance(event, StreamFinalEvent):
                # 收集工具调用
                if event.data.tool_calls:
                    tool_calls_buffer = event.data.tool_calls

        # 流结束后，最终显示工具调用
        if tool_calls_buffer:
            with tool_placeholder.container():
                for tc in tool_calls_buffer:
                    with st.expander(
                        f"🔧 调用工具: {tc["function"]["name"]}", expanded=False
                    ):
                        st.markdown(f"*参数: {tc["function"]["arguments"]}*")

    # 流式输出结束后，触发自动存档
    _trigger_auto_archive(agent)

    # 刷新 UI 确保最终状态正确显示
    st.rerun()


def _trigger_auto_archive(agent: NoraAgent):
    """
    触发自动存档
    在每次对话完成后自动保存会话状态
    """
    try:
        snapshot_storage = SnapshotStorage.get_instance()
        current_module_id = st.session_state.get("current_module_id", "common_helper")

        # 保存自动存档
        snapshot_storage.save_auto_archive(
            messages=agent.messages,
            current_module_id=current_module_id,
        )
        logging.debug("自动存档已保存")
    except Exception as e:
        logging.error(f"自动存档失败: {e}")
