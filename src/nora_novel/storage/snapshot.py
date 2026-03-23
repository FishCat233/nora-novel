import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from nora_novel.core.types import CommonChatMessage, ToolCallMessage, ChatMessage


@dataclass
class SnapshotInfo:
    """快照元数据"""
    filename: str
    name: str
    timestamp: str
    message_count: int
    current_module_id: str


class SnapshotStorage:
    """会话快照存储管理类"""

    _instance: Optional["SnapshotStorage"] = None

    def __init__(self, snapshot_path: Optional[str] = None):
        if SnapshotStorage._instance is not None:
            raise RuntimeError("Call SnapshotStorage.get_instance() instead")

        if snapshot_path is None:
            # 默认路径：WIKI_PATH 的同级目录 snapshots
            wiki_path = os.path.abspath(os.getenv("WIKI_PATH", "./data/"))
            snapshot_path = os.path.join(os.path.dirname(wiki_path), "snapshots")

        self.snapshot_path = os.path.abspath(snapshot_path)
        self._ensure_directory_exists()

        SnapshotStorage._instance = self

    @staticmethod
    def get_instance(snapshot_path: Optional[str] = None) -> "SnapshotStorage":
        """获取单例实例"""
        if SnapshotStorage._instance is None:
            SnapshotStorage._instance = SnapshotStorage(snapshot_path)
        return SnapshotStorage._instance

    def _ensure_directory_exists(self):
        """确保快照目录存在"""
        if not os.path.exists(self.snapshot_path):
            os.makedirs(self.snapshot_path, exist_ok=True)
            logging.info(f"创建快照目录: {self.snapshot_path}")

    def _serialize_message(self, message: ChatMessage) -> dict:
        """将消息序列化为字典"""
        if isinstance(message, CommonChatMessage):
            return {
                "role": message.role,
                "content": message.content,
                "tool_calls": message.tool_calls,
            }
        elif isinstance(message, ToolCallMessage):
            return {
                "role": message.role,
                "content": message.content,
                "tool_call_id": message.tool_call_id,
                "tool_call_name": message.tool_call_name,
            }
        else:
            # 处理其他类型（如 ChatCompletionMessage）
            return {
                "role": getattr(message, "role", "unknown"),
                "content": getattr(message, "content", ""),
            }

    def _deserialize_message(self, data: dict) -> ChatMessage:
        """将字典反序列化为消息"""
        role = data.get("role")

        if role == "tool":
            return ToolCallMessage(
                role=role,
                content=data.get("content", ""),
                tool_call_id=data.get("tool_call_id"),
                tool_call_name=data.get("tool_call_name"),
            )
        else:
            return CommonChatMessage(
                role=role,
                content=data.get("content", ""),
                tool_calls=data.get("tool_calls"),
            )

    def save_snapshot(
        self,
        name: str,
        messages: list[ChatMessage],
        current_module_id: str,
    ) -> str:
        """
        保存会话快照

        Args:
            name: 用户自定义的快照名称
            messages: 消息历史列表
            current_module_id: 当前模块ID

        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.json"
        filepath = os.path.join(self.snapshot_path, filename)

        # 序列化消息
        serialized_messages = [self._serialize_message(msg) for msg in messages]

        snapshot_data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "current_module_id": current_module_id,
            "messages": serialized_messages,
            "message_count": len(messages),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)

        logging.info(f"保存快照: {filename}")
        return filepath

    def load_snapshot(self, filename: str) -> dict:
        """
        加载会话快照

        Args:
            filename: 快照文件名

        Returns:
            快照数据字典
        """
        filepath = os.path.join(self.snapshot_path, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 反序列化消息
        if "messages" in data:
            data["messages"] = [
                self._deserialize_message(msg) for msg in data["messages"]
            ]

        logging.info(f"加载快照: {filename}")
        return data

    def list_snapshots(self) -> list[SnapshotInfo]:
        """
        列出所有用户保存的快照（排除自动保存文件）

        Returns:
            快照信息列表，按时间倒序排列
        """
        snapshots = []

        if not os.path.exists(self.snapshot_path):
            return snapshots

        for filename in os.listdir(self.snapshot_path):
            # 排除自动保存文件和隐藏文件
            if filename.startswith(".") or not filename.endswith(".json"):
                continue

            filepath = os.path.join(self.snapshot_path, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                snapshots.append(
                    SnapshotInfo(
                        filename=filename,
                        name=data.get("name", "未命名"),
                        timestamp=data.get("timestamp", ""),
                        message_count=data.get("message_count", 0),
                        current_module_id=data.get("current_module_id", ""),
                    )
                )
            except Exception as e:
                logging.warning(f"读取快照文件失败 {filename}: {e}")

        # 按时间倒序排列
        snapshots.sort(key=lambda x: x.timestamp, reverse=True)
        return snapshots

    def delete_snapshot(self, filename: str) -> bool:
        """
        删除快照

        Args:
            filename: 快照文件名

        Returns:
            是否删除成功
        """
        filepath = os.path.join(self.snapshot_path, filename)

        try:
            os.remove(filepath)
            logging.info(f"删除快照: {filename}")
            return True
        except Exception as e:
            logging.error(f"删除快照失败 {filename}: {e}")
            return False

    def auto_save(self, messages: list[ChatMessage]):
        """
        自动保存最近10条对话

        Args:
            messages: 消息历史列表
        """
        # 过滤出用户和助手消息（排除系统消息和工具消息）
        chat_messages = [
            msg
            for msg in messages
            if isinstance(msg, CommonChatMessage)
            and msg.role in ["user", "assistant"]
        ]

        # 只保留最近10条
        recent_messages = chat_messages[-10:]

        # 序列化
        serialized_messages = [self._serialize_message(msg) for msg in recent_messages]

        auto_save_data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "messages": serialized_messages,
            "message_count": len(recent_messages),
        }

        filepath = os.path.join(self.snapshot_path, ".auto_save.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(auto_save_data, f, ensure_ascii=False, indent=2)

    def get_auto_save(self) -> Optional[dict]:
        """
        获取自动保存的对话历史

        Returns:
            自动保存数据，如果不存在则返回 None
        """
        filepath = os.path.join(self.snapshot_path, ".auto_save.json")

        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 反序列化消息
            if "messages" in data:
                data["messages"] = [
                    self._deserialize_message(msg) for msg in data["messages"]
                ]

            return data
        except Exception as e:
            logging.error(f"读取自动保存文件失败: {e}")
            return None

    def clear_auto_save(self):
        """清除自动保存文件"""
        filepath = os.path.join(self.snapshot_path, ".auto_save.json")
        if os.path.exists(filepath):
            os.remove(filepath)
