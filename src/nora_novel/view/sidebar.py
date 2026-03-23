import streamlit as st

from nora_novel.core.pipeline_tool import PIPELINE
from nora_novel.core.types import CommonChatMessage
from nora_novel.storage.snapshot import SnapshotStorage


def main_sidebar():
    with st.sidebar:
        # Wiki 管理入口
        st.header("Wiki")
        if st.button("Wiki 管理", key="wiki_manager", use_container_width=True):
            st.session_state.page = "wiki_manager"
            st.rerun()

        # 存档管理区域
        st.header("📁 存档管理")
        _snapshot_manager_ui()

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
                CommonChatMessage(
                    role="user",
                    content=f"（系统：已切换到【{new_tool.name}】模式。接下来请按该模式的要求继续。）",
                )
            )

            st.session_state.pending_tool_call = []
            st.rerun()


def _snapshot_manager_ui():
    """存档管理 UI"""
    snapshot_storage: SnapshotStorage = st.session_state.snapshot_storage

    # 保存当前会话
    with st.expander("💾 保存当前会话", expanded=False):
        snapshot_name = st.text_input(
            "存档名称", placeholder="输入存档名称...", key="snapshot_name_input"
        )
        if st.button("保存存档", use_container_width=True, key="save_snapshot_btn"):
            # 如果名称为空，使用当前时间作为默认名称
            name = snapshot_name.strip()
            if not name:
                from datetime import datetime

                name = datetime.now().strftime("%Y%m%d_%H%M%S")

            try:
                filepath = snapshot_storage.save_snapshot(
                    name=name,
                    messages=st.session_state.agent.messages,
                    current_module_id=st.session_state.current_module_id,
                )
                st.success(f"✅ 存档已保存: {name}")
            except Exception as e:
                st.error(f"❌ 保存失败: {e}")

    # 显示已保存的存档列表
    st.subheader("已保存的存档")

    try:
        snapshots = snapshot_storage.list_snapshots()

        if not snapshots:
            st.info("暂无存档")
            return

        for snapshot in snapshots:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**📄 {snapshot.name}**")
                    # 格式化时间显示
                    try:
                        dt = snapshot.timestamp.replace("T", " ").split(".")[0]
                    except:
                        dt = snapshot.timestamp
                    st.caption(f"{dt} | {snapshot.message_count} 条消息")

                with col2:
                    # 加载按钮
                    if st.button(
                        "📂 加载",
                        key=f"load_{snapshot.filename}",
                        use_container_width=True,
                    ):
                        _handle_load_snapshot(snapshot.filename)

                    # 删除按钮
                    if st.button(
                        "🗑️ 删除",
                        key=f"delete_{snapshot.filename}",
                        use_container_width=True,
                    ):
                        _handle_delete_snapshot(snapshot.filename)

                st.divider()

    except Exception as e:
        st.error(f"读取存档列表失败: {e}")


def _handle_load_snapshot(filename: str):
    """处理加载存档"""
    # 显示确认对话框
    st.session_state.load_snapshot_confirm = filename
    st.rerun()


def _handle_delete_snapshot(filename: str):
    """处理删除存档"""
    snapshot_storage: SnapshotStorage = st.session_state.snapshot_storage

    if snapshot_storage.delete_snapshot(filename):
        st.success("✅ 存档已删除")
        st.rerun()
    else:
        st.error("❌ 删除失败")


def show_load_confirmation():
    """显示加载存档确认对话框"""
    if "load_snapshot_confirm" not in st.session_state:
        return False

    filename = st.session_state.load_snapshot_confirm

    # 使用对话框显示确认
    @st.dialog("确认加载存档")
    def confirm_dialog():
        st.warning("⚠️ 加载存档将替换当前会话，未保存的对话将丢失！")
        st.info(f"要加载的存档: **{filename}**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 确认加载", use_container_width=True, type="primary"):
                _execute_load_snapshot(filename)
                del st.session_state.load_snapshot_confirm
                st.rerun()

        with col2:
            if st.button("❌ 取消", use_container_width=True):
                del st.session_state.load_snapshot_confirm
                st.rerun()

    confirm_dialog()
    return True


def _execute_load_snapshot(filename: str):
    """执行加载存档操作"""
    snapshot_storage: SnapshotStorage = st.session_state.snapshot_storage

    try:
        data = snapshot_storage.load_snapshot(filename)

        # 恢复会话状态
        st.session_state.current_module_id = data.get(
            "current_module_id", "common_helper"
        )

        # 恢复 Agent 状态
        from nora_novel.core.pipeline_tool import PIPELINE
        from nora_novel.core.agent import NoraAgent
        from openai import OpenAI
        import os

        # 重新创建 Agent
        client = OpenAI(
            api_key=os.getenv("SILICONFLOW_API_KEY"),
            base_url="https://api.siliconflow.cn/v1",
        )

        current_module = PIPELINE.get(
            st.session_state.current_module_id, PIPELINE["common_helper"]
        )

        st.session_state.agent = NoraAgent(
            client, system_prompt=current_module.system_prompt
        ).setup_pipeline(current_module)

        # 恢复消息历史
        messages = data.get("messages", [])
        st.session_state.agent.messages = messages

        # 清除待处理工具调用
        st.session_state.pending_tool_call = []

        st.success(f"✅ 存档已加载: {data.get('name', filename)}")

    except Exception as e:
        st.error(f"❌ 加载存档失败: {e}")
