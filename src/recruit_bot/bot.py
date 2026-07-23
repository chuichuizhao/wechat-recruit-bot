from __future__ import annotations

import asyncio

from wechatbot import WeChatBot

from .config import Settings
from .feishu import FeishuSpreadsheetStore
from .inbox import InboxItem, JsonlInbox
from .service import RecruitmentService


def format_feishu_success(
    company: str,
    category: str,
    jobs: tuple[str, ...],
    unsubmitted_count: int,
) -> str:
    title = f"{company}-{jobs[0]}" if len(jobs) == 1 else f"{company}-{category}"
    return f"{title}\n\n已保存到飞书表格\n\n还有 {unsubmitted_count} 个未投递"


def run_bot(
    settings: Settings,
    service: RecruitmentService | None = None,
    feishu: FeishuSpreadsheetStore | None = None,
) -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    inbox = JsonlInbox(settings.data_dir / "inbox.jsonl")
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
            await bot.reply(message, "目前只支持文字或微信公众号文章链接。")
            return

        try:
            item = InboxItem.from_message(sender_id, text, getattr(message, "timestamp", None))
            inbox.save(item)
            label = "公众号链接" if item.kind == "wechat_article" else "文字"

            if service is None:
                await bot.reply(message, f"已收到{label}，编号：{item.id[:8]}")
                return

            await bot.send_typing(sender_id)
            result = await asyncio.to_thread(service.process, text)
            reply = result.format_for_wechat()
            saved_url = ""
            if feishu is not None:
                try:
                    save_result = await asyncio.to_thread(feishu.save, result)
                    reply = format_feishu_success(
                        result.company,
                        result.category,
                        result.jobs,
                        save_result.unsubmitted_count,
                    )
                    saved_url = settings.feishu_spreadsheet_url
                except Exception as error:
                    print(f"飞书保存失败：{error}")
                    reply += "\n\n飞书保存失败，招聘整理结果未受影响。"
            await bot.reply(message, reply)
            if saved_url:
                # A standalone URL is much more reliably recognized as clickable
                # by WeChat than a URL embedded in other bot-generated text.
                await bot.send(sender_id, saved_url)
        except Exception as error:
            print(f"处理失败：{error}")
            await bot.reply(message, f"消息处理失败：{error}")

    if not settings.allowed_user_ids:
        print("警告：ALLOWED_USER_IDS 为空，机器人会响应所有联系人。")
        print("首次测试后，请把日志中的 user_id 写入 .env 并重启。")
    if service is None:
        print("接收模式：消息将保存到 .data/inbox.jsonl（未启用 AI 整理）。")
    elif feishu is not None:
        print("飞书同步已启用：整理成功后将自动写入电子表格。")
    bot.run()
