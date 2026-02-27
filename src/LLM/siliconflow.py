from LLM.interface import ChatableILLM


class SiliconFlowLLM(ChatableILLM):
    def __init__(self, api_key: str):
        super().Setup(api_key=api_key)


SiliconFlowLLM.Setup(base_url="https://api.siliconflow.cn/v1")
