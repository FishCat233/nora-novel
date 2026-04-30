# Nora Novel

*人机协作小说创作系统——让 AI 成为你的写作搭档，而不是替代品。*

Nora Novel 是一个基于 **Streamlit** 构建的 Web 应用，旨在通过 AI Agent 辅助人类创作者进行小说创作。它不只是简单的「AI 写作工具」，而是一个强调**人机协作**的创作环境——AI 负责发散思维、整理素材、分析节奏，而人类始终掌握创作的主动权。

## 核心功能

Nora Novel 将创作流程划分为三大模块，每个模块都有专门的 AI 助手：

| 模块                    | 功能                         | 说明                                   |
| ----------------------- | ---------------------------- | -------------------------------------- |
| **灵感探索** (Explorer) | 情节构思、角色设定、异能设计 | 通过对话、抽奖等方式激发创作灵感       |
| **节奏分析** (Adjust)   | 分析小说节奏、结构优化建议   | 帮你发现叙事节奏的潜在问题             |
| **仿写渲染** (Render)   | 根据范文风格润色文字         | 学习你喜欢的作家风格并应用到自己的作品 |

此外，系统内置 **Wiki 知识库** 功能，可以存储和管理你的世界观设定、角色档案、剧情大纲等创作素材。

## 技术架构

Nora Novel 采用分层架构设计：

```
nora-novel/
├── core/           # 核心逻辑层
│   ├── agent.py    # NoraAgent - AI Agent 核心
│   ├── pipeline_tool.py  # 功能模块定义
│   └── tools.py    # 工具注册与实现
├── storage/        # 数据存储层
│   ├── wiki.py     # Wiki 知识库
│   └── snapshot.py # 会话快照
├── view/           # UI 视图层 (Streamlit)
│   ├── chat_history.py
│   ├── chat_input.py
│   ├── sidebar.py
│   └── wiki_manager*.py
└── main.py         # 应用入口
```

### 核心组件

**NoraAgent** 是整个系统的大脑，基于 DeepSeek-V3.2 模型驱动。它通过**工具调用（Tool Calling）**机制与外部系统交互：

- `ask_user` - 向用户提问获取更多信息
- `search_wiki` / `update_wiki` - 读写 Wiki 知识库
- `element_lottery` - 随机生成灵感元素

这种设计让 AI 不再是「黑盒」，而是**可观察、可干预、可回溯**的协作伙伴。

## 快速开始

### 环境要求

- Python >= 3.12
- OpenAI API Key（默认使用 SiliconFlow 平台）

### 安装

```bash
# 克隆仓库
git clone <repository-url>
cd nora-novel

# 使用 uv 安装依赖（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 配置

复制 `.env.example` 为 `.env`，并填写你的配置：

```bash
SILICONFLOW_API_KEY=your_api_key_here
AUTH_CONFIG_PATH=auth_config.yaml
```

创建 `auth_config.yaml` 用于用户认证：

```yaml
credentials:
  usernames:
    your_username:
      email: your@email.com
      name: Your Name
      password: hashed_password  # 使用 streamlit-authenticator 生成

cookie:
  name: nora_novel_session
  key: your_random_key
  expiry_days: 30
```

### 运行

```bash
# 使用 uv
uv run nora-novel

# 或直接运行
streamlit run src/nora_novel/main.py
```

### Docker 部署

```bash
docker-compose up -d
```

## 使用指南

### 1. 灵感探索

当你卡文或需要新点子时，切换到「灵感探索」模块。你可以：

- **灵感抽奖**：随机组合元素（职业 + 场景 + 冲突）激发联想
- **交互对话**：通过 AI 的提问引导你深入思考
- **自由探索**：直接提出你的需求，让 AI 帮你发散

### 2. Wiki 知识库

在创作过程中，随时使用 Wiki 记录和查阅设定：

```
角色::主角名::基本信息.md
世界观::魔法体系::元素法则.md
剧情::第一卷::大纲.md
```

Wiki 支持层级结构，用 `::` 作为分隔符。AI 可以通过工具自动读写 Wiki，帮你整理素材。

### 3. 节奏分析

将章节内容粘贴给 AI，它会分析叙事节奏、情节密度、情绪曲线，并给出改进建议。

### 4. 仿写渲染

提供一段你喜欢的范文，AI 会分析其语言风格、句式特点、修辞手法，然后帮你把草稿润色成相似风格。

## 设计理念

Nora Novel 的设计遵循几个核心原则：

1. **人机协作，而非 AI 代写** - AI 是助手，人类是主导
2. **可观察性** - 所有 AI 操作都可见、可干预
3. **渐进式创作** - 从灵感发散到细节打磨，支持不同创作阶段
4. **知识沉淀** - Wiki 系统让创作素材可积累、可复用

## 技术栈

| 组件     | 技术                            |
| -------- | ------------------------------- |
| 前端框架 | Streamlit                       |
| AI 模型  | DeepSeek-V3.2 (via SiliconFlow) |
| 认证     | streamlit-authenticator         |
| 包管理   | uv / setuptools                 |
| 部署     | Docker                          |

## 贡献

欢迎提交 Issue 和 PR！无论是功能建议、Bug 反馈还是代码贡献，都很感谢。

## 许可证

MIT License

---

*「写作是一场孤独的旅程，但有了好的搭档，路途会不那么漫长。」—— Nora Novel*
