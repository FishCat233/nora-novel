import re


def split_thought_response(content: str):
    """
    将消息内容拆分为思考部分和回答部分。
    """
    # 匹配思考块：开始标签单独一行，结束标签单独一行，中间内容跨行
    think_pattern = r"^\s*\[思考\]\s*$(.*?)^\s*\[结束思考\]\s*$"
    # 匹配回答块
    answer_pattern = r"^\s*\[回答\]\s*$(.*?)^\s*\[结束回答\]\s*$"

    think_match = re.search(think_pattern, content, re.DOTALL | re.M)
    answer_match = re.search(answer_pattern, content, re.DOTALL | re.M)

    thought = think_match.group(1).strip() if think_match else None

    if answer_match:
        response = answer_match.group(1).strip()
    else:
        # 没有回答块：如果有思考块，则回答为 None；否则整个内容作为回答
        response = None if think_match else content.strip()

    return thought, response
