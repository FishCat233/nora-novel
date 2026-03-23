# 自动存档功能 Tasks

## Phase 1: 存储层实现

### Task 1.1: 扩展 SnapshotStorage 类
**文件**: `src/nora_novel/storage/snapshot.py`

- [ ] 添加自动存档目录配置 `auto_archive_path`
- [ ] 实现 `_ensure_auto_archive_directory()` 方法
- [ ] 实现 `save_auto_archive()` 方法：
  - 保存到 `{SNAPSHOT_PATH}/auto_archives/` 目录
  - 文件命名格式 `auto_archive_{index}.json`，index 为 0-9
  - 包含字段：version, timestamp, index, current_module_id, messages, message_count
- [ ] 实现 `list_auto_archives()` 方法：
  - 读取所有自动存档文件
  - 返回按 index 排序的列表
- [ ] 实现 `load_auto_archive()` 方法：
  - 根据 index 加载指定自动存档
- [ ] 实现 `_rotate_auto_archives()` 方法：
  - 当保存第11条时，删除 index 0
  - 将 index 0-8 依次重命名为 1-9
  - 新存档保存为 index 9

### Task 1.2: 添加 AutoArchiveInfo 数据类
**文件**: `src/nora_novel/storage/snapshot.py`

- [ ] 添加 `AutoArchiveInfo` dataclass：
  - index: int
  - timestamp: str
  - message_count: int
  - current_module_id: str

## Phase 2: 业务逻辑层实现

### Task 2.1: 在 chat_input.py 中集成自动存档
**文件**: `src/nora_novel/view/chat_input.py`

- [ ] 导入 `SnapshotStorage`
- [ ] 在 `chat_output_stream()` 函数末尾添加自动存档调用：
  - 流式输出结束后保存自动存档
  - 只在有实际对话内容时触发
- [ ] 确保工具调用处理完成后才触发自动存档

### Task 2.2: 在 main.py 中初始化自动存档
**文件**: `src/nora_novel/main.py`

- [ ] 确保 `SnapshotStorage` 已初始化
- [ ] 验证自动存档目录已创建

## Phase 3: UI 层实现

### Task 3.1: 在 sidebar.py 中添加自动存档 UI
**文件**: `src/nora_novel/view/sidebar.py`

- [ ] 在"已保存的存档"下方添加"🕐 自动存档"折叠区域：
  - 使用 `st.expander()`，默认折叠（`expanded=False`）
  - 标题显示当前存档数量，如"🕐 自动存档 (10)"
- [ ] 实现 `_auto_archive_manager_ui()` 函数：
  - 调用 `list_auto_archives()` 获取列表
  - 按时间倒序显示（最新的 index 9 显示在最上面）
  - 每个存档显示：#序号、时间、消息数
  - 添加"📂 加载"按钮
- [ ] 实现 `_handle_load_auto_archive()` 函数：
  - 调用 `load_auto_archive()` 加载数据
  - 复用现有的 `_execute_load_snapshot()` 逻辑恢复会话

### Task 3.2: 添加加载确认对话框
**文件**: `src/nora_novel/view/sidebar.py`

- [ ] 复用现有的 `show_load_confirmation()` 逻辑
- [ ] 确保加载自动存档时也有确认对话框

## Phase 4: 测试与验证

### Task 4.1: 功能测试
- [ ] 测试自动存档是否在每次对话后正确保存
- [ ] 测试自动存档数量限制（最多10条）
- [ ] 测试循环覆盖机制（第11条删除最旧的）
- [ ] 测试侧边栏自动存档列表显示
- [ ] 测试加载自动存档功能

### Task 4.2: 边界测试
- [ ] 测试空对话时的自动存档行为
- [ ] 测试快速连续对话时的存档行为
- [ ] 测试加载自动存档后再次对话的存档行为
