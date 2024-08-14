import re

# 测试函数
test_strings = [
    "这是一个PT下载站",
    "GPT是一种人工智能模型",
    "PT和GPT是不同的概念",
    "PTPT是重复的PT",
    "GPT不应该被匹配",
    "PT 种子下载很方便"
]

for string in test_strings:
    pattern = '(?<![A-Za-z])PT(?![A-Za-z])'
    result = re.findall(pattern, string)
    print(f"字符串： '{string}'")
    print(f"匹配结果： {result}\n")