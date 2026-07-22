from __future__ import annotations

import asyncio

from wechatbot import WeChatBot

from .config import Settings
from .service import RecruitmentService


def run_bot(settings: Settings, service: RecruitmentService) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    bot = WeChatBot(cred_path=str(settings.data_dir / "credentials.json"))

    @bot.on_message
    async def handle(message) -> None:
        sender_id = str(message.user_id)
        text = (message.text or "").strip()
        print(f"收到消息 user_id={sender_id!r} type={message.type!r}")

        if settings.allowed_user_ids and sender_id not in settings.allowed_user_ids:
            print(f"忽略未授权用户：{sender_id}")
            return
        if not text:
            await bot.reply(message, "目前只支持招聘文字或微信公众号文章链接。")
            return

        try:
            await bot.send_typing(sender_id)
            result = await asyncio.to_thread(service.process, text)
            await bot.reply(message, result.format_for_wechat())
        except Exception as error:
            print(f"处理失败：{error}")
            await bot.reply(message, f"整理失败：{error}")

    if not settings.allowed_user_ids:
        print("警告：ALLOWED_USER_IDS 为空，机器人会响应所有联系人。")
        print("首次测试后，请把日志中的 user_id 写入 .env 并重启。")
    bot.run()
