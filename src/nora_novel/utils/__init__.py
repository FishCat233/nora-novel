import re


def split_thought_response(content: str):
    """
    将消息内容拆分为思考部分和回答部分。
    思考部分由 [思考] 和 [结束思考] 标签包裹，其余内容默认为回答部分。
    """
    # 匹配思考块：开始标签单独一行，结束标签单独一行，中间内容跨行
    think_pattern = r"^\s*<思考>\s*$(.*?)^\s*<\/思考>\s*$"

    think_match = re.search(think_pattern, content, re.DOTALL | re.MULTILINE)

    if think_match:
        thought = think_match.group(1).strip()
        # 移除整个思考块（包括标签）得到回答部分
        start, end = think_match.start(), think_match.end()
        response = (content[:start] + content[end:]).strip()
    else:
        thought = None
        response = content.strip()

    return thought, response
