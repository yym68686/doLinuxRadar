import re # 导入 re 模块
import json
import requests

# 定义获取并解析 pre 标签内容的函数
def fetch_and_parse_pre_content(target_url, flare_solverr_url="http://localhost:8191/v1"):
    """
    发送请求到 FlareSolverr，获取指定 URL 的内容，
    提取第一个 <pre> 标签内的文本，并将其解析为 JSON。

    Args:
        target_url (str): 需要 FlareSolverr 抓取的目标 URL。
        flare_solverr_url (str, optional): FlareSolverr v1 API 的 URL。
                                          默认为 "http://localhost:8191/v1"。

    Returns:
        dict or None: 解析后的 JSON 对象，如果未找到 <pre> 标签或发生错误则返回 None。
    """
    headers = {"Content-Type": "application/json"}
    data = {
        "cmd": "request.get",
        "url": target_url,
        "maxTimeout": 60000
    }
    try:
        response = requests.post(flare_solverr_url, headers=headers, json=data, timeout=70) # 增加超时
        response.raise_for_status() # 检查 HTTP 请求错误
        response_data = response.json()
        html_content = response_data.get("solution", {}).get("response")

        if not html_content:
            print("错误：未能从 FlareSolverr 响应中获取 HTML 内容")
            return None

        # 使用正则表达式查找 <pre> 标签内的内容
        match = re.search(r"<pre[^>]*>(.*?)</pre>", html_content, re.DOTALL)

        # 检查是否找到匹配项
        if match:
            extracted_text = match.group(1).strip() # 获取并清理提取的文本
            try:
                # 尝试解析 JSON
                result = json.loads(extracted_text)
                return result # 返回解析后的 JSON 对象
            except json.JSONDecodeError as e:
                print(f"错误：解析 JSON 失败 - {e}")
                print(f"提取到的文本内容：\n{extracted_text}")
                return None
        else:
            print("未在响应中找到 <pre> 标签内的内容")
            # print(f"原始 HTML 内容：\n{html_content}") # 取消注释以调试
            return None
    except requests.exceptions.RequestException as e:
        print(f"错误：请求 FlareSolverr 时发生错误 - {e}")
        return None
    except Exception as e:
        print(f"发生未知错误：{e}")
        return None

# --- 主程序部分 ---
if __name__ == "__main__":
    # 调用函数并传入目标 URL
    target_linux_do_url = "https://linux.do/latest.json"
    parsed_data = fetch_and_parse_pre_content(target_linux_do_url)

    # 打印结果
    if parsed_data:
        # 使用 json.dumps 美化输出
        print(json.dumps(parsed_data, indent=4, ensure_ascii=False))
    else:
        print("未能成功获取或解析数据。")