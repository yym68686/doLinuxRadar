import os
import json

def get_and_parse_json(url, cf_clearance = None):
    import httpx
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    }
    cookie_dict = {}
    if cf_clearance:
        cookie_dict["cf_clearance"] = cf_clearance
    try:
        with httpx.Client() as client:
            # 直接将字典传递给 cookies 参数
            response = client.get(url, headers=headers, cookies=cookie_dict)
        response.raise_for_status()
        data = response.json()
        return data

    except httpx.HTTPStatusError as e:
        print(f"HTTP 错误： {e}")
    except httpx.RequestError as e:
        print(f"网络请求错误： {e}")
    except json.JSONDecodeError:
        print("JSON 解析错误")
    except Exception as e:
        print(f"发生未知错误： {e}")

    return None

url = "https://linux.do/latest.json"

cf_clearance = os.getenv("CF_CLEARANCE")
print(get_and_parse_json(url, cf_clearance))