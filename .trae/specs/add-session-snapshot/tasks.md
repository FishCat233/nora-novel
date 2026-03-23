# Tasks

- [ ] Task 1: 创建快照存储模块 `storage/snapshot.py`
  - [ ] SubTask 1.1: 实现 `SnapshotStorage` 类，单例模式
  - [ ] SubTask 1.2: 实现 `save_snapshot(name, session_data)` 保存用户手动存档
  - [ ] SubTask 1.3: 实现 `load_snapshot(filename)` 加载指定存档
  - [ ] SubTask 1.4: 实现 `list_snapshots()` 列出所有用户存档（排除.auto_save.json）
  - [ ] SubTask 1.5: 实现 `delete_snapshot(filename)` 删除存档
  - [ ] SubTask 1.6: 实现 `auto_save(messages)` 自动保存最近10条对话
  - [ ] SubTask 1.7: 实现 `get_auto_save()` 获取自动保存的对话历史
  - [ ] SubTask 1.8: 实现消息序列化/反序列化辅助函数

- [ ] Task 2: 修改 `view/sidebar.py` 添加存档管理 UI
  - [ ] SubTask 2.1: 添加"📁 存档管理"区域标题
  - [ ] SubTask 2.2: 实现存档名称输入框和"💾 保存存档"按钮
  - [ ] SubTask 2.3: 实现存档列表显示（名称、时间、消息数）
  - [ ] SubTask 2.4: 实现每个存档的"加载"按钮
  - [ ] SubTask 2.5: 实现每个存档的"删除"按钮
  - [ ] SubTask 2.6: 添加加载存档确认提示（警告会丢失当前对话）

- [ ] Task 3: 修改 `view/chat_history.py` 添加重新生成按钮
  - [ ] SubTask 3.1: 在 `chat_assistant` 函数中添加"🔄 重新生成"按钮
  - [ ] SubTask 3.2: 实现重新生成确认对话框
  - [ ] SubTask 3.3: 实现重新生成逻辑（截断消息历史并重新调用 Agent）

- [ ] Task 4: 修改 `view/chat_input.py` 添加自动保存调用
  - [ ] SubTask 4.1: 在对话完成后调用 `auto_save()` 保存最近10条
  - [ ] SubTask 4.2: 确保只保存用户和助手消息（过滤系统消息和工具消息）

- [ ] Task 5: 修改 `main.py` 初始化快照存储和处理读档
  - [ ] SubTask 5.1: 导入 `SnapshotStorage`
  - [ ] SubTask 5.2: 在 session_state 初始化时创建 snapshot_storage
  - [ ] SubTask 5.3: 添加处理 `st.session_state.load_snapshot` 标记的逻辑
  - [ ] SubTask 5.4: 确保快照存储目录存在

# Task Dependencies
- Task 2 依赖 Task 1（需要存储模块方法）
- Task 3 依赖 Task 1（需要 get_auto_save 方法）
- Task 4 依赖 Task 1（需要 auto_save 方法）
- Task 5 依赖 Task 1（需要 SnapshotStorage 类）
