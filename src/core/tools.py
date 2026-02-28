from typing import Iterable
from openai.types.chat import ChatCompletionToolUnionParam

tools: Iterable[ChatCompletionToolUnionParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time with format",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_format": {
                        "type": "string",
                        "description": 'The format of the time, e.g. Example: "%d/%m/%Y, %H:%M:%S" for "2026/02/28, 13:02:24"',
                    }
                },
                "required": ["time_format"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "ask_user_question",
    #         "description": "Ask the user a clarification question before continuing",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "question": {
    #                     "type": "string",
    #                     "description": "The question to ask the user",
    #                 }
    #             },
    #             "required": ["question"],
    #         },
    #     },
    # }
]


class Tool:
    @staticmethod
    def dispatch(name: str, arguments: dict):
        if name == "get_current_time":
            return Tool.get_current_time(arguments["time_format"])

        raise ValueError(f"Unknown tool: {name}")

    @staticmethod
    def get_current_time(time_format: str):
        import datetime

        try:
            now = datetime.datetime.now()
            return now.strftime(time_format)
        except ValueError:
            return "Invalid time format"
