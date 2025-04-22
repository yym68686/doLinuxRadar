import feedparser # 导入 feedparser 库

def get_and_parse_rss(url): # 函数名修改为 get_and_parse_rss
    import httpx
    try:
        with httpx.Client() as client:
            # 直接将字典传递给 cookies 参数
            response = client.get(url)
        response.raise_for_status()
        # 使用 feedparser 解析返回的文本
        feed_data = feedparser.parse(response.text)
        return feed_data # 返回解析后的 feed 对象

    except httpx.HTTPStatusError as e:
        print(f"HTTP 错误： {e}")
    except httpx.RequestError as e:
        print(f"网络请求错误： {e}")
    except Exception as e:
        print(f"发生未知错误： {e}")

    return None

url = "https://linux.do/latest.rss"

feed = get_and_parse_rss(url) # 调用修改后的函数

# 检查是否成功获取并解析 feed
if feed:
    print(f"Feed 标题: {feed.feed.title}") # 打印 Feed 的标题
    print("最新帖子:")
    # 遍历 feed 中的条目 (entries) 并打印标题和链接
    for entry in feed.entries:
        print(f"- {entry.title} ({entry.link})")
else:
    print("无法获取或解析 RSS feed。")

# 原来的 print(get_and_parse_json(url)) 被移除