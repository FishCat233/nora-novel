# 自动存档功能 Checklist

## 实现检查项

### 存储层

- [ ] `snapshot.py` 中 `AutoArchiveInfo` 数据类已定义
- [ ] `snapshot.py` 中 `auto_archive_path` 属性已添加
- [ ] `_ensure_auto_archive_directory()` 方法已实现
- [ ] `save_auto_archive()` 方法已实现
- [ ] `list_auto_archives()` 方法已实现
- [ ] `load_auto_archive()` 方法已实现
- [ ] `_rotate_auto_archives()` 循环覆盖逻辑已实现

### 业务逻辑层

- [ ] `chat_input.py` 中已导入 `SnapshotStorage`
- [ ] `chat_output_stream()` 函数末尾已添加自动存档调用
- [ ] 自动存档只在有实际对话内容时触发
- [ ] `main.py` 中 `SnapshotStorage` 初始化正确

### UI 层

- [ ] `sidebar.py` 中已添加"🕐 自动存档"折叠区域
- [ ] 自动存档区域默认折叠（`expanded=False`）
- [ ] 标题显示当前存档数量
- [ ] `_auto_archive_manager_ui()` 函数已实现
- [ ] 自动存档列表按时间倒序显示
- [ ] 每个存档显示 #序号、时间、消息数
- [ ] 每个存档有"📂 加载"按钮
- [ ] 加载自动存档有确认对话框

### 功能验证

- [ ] 每次对话完成后自动保存存档
- [ ] 自动存档最多保留10条
- [ ] 第11条存档触发循环覆盖（删除最旧的）
- [ ] 侧边栏能正确显示自动存档列表
- [ ] 能成功加载自动存档并恢复会话
- [ ] 加载后有成功提示

## 代码质量检查

- [ ] 代码符合项目现有风格
- [ ] 错误处理完善（try-except）
- [ ] 日志记录完整
- [ ] 类型注解正确
- [ ] 无循环导入问题

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/nora_novel/storage/snapshot.py` | 修改 | 添加自动存档相关方法 |
| `src/nora_novel/view/sidebar.py` | 修改 | 添加自动存档 UI |
| `src/nora_novel/view/chat_input.py` | 修改 | 添加自动存档触发逻辑 |
| `src/nora_novel/main.py` | 修改（可选） | 确保初始化正确 |
