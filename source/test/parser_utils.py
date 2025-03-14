import re
from datetime import datetime


def unified_preprocessing(text: str) -> str:
    """统一预处理模块（处理换行/空格混合格式）"""
    # 替换所有换行符为空格
    text = text.replace('\n', ' ')

    # 智能空格压缩（合并连续空格）
    text = re.sub(r'\s+', ' ', text).strip()

    # 关键分隔符修复
    text = re.sub(
        r'(?i)(posted\s*on)(?=\w)',
        lambda m: m.group(1) + ' ',
        text
    )  # 处理Postedon粘连

    # 标签与数字分离（如#trump2024 → #trump 2024）
    text = re.sub(r'(#\w+)(\d)', r'\1 \2', text)

    return text


def robust_parser(text: str) -> str:
    """混合格式解析器（兼容换行/无换行）"""
    processed_text = unified_preprocessing(text)

    # 动态模式匹配
    pattern = re.compile(
        r'^(?P<question>.*?)\s+'
        r'(?P<views>\d+\sviews\s.*?\sdays?)\s+'
        r'(?P<date>Posted\son\s(?:Jan|Feb|Mar|Apr|May|Jun|'
        r'Jul|Aug|Sep|Oct|Nov|Dec)\s\d{1,2})$',
        re.IGNORECASE | re.VERBOSE
    )

    match = pattern.match(processed_text)
    if not match:
        raise ValueError(f"解析失败: {processed_text}")

    # 日期有效性校验
    try:
        datetime.strptime(match.group('date'), 'Posted on %b %d')
    except ValueError:
        raise ValueError("日期不存在（如2月30日）")

    return f"""1. {match.group('views')}  
2. {match.group('question')}  
3. {match.group('date')}"""


# 测试不同换行格式
test_cases = [
    # 带换行案例
    "Should we\nbuild a wall? #border\n2023\n2198 views in the last 7 days\nPosted on Feb 28",

    # 混合换行案例
    "Gun control laws\n\n\n1500 views in the last 2 days Posted on\nMar 15",

    # 无换行案例
    "Climate change denial#env 5000 views in the last 24 days Posted on May 31"
]
# 入口函数
if __name__ == "__main__":
    for case in test_cases:
        try:
            print("原始输入:", case)
            print("预处理后:", unified_preprocessing(case))
            print(robust_parser(case))
        except Exception as e:
            print(f"错误: {str(e)}")
        print("---")

