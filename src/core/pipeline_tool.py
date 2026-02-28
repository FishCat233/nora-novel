from .tools import tools


class PipelineTool:
    def __init__(
        self,
        id: str,
        name: str,
        category: str,
        description: str,
        system_prompt: str,
        allowed_tools: list[str] = None,
    ):
        self.id = id
        self.name = name
        self.category = category
        self.description = description
        self.system_prompt = system_prompt

        if allowed_tools is None:
            self.allowed_tools = tools
        else:
            self.allowed_tools = allowed_tools


COMMON_HELPER = PipelineTool(
    id="common_helper",
    name="通用助手",
    category="common",
    description="提供各种通用帮助，如时间查询、信息查询等。",
    system_prompt="你是一个写作助手，能够根据用户的要求在其小说数据库的支持下进行各种写作任务以辅助用户书写更好的小说。"
    "之前的对话可能包含其他阶段的讨论，但请忽略它们，专注于当前任务。 如果需要引用之前的信息，请根据消息内容自行判断相关性。",
)

EXPLORE_INSPIRATION = PipelineTool(
    id="explor_inspiration",
    name="灵感探索",
    category="explorer",
    description="根据你的约束和已有设定，探索新颖的情节、角色或异能设定。",
    system_prompt="你是一位创意伙伴，擅长在给定的约束下进行头脑风暴。"
    "你需要结合用户提供的要求和已有的 Wiki 设定，生成多个合理且有趣的情节选项。"
    "请优先调用 search_wiki 获取已有设定，避免重复。"
    "之前的对话可能包含其他阶段的讨论，但请忽略它们，专注于当前任务。 如果需要引用之前的信息，请根据消息内容自行判断相关性。"
    "如果信息不足，可以用 ask_user 向用户提问。",
    allowed_tools=[
        "search_wiki",
        "get_wiki_page_by_title",
        "list_wiki_pages",
        "ask_user",
        "get_current_time",
    ],
)

ADJUST_RHYTHM_ANALYSIS = PipelineTool(
    id="adjust_rhythm_analysis",
    name="节奏分析",
    category="adjust",
    description="分析小说的节奏，并给出调整建议。",
    system_prompt="你是一位小说节奏分析专家，擅长分析小说的节奏并给出调整建议。"
    "你需要根据用户提供的内容，分析其节奏，并给出具体的调整建议。"
    "之前的对话可能包含其他阶段的讨论，但请忽略它们，专注于当前任务。 如果需要引用之前的信息，请根据消息内容自行判断相关性。"
    "如果信息不足，可以用 ask_user 向用户提问。",
    allowed_tools=[
        "search_wiki",
        "get_wiki_page_by_title",
        "list_wiki_pages",
        "ask_user",
        "get_current_time",
    ],
)

RENDER_IMITATE = PipelineTool(
    id="render_imitate",
    name="仿写渲染",
    category="render",
    description="根据草稿和范文，将草稿渲染成符合范文风格的正文。",
    system_prompt=(
        "你是一位擅长模仿风格的写手。用户会提供草稿和范文，你需要分析范文的风格特征"
        "（如句式、用词、语气），然后将草稿中的内容改写为符合该风格的完整正文。"
        "之前的对话可能包含其他阶段的讨论，但请忽略它们，专注于当前任务。 如果需要引用之前的信息，请根据消息内容自行判断相关性。"
        "如果草稿中包含 {{占位符}}，请用合理的描述替换它们。"
    ),
    allowed_tools=[
        "search_wiki",
        "get_wiki_page_by_title",
        "list_wiki_pages",
        "ask_user",
        "get_current_time",
    ],
)

PIPELINE = {
    "common_helper": COMMON_HELPER,
    "explorer_inspiration": EXPLORE_INSPIRATION,
    "adjust_rhythm_analysis": ADJUST_RHYTHM_ANALYSIS,
    "render_imitate": RENDER_IMITATE,
}
