from __future__ import annotations

import argparse

from .bot import run_bot
from .config import Settings
from .feishu import FeishuSpreadsheetStore
from .qwen import QwenRecruitmentAnalyzer
from .service import RecruitmentService
from .wechat_article import WeChatArticleReader


def build_service(settings: Settings) -> RecruitmentService:
    return RecruitmentService(
        WeChatArticleReader(settings.request_timeout_seconds, settings.max_article_images),
        QwenRecruitmentAnalyzer(settings),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="微信招聘整理机器人")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--bot", action="store_true", help="启动微信机器人")
    mode.add_argument("--text", help="测试一段招聘文字")
    mode.add_argument("--url", help="测试一个微信公众号链接")
    args = parser.parse_args()

    settings = Settings.load()
    if args.bot:
        service = build_service(settings) if settings.dashscope_api_key else None
        feishu = None
        if settings.feishu_configured:
            feishu = FeishuSpreadsheetStore(
                settings.feishu_app_id,
                settings.feishu_app_secret,
                settings.feishu_spreadsheet_token,
                settings.feishu_sheet_id,
                settings.feishu_wiki_node_token,
                settings.request_timeout_seconds,
            )
        run_bot(settings, service, feishu)
        return

    service = build_service(settings)
    source = args.text or args.url or ""
    print(service.process(source).format_for_wechat())


if __name__ == "__main__":
    main()
