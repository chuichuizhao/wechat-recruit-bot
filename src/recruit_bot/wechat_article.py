from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image


IPHONE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
    "AppleWebKit/605.1.15 Mobile/15E148 MicroMessenger/8.0"
)


@dataclass(frozen=True)
class Article:
    title: str
    text: str
    image_urls: tuple[str, ...]
    source_url: str


class WeChatArticleReader:
    def __init__(self, timeout: int = 20, max_images: int = 8) -> None:
        self.timeout = timeout
        self.max_images = max_images
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": IPHONE_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,*/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
        )

    def _get_with_retry(self, url: str, **kwargs) -> requests.Response:
        """Retry transient disconnects frequently returned by mp.weixin.qq.com."""
        last_error: requests.RequestException | None = None
        for attempt in range(3):
            try:
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    **kwargs,
                )
                response.raise_for_status()
                return response
            except requests.RequestException as error:
                last_error = error
                self.session.close()
                if attempt < 2:
                    time.sleep(attempt + 1)

        raise ValueError("公众号页面连接失败，已自动重试 3 次，请稍后重新发送链接。") from last_error

    @staticmethod
    def validate_url(url: str) -> str:
        parsed = urlparse(url.strip())
        if parsed.scheme != "https" or parsed.hostname != "mp.weixin.qq.com":
            raise ValueError("目前只支持 https://mp.weixin.qq.com 的公众号文章链接。")
        return parsed.geturl()

    def read(self, url: str) -> Article:
        safe_url = self.validate_url(url)
        response = self._get_with_retry(safe_url)
        if urlparse(response.url).hostname != "mp.weixin.qq.com":
            raise ValueError("公众号链接跳转到了不受支持的站点。")
        response.encoding = response.apparent_encoding or "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        title_node = soup.select_one("#activity-name") or soup.find("h1")
        content = soup.select_one("#js_content") or soup.find("article")
        if content is None:
            raise ValueError("未找到公众号正文，文章可能需要验证或已被删除。")

        title = title_node.get_text(" ", strip=True) if title_node else ""
        text = content.get_text("\n", strip=True)
        image_urls: list[str] = []
        seen: set[str] = set()
        for image in content.find_all("img"):
            source = image.get("data-src") or image.get("src")
            if not source:
                continue
            absolute = urljoin(safe_url, source)
            if absolute not in seen:
                seen.add(absolute)
                image_urls.append(absolute)
            if len(image_urls) >= self.max_images:
                break

        return Article(title=title, text=text[:20_000], image_urls=tuple(image_urls), source_url=safe_url)

    def download_image(self, url: str) -> tuple[bytes, str]:
        response = self._get_with_retry(
            url,
            headers={"Referer": "https://mp.weixin.qq.com/"},
        )
        if len(response.content) > 12 * 1024 * 1024:
            raise ValueError("图片超过 12MB，已跳过。")

        image = Image.open(BytesIO(response.content)).convert("RGB")
        image.thumbnail((1600, 1600))
        output = BytesIO()
        image.save(output, format="JPEG", quality=86, optimize=True)
        return output.getvalue(), "image/jpeg"
