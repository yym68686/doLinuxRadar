#!/usr/bin/env python
# pylint: disable=unused-argument

import logging
from telegram import Update
from telegram import BotCommand, Update
from telegram.ext import CommandHandler, ApplicationBuilder, Application, AIORateLimiter, InlineQueryHandler, ContextTypes
# 启用日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.ERROR)

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

    def add_tag(self, user_id, tag):
        if 'tags' not in self.config[user_id].data:
            self.config[user_id]['tags'] = []
        if isinstance(tag, list):
            self.config[user_id]['tags'] = []
            for t in tag:
                self.config[user_id]['tags'].append(t)
        else:
            if tag not in self.config[user_id]['tags']:
                self.config[user_id]['tags'].append(tag)

    def add_page(self, user_id, page):
        if 'pages' not in self.config[user_id].data:
            self.config[user_id]['pages'] = []
        if page not in self.config[user_id]['pages']:
            self.config[user_id]['pages'].append(page)

    def get_tags(self, user_id):
        return self.config[user_id]['tags'] if 'tags' in self.config[user_id].data else []

    def get_pages(self, user_id):
        return self.config[user_id]['pages'] if 'pages' in self.config[user_id].data else []

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
        # 发送 GET 请求
        with httpx.Client() as client:
            response = client.get(url)

        # 检查请求是否成功
        response.raise_for_status()

        # 解析 JSON 内容
        data = response.json()

        # 返回解析后的 JSON 数据
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
    result = get_and_parse_json(url)["topic_list"]["topics"]
    # print(json.dumps(result, indent=2, ensure_ascii=False))
    titles = [i["title"].lower() for i in result]
    # print("context.job.chat_id", context.job.chat_id)
    # print("UserConfig[str(context.job.chat_id)]", UserConfig[str(context.job.chat_id)])
    chat_id = context.job.chat_id
    tags = user_config.get_tags(str(chat_id))
    for index, title in enumerate(titles):
        print(tags, any(tag in title for tag in tags), title)
        if any(tag in title for tag in tags):
            if result[index]['id'] not in user_config.get_pages(str(chat_id)):
                print("bingo", tags, title)
                tag_mess = " ".join([f"#{tag}" for tag in tags if tag in title])
                user_config.add_page(str(chat_id), result[index]['id'])
                url = f"https://linux.do/t/topic/{result[index]['id']}"
                message = (
                    f"{tag_mess}\n\n"
                    f"{title}\n\n"
                    f"{url}"
                )
                await context.bot.send_message(chat_id=chat_id, text=message)
tips_message = (
    "欢迎使用 Linux.do 风向标 bot！\n\n"
    "使用 /set 10 来设置每10秒执行一次的任务。\n\n"
    "使用 /unset 来取消任务。\n\n"
    "使用 /set_tags 免费 公益 来设置含有指定关键词的话题。\n\n"
    "有 bug 请联系 @yym68686\n\n"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """发送使用说明"""
    await update.message.reply_text(tips_message)

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
        context.job_queue.run_repeating(scheduled_function,
                                        interval=10,
                                        first=1,
                                        chat_id=chat_id,
                                        name=str(chat_id))
        # context.job_queue.run_once(alarm, due, chat_id=chat_id, name=str(chat_id), data=due)

        text = "Timer successfully set!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds>")

async def set_tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "成功取消定时任务！" if job_removed else "您没有活动的定时任务。"
    await update.message.reply_text(text)

async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand('set', '设置嗅探间隔'),
        BotCommand('set_tags', '设置监控关键词'),
        BotCommand('unset', '取消监控linux.do'),
        BotCommand('start', '使用简介'),
    ])
    await application.bot.set_my_description(tips_message)

def main() -> None:
    """运行bot"""
    # 创建Application并传入您的bot token
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

    # 添加命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("unset", unset))
    application.add_handler(CommandHandler("set_tags", set_tags))
    # 运行bot直到用户按下Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()