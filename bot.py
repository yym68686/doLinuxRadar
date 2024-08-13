#!/usr/bin/env python
# pylint: disable=unused-argument

import os
import logging
from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ApplicationBuilder, Application, AIORateLimiter, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.ERROR)


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
            return json.load(f)

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

    def add_tag(self, user_id, tag):
        if 'tags' not in self.config[user_id].data:
            self.config[user_id]['tags'] = []
        if isinstance(tag, list):
            self.config[user_id]['tags'] = []
            for t in tag:
                self.config[user_id]['tags'].append(t)
            update_user_config(user_id, 'tags', self.config[user_id]['tags'])
        else:
            if tag not in self.config[user_id]['tags']:
                self.config[user_id]['tags'].append(tag)

    def add_page(self, user_id, page):
        if 'pages' not in self.config[user_id].data:
            self.config[user_id]['pages'] = []
        if page not in self.config[user_id]['pages']:
            self.config[user_id]['pages'].append(page)
        update_user_config(user_id, 'pages', self.config[user_id]['pages'])

    def get_tags(self, user_id):
        return self.config[user_id]['tags'] if 'tags' in self.config[user_id].data else []

    def get_pages(self, user_id):
        return self.config[user_id]['pages'] if 'pages' in self.config[user_id].data else []

    def get_timer(self, user_id):
        return self.config[user_id]['timer'] if 'timer' in self.config[user_id].data else True

    def to_json(self):
        def nested_dict_to_dict(nd):
            if isinstance(nd, NestedDict):
                return {k: nested_dict_to_dict(v) for k, v in nd.data.items()}
            return nd

        serializable_config = nested_dict_to_dict(self.config)
        return json.dumps(serializable_config, ensure_ascii=False, indent=2)

    def __str__(self):
        return str(self.config)

user_config = UserConfig()

import json
def get_and_parse_json(url):
    import httpx
    try:
        with httpx.Client() as client:
            response = client.get(url)
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

# 这是将被定时执行的函数
async def scheduled_function(context: ContextTypes.DEFAULT_TYPE) -> None:
    """这个函数将每10秒执行一次"""
    url = "https://linux.do/latest.json"
    result = None
    try:
        result = get_and_parse_json(url)["topic_list"]["topics"]
    except Exception as e:
        logging.error(f"获取数据失败：{e}")
    if result is None:
        logging.error("获取数据失败")
        return
    # print(json.dumps(result, indent=2, ensure_ascii=False))
    titles = [i["title"].lower() for i in result]
    for chat_id in user_config.config.data.keys():
        chat_id = int(chat_id)
        print("chat_id", chat_id, user_config.get_timer(str(chat_id)))
        if user_config.get_timer(str(chat_id)) == False:
            continue
        tags = user_config.get_tags(str(chat_id))
        for index, title in enumerate(titles):
            # print(tags, any(tag in title for tag in tags), title)
            if any(tag in title for tag in tags):
                if result[index]['id'] not in user_config.get_pages(str(chat_id)):
                    print("bingo", tags, title)
                    tag_mess = " ".join([f"#{tag}" for tag in tags if tag in title])
                    user_config.add_page(str(chat_id), result[index]['id'])
                    url = f"https://linux.do/t/topic/{result[index]['id']}"
                    message = (
                        f"{tag_mess}\n"
                        f"{title}\n"
                        f"{url}"
                    )
                    await context.bot.send_message(chat_id=chat_id, text=message)

tips_message = (
    "欢迎使用 Linux.do 风向标 bot！\n\n"
    "使用 /tags 免费 公益 来设置含有指定关键词的话题。\n\n"
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
            interval=10,
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
    tags = [tag.lower() for tag in tags]
    user_config.add_tag(str(chat_id), tags)
    print("UserConfig", user_config.to_json())
    await update.effective_message.reply_text("Tags successfully set!")

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

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()