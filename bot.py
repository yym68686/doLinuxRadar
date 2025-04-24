#!/usr/bin/env python
# pylint: disable=unused-argument

import os
import re
import logging
import requests
from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ApplicationBuilder, Application, AIORateLimiter, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("apscheduler.executors.default").setLevel(logging.ERROR)


ADMIN_LIST = os.environ.get('ADMIN_LIST', None)
if ADMIN_LIST:
    ADMIN_LIST = [int(id) for id in ADMIN_LIST.split(",")]
# 判断是否是管理员
def AdminAuthorization(func):
    async def wrapper(*args, **kwargs):
        update, context = args[:2]
        chatid = update.message.chat_id
        if ADMIN_LIST == None:
            return await func(*args, **kwargs)
        if (update.effective_user.id not in ADMIN_LIST):
            message = (
                f"`Hi, {update.effective_user.username}!`\n\n"
                f"id: `{update.effective_user.id}`\n\n"
                f"您没有权限访问！需要管理员权限。\n\n"
            )
            await context.bot.send_message(chat_id=chatid, text=message, parse_mode='MarkdownV2')
            return
        return await func(*args, **kwargs)
    return wrapper

def get_time():
    from datetime import datetime, timedelta, timezone
    tz_utc_8 = timezone(timedelta(hours=8))
    beijing_time = datetime.now(timezone.utc).astimezone(tz_utc_8)
    return beijing_time.strftime("%Y-%m-%d %H:%M:%S")

import json
import fcntl
from contextlib import contextmanager

CONFIG_DIR = os.environ.get('CONFIG_DIR', 'user_configs')

@contextmanager
def file_lock(filename):
    with open(filename, 'a+') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield f
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

def save_user_config(user_id, config):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    filename = os.path.join(CONFIG_DIR, f'{user_id}.json')

    with file_lock(filename):
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

def load_user_config(user_id):
    filename = os.path.join(CONFIG_DIR, f'{user_id}.json')

    if not os.path.exists(filename):
        return {}

    with file_lock(filename):
        with open(filename, 'r') as f:
            content = f.read()
            if not content.strip():
                return {}
            else:
                return json.loads(content)

def update_user_config(user_id, key, value):
    config = load_user_config(user_id)
    config[key] = value
    save_user_config(user_id, config)

class NestedDict:
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        if key not in self.data:
            self.data[key] = NestedDict()
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __str__(self):
        return str(self.data)

    def keys(self):
        return self.data.keys()

class UserConfig:
    def __init__(self):
        self.config = NestedDict()
        self.load_all_configs()

    def load_all_configs(self):
        if not os.path.exists(CONFIG_DIR):
            return

        for filename in os.listdir(CONFIG_DIR):
            if filename.endswith('.json'):
                user_id = filename[:-5]  # 移除 '.json' 后缀
                user_config = load_user_config(user_id)
                self.config[user_id] = NestedDict()
                for key, value in user_config.items():
                    self.config[user_id][key] = value

    def set_timer(self, user_id):
        if 'timer' not in self.config[user_id].data:
            self.config[user_id]['timer'] = True
        self.config[user_id]['timer'] = not self.config[user_id]['timer']
        update_user_config(user_id, 'timer', self.config[user_id]['timer'])
        return self.config[user_id]['timer']

    def set_value(self, user_id, key, value: list, append=False):
        if key not in self.config[user_id].data:
            self.config[user_id][key] = []
        if append == False:
            self.config[user_id][key] = []
        for t in value:
            self.config[user_id][key].append(t)
        update_user_config(user_id, key, self.config[user_id][key])

    def get_value(self, user_id, key, default=[]):
        return self.config[user_id][key] if key in self.config[user_id].data else default

    def to_json(self, user_id=None):
        def nested_dict_to_dict(nd):
            if isinstance(nd, NestedDict):
                return {k: nested_dict_to_dict(v) for k, v in nd.data.items()}
            return nd

        if user_id:
            serializable_config = nested_dict_to_dict(self.config[user_id])
        else:
            serializable_config = nested_dict_to_dict(self.config)

        return json.dumps(serializable_config, ensure_ascii=False, indent=2)

    def __str__(self):
        return str(self.config)

user_config = UserConfig()

import json
def get_and_parse_json(target_url, flare_solverr_url="http://localhost:8191/v1"):
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

from telegram.error import Forbidden, TelegramError
async def is_bot_blocked(bot, user_id: int) -> bool:
    try:
        # 尝试向用户发送一条测试消息
        await bot.send_chat_action(chat_id=user_id, action="typing")
        return False  # 如果成功发送，说明机器人未被封禁
    except Forbidden:
        print("error:", user_id, "已封禁机器人")
        return True  # 如果收到Forbidden错误，说明机器人被封禁
    except TelegramError:
        # 处理其他可能的错误
        return False  # 如果是其他错误，我们假设机器人未被封禁

# 这是将被定时执行的函数
async def scheduled_function(context: ContextTypes.DEFAULT_TYPE) -> None:
    """这个函数将每10秒执行一次"""
    url = "https://linux.do/latest.json"
    result = None
    flare_solverr_url = os.environ.get("FLARESOLLVERR_URL", "http://localhost:8191/v1")
    try:
        result = get_and_parse_json(url, flare_solverr_url)["topic_list"]["topics"]
    except Exception as e:
        logging.error("获取数据失败：%s", repr(e))
        return
    # print(json.dumps(result, indent=2, ensure_ascii=False))
    titles = [i["title"].lower() for i in result]
    for chat_id in user_config.config.data.keys():
        chat_id = int(chat_id)
        tags = user_config.get_value(str(chat_id), "tags", default=[])
        if tags == []:
            continue
        re_rule = "|".join(tags)
        pages = user_config.get_value(str(chat_id), "pages", default=[])
        timer = user_config.get_value(str(chat_id), "timer", default=True)
        if timer == False:
            continue
        for index, title in enumerate(titles):
            findall_result = list(set(re.findall(re_rule, title)))
            page_id = result[index]['id']
            url = f"https://linux.do/t/topic/{page_id}"
            if ADMIN_LIST and chat_id in ADMIN_LIST:
                print("ADMIN_LIST", findall_result, chat_id, page_id, title)
            if findall_result and page_id not in pages and not await is_bot_blocked(context.bot, chat_id):
                print(get_time(), tags, chat_id, page_id, title)
                tag_mess = " ".join([f"#{tag}" for tag in findall_result])
                message = (
                    f"{tag_mess}\n"
                    f"{title}\n"
                    f"{url}"
                )
                await context.bot.send_message(chat_id=chat_id, text=message)
                user_config.set_value(str(chat_id), "pages", [page_id], append=True)

tips_message = (
    "欢迎使用 Linux.do 风向标 bot！\n\n"
    "使用 /tags 免费 公益 来设置含有指定关键词的话题。\n\n"
    "关键词支持正则匹配，例如我想匹配openai，但是不想匹配openair，可以使用/tags (?<![A-Za-z])openai(?![A-Za-z])\n\n"
    "使用 /set 10 来设置每10秒执行一次的任务。\n\n"
    "使用 /unset 来取消或者打开消息推送。\n\n"
    "有 bug 请联系 @yym68686\n\n"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """发送使用说明"""
    await update.message.reply_text(tips_message)

@AdminAuthorization
async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = float(context.args[0])
        if due < 0:
            await update.effective_message.reply_text("Sorry we can not go back to future!")
            return

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_repeating(
            scheduled_function,
            interval=due,
            first=1,
            chat_id=chat_id,
            name=str(chat_id)
        )

        text = "Timer successfully set!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds>")

async def tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """设置标签"""
    chat_id = update.effective_message.chat_id
    tags = context.args
    tags = list(set([tag.lower() for tag in tags]))
    user_config.set_value(str(chat_id), "tags", tags, append=False)
    print("UserConfig", user_config.to_json(str(chat_id)))
    if tags == []:
        await update.effective_message.reply_text("📖 关键词已清空！")
    else:
        await update.effective_message.reply_text("📖 监控关键词设置成功！")

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """如果存在，则移除指定名称的任务"""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """取消定时任务"""
    chat_id = update.message.chat_id
    # job_removed = remove_job_if_exists(str(chat_id), context)
    # text = "成功取消定时任务！" if job_removed else "您没有活动的定时任务。"
    timer_status = user_config.set_timer(str(chat_id))
    text = "已关闭消息推送 📢！" if timer_status == False else "已开启消息推送 📢！"
    await update.message.reply_text(text)

async def error(update, context):
    import traceback
    traceback_string = traceback.format_exception(None, context.error, context.error.__traceback__)
    if "telegram.error.TimedOut: Timed out" in traceback_string:
        print('telegram.error.TimedOut: Timed out')
        return
    if "telegram.error.NetworkError: Bad Gateway" in traceback_string:
        print('telegram.error.NetworkError: Bad Gateway')
        return

async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand('tags', '设置监控关键词（空格隔开）'),
        BotCommand('set', '设置嗅探间隔(秒)'),
        BotCommand('unset', '关闭或打开消息推送'),
        BotCommand('start', 'linux.do 风向标使用简介'),
    ])
    await application.bot.set_my_description(tips_message)

def main() -> None:
    """运行bot"""
    import os
    BOT_TOKEN = os.environ.get('BOT_TOKEN', None)
    time_out = 600
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .connection_pool_size(65536)
        .get_updates_connection_pool_size(65536)
        .read_timeout(time_out)
        .pool_timeout(time_out)
        .get_updates_read_timeout(time_out)
        .get_updates_write_timeout(time_out)
        .get_updates_pool_timeout(time_out)
        .get_updates_connect_timeout(time_out)
        .rate_limiter(AIORateLimiter(max_retries=5))
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("unset", unset))
    application.add_handler(CommandHandler("tags", tags))
    application.add_error_handler(error)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()