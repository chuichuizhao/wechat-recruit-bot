from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4


URL_PATTERN = re.compile(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+")
TRAILING_PUNCTUATION = "。），,)]！!；;：:\"'》>"


@dataclass(frozen=True)
class InboxItem:
    id: str
    sender_id: str
    kind: str
    text: str
    urls: tuple[str, ...]
    received_at: str

    @classmethod
    def from_message(
        cls,
        sender_id: str,
        text: str,
        received_at: datetime | None = None,
    ) -> "InboxItem":
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("消息内容不能为空。")

        urls = tuple(match.group(0).rstrip(TRAILING_PUNCTUATION) for match in URL_PATTERN.finditer(cleaned))
        has_wechat_article = any(
            urlparse(url).scheme == "https" and urlparse(url).hostname == "mp.weixin.qq.com"
            for url in urls
        )
        timestamp = received_at or datetime.now(timezone.utc)
        return cls(
            id=uuid4().hex,
            sender_id=sender_id,
            kind="wechat_article" if has_wechat_article else "text",
            text=cleaned,
            urls=urls,
            received_at=timestamp.astimezone(timezone.utc).isoformat(),
        )


class JsonlInbox:
    """Append-only local inbox; one JSON object per line."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, item: InboxItem) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(item)
        payload["urls"] = list(item.urls)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
