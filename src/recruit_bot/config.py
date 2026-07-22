from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    dashscope_api_key: str
    dashscope_base_url: str
    qwen_vl_model: str
    allowed_user_ids: frozenset[str]
    max_article_images: int
    request_timeout_seconds: int
    data_dir: Path

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        project_root = Path(__file__).resolve().parents[2]
        allowed = frozenset(
            item.strip()
            for item in os.getenv("ALLOWED_USER_IDS", "").split(",")
            if item.strip()
        )
        return cls(
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", "").strip(),
            dashscope_base_url=os.getenv(
                "DASHSCOPE_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ).rstrip("/"),
            qwen_vl_model=os.getenv("QWEN_VL_MODEL", "qwen3-vl-plus").strip(),
            allowed_user_ids=allowed,
            max_article_images=max(1, min(int(os.getenv("MAX_ARTICLE_IMAGES", "8")), 20)),
            request_timeout_seconds=max(5, int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))),
            data_dir=project_root / ".data",
        )

    def require_api_key(self) -> None:
        if not self.dashscope_api_key:
            raise RuntimeError("缺少 DASHSCOPE_API_KEY，请复制 .env.example 为 .env 并填写新密钥。")
