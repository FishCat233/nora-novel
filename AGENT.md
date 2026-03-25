# Nora Novel - Agent 开发指南

## 项目概述

Nora Novel 是一个人机协作小说创作系统，基于 Streamlit 构建的 Web 应用。它通过 AI Agent 辅助人类创作者进行小说创作，提供灵感探索、节奏分析、仿写渲染等功能模块。

## 核心架构

### 1. 项目结构

```
nora-novel/
├── src/nora_novel/
│   ├── core/           # 核心逻辑层
│   │   ├── agent.py    # NoraAgent - AI Agent 核心实现
│   │   ├── pipeline_tool.py  # PipelineTool - 功能模块定义
│   │   ├── tools.py    # 工具注册与实现
│   │   └── types.py    # 类型定义
│   ├── storage/        # 数据存储层
│   │   └── wiki.py     # Wiki 存储管理
│   ├── view/           # UI 视图层
│   │   ├── chat_history.py   # 聊天历史显示
│   │   ├── chat_input.py     # 聊天输入处理
│   │   ├── sidebar.py        # 侧边栏模块切换
│   │   └── wiki_manager_simple.py  # Wiki 管理界面
│   ├── utils/          # 工具函数
│   └── main.py         # 应用入口
├── AGENT.md            # 本文件
├── README.md           # 项目说明
├── pyproject.toml      # Python 项目配置
├── Dockerfile          # Docker 构建配置
└── docker-compose.yml  # Docker Compose 配置
```

### 2. 核心组件

#### 2.1 NoraAgent (core/agent.py)

AI Agent 的核心实现，负责与 LLM (DeepSeek-V3.2) 交互。

**主要功能：**
- `step(prompt)`: 单步运行 Agent，返回工具调用列表或 "finished"
- `step_stream(prompt)`: 流式运行 Agent，支持实时显示生成内容
- `execute_tool_call(tool_call)`: 执行工具调用并处理结果
- `setup_pipeline(pipeline)`: 设置当前功能模块

**关键属性：**
- `messages`: 对话历史记录
- `system_prompt`: 系统提示词
- `allow_tools`: 允许使用的工具列表
- `pending_tool`: 待处理的工具调用

#### 2.2 PipelineTool (core/pipeline_tool.py)

定义不同的功能模块，每个模块有特定的系统提示词和可用工具。

**现有模块：**

| 模块ID                    | 名称     | 类别     | 描述                           |
| ------------------------- | -------- | -------- | ------------------------------ |
| common_helper             | 通用助手 | common   | 提供各种通用帮助               |
| explorer_inspiration      | 灵感探索 | explorer | 探索新颖的情节、角色或异能设定 |
| explore_interact_dialogue | 交互对话 | explorer | 通过询问驱动对话，激发联想     |
| explore_inspire_lottery   | 灵感抽奖 | explorer | 随机生成灵感元素组合           |
| adjust_rhythm_analysis    | 节奏分析 | adjust   | 分析小说节奏并给出建议         |
| render_imitate            | 仿写渲染 | render   | 根据范文风格渲染草稿           |

#### 2.3 Tool 系统 (core/tools.py)

工具注册与实现机制，使用装饰器模式注册工具。

**可用工具：**

| 工具名                 | 功能                 | 需要UI确认 |
| ---------------------- | -------------------- | ---------- |
| get_current_time       | 获取当前时间         | 否         |
| ask_user               | 向用户提问           | 是         |
| search_wiki            | 搜索 Wiki 条目       | 否         |
| get_wiki_page_by_title | 按标题获取 Wiki 页面 | 否         |
| list_wiki_pages        | 列出所有 Wiki 页面   | 否         |
| update_wiki_page       | 更新/创建 Wiki 页面  | 是         |
| remove_wiki_page       | 删除 Wiki 页面       | 是         |
| element_lottery        | 元素抽奖             | 否         |

#### 2.4 Wiki 存储 (storage/wiki.py)

基于文件系统的 Wiki 存储，使用 `::` 作为路径分隔符。

**关键方法：**
- `search_wiki(query, in_content, recursive, mode)`: 搜索条目
- `get_wiki_page_by_path(path)`: 按路径获取内容
- `get_wiki_page_by_title(title)`: 按标题获取内容
- `update_wiki_page(path, content, append)`: 更新/创建条目
- `remove_wiki_page(path)`: 删除条目

**路径格式：**
- Wiki 路径: `角色::哈基米::能力.md`
- 系统路径: `角色/哈基米/能力.md`

## 开发规范

### 1. 添加新工具

在 `core/tools.py` 中添加：

```python
class MyToolParams(BaseModel):
    param1: str
    param2: int = 0  # 默认值
    model_config = ConfigDict(extra="forbid")

class Tool:
    @staticmethod
    @register_tool(MyToolParams)
    def my_tool(param1: str, param2: int) -> str:
        """
        工具描述，将被用于 LLM 的工具定义
        Args:
            param1: 参数1说明
            param2: 参数2说明
        Returns: 返回结果说明
        """
        # 实现逻辑
        return result
```

**注意事项：**
- 参数模型必须继承 `BaseModel` 并设置 `extra="forbid"`
- 工具函数必须是 `@staticmethod`
- 如果工具需要用户确认，在 `chat_input.py` 中添加对应的 UI 处理

### 2. 添加新 Pipeline 模块

在 `core/pipeline_tool.py` 中添加：

```python
MY_NEW_MODULE = PipelineTool(
    id="my_new_module",
    name="新模块名称",
    category="category_name",
    description="模块功能描述",
    system_prompt="""
    模块特定的系统提示词...
    """,
    allowed_tools=["tool1", "tool2"],  # 可选，限制可用工具
)

# 添加到 PIPELINE 字典
PIPELINE = {
    # ... 现有模块
    "my_new_module": MY_NEW_MODULE,
}
```

### 3. 修改 UI 交互

#### 3.1 聊天输入处理 (view/chat_input.py)

如果需要为新工具添加 UI 确认：

```python
def _handle_pending_tool_call(agent: NoraAgent):
    # ... 现有代码
    
    elif name == "my_new_tool":
        # 显示确认界面
        st.warning(f"⚠️ Agent 请求执行: **{args.get('param')}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("确认", key=f"confirm_{tool_call.id}", type="primary"):
                agent.execute_tool_call(tool_call)
                use_ui_tool_call(tool_calls)
        with col2:
            if st.button("拒绝", key=f"deny_{tool_call.id}"):
                agent.messages.append(
                    ToolCallMessage(
                        role="tool",
                        content="ERROR: 用户拒绝了操作",
                        tool_call_id=tool_call.id,
                        tool_call_name=tool_call.function.name,
                    )
                )
                use_ui_tool_call(tool_calls)
        return
```

#### 3.2 聊天历史显示 (view/chat_history.py)

如需自定义消息显示格式，修改 `chat_assistant` 或添加新的显示函数。

### 4. 环境变量配置

复制 `.env.example` 为 `.env` 并配置：

```bash
# API Keys
SILICONFLOW_API_KEY=your_api_key

# Wiki Path
WIKI_PATH=/path/to/wiki/data

# Auth Config (可选)
AUTH_CONFIG_PATH=/path/to/auth_config.yaml
```

## 核心设计原则

### 1. 人类主导，AI 辅助
- 所有创意决策由人类做出
- AI 提供选项、分析和执行扩展

### 2. Wiki 是唯一事实来源
- 生成内容前必须先查询 Wiki
- 修改 Wiki 需要用户确认
- 使用 `ask_user` 工具主动询问

### 3. 思考与回答分离
- 使用 `<思考>` 和 `</思考>` 标签包裹思考过程
- 每个 message 最多一对思考标签
- 标签必须单独占一行

### 4. 工具调用透明
- 调用工具前解释原因
- 修改类工具需要用户确认
- 支持批量工具调用

## 调试与开发

### 本地运行

```bash
# 使用 uv
uv run streamlit run src/nora_novel/main.py

# 或使用 Python
python -m streamlit run src/nora_novel/main.py
```

### Docker 运行

```bash
docker-compose up -d
```

### 日志级别

在 `main.py` 中设置：

```python
logging.basicConfig(level=logging.DEBUG)  # DEBUG/INFO/WARNING/ERROR
```

## 常见问题

### Q: 如何添加需要用户交互的新工具？
A: 1. 在 `tools.py` 中注册工具 2. 在 `chat_input.py` 的 `_handle_pending_tool_call` 中添加 UI 处理逻辑

### Q: 如何修改系统提示词？
A: 编辑 `pipeline_tool.py` 中对应模块的 `system_prompt`，或修改 `COMMON_SYSTEM` 影响所有模块

### Q: Wiki 文件存储在哪里？
A: 由 `WIKI_PATH` 环境变量指定，默认为 `./data/`

### Q: 如何切换 LLM 模型？
A: 修改 `agent.py` 中的 `model` 参数（当前使用 `deepseek-ai/DeepSeek-V3.2`）

## 扩展阅读

- [Streamlit 文档](https://docs.streamlit.io/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Pydantic 文档](https://docs.pydantic.dev/)
