from __future__ import annotations

import re

from .qwen import QwenRecruitmentAnalyzer, RecruitmentSummary
from .wechat_article import WeChatArticleReader


WECHAT_URL_PATTERN = re.compile(r"https://mp\.weixin\.qq\.com/[^\s]+")


class RecruitmentService:
    def __init__(self, reader: WeChatArticleReader, analyzer: QwenRecruitmentAnalyzer) -> None:
        self.reader = reader
        self.analyzer = analyzer

    def process(self, message: str) -> RecruitmentSummary:
        cleaned = message.strip()
        if not cleaned:
            raise ValueError("请发送招聘文字或微信公众号文章链接。")

        match = WECHAT_URL_PATTERN.search(cleaned)
        if not match:
            return self.analyzer.analyze(cleaned)

        article = self.reader.read(match.group(0).rstrip("。），,)]"))
        images: list[tuple[bytes, str]] = []
        for image_url in article.image_urls:
            try:
                images.append(self.reader.download_image(image_url))
            except Exception as error:
                print(f"跳过图片 {image_url}: {error}")

        article_text = f"标题：{article.title}\n{article.text}"
        return self.analyzer.analyze(article_text, images, article.source_url)
