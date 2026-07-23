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
    feishu_app_id: str
    feishu_app_secret: str
    feishu_spreadsheet_token: str
    feishu_sheet_id: str
    feishu_wiki_node_token: str
    feishu_spreadsheet_url: str

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        project_root = Path(__file__).resolve().parents[2]
        allowed = frozenset(
            item.strip()
            for item in os.getenv("ALLOWED_USER_IDS", "").split(",")
            if item.strip()
        )
        wiki_node_token = os.getenv("FEISHU_WIKI_NODE_TOKEN", "").strip()
        spreadsheet_url = os.getenv("FEISHU_SPREADSHEET_URL", "").strip()
        if not spreadsheet_url and wiki_node_token:
            spreadsheet_url = f"https://my.feishu.cn/wiki/{wiki_node_token}?from=from_copylink"
        return cls(
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", "").strip(),
            dashscope_base_url=os.getenv("DASHSCOPE_BASE_URL", "").strip().rstrip("/"),
            qwen_vl_model=os.getenv("QWEN_VL_MODEL", "").strip(),
            allowed_user_ids=allowed,
            max_article_images=max(1, min(int(os.getenv("MAX_ARTICLE_IMAGES", "8")), 20)),
            request_timeout_seconds=max(5, int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))),
            data_dir=project_root / ".data",
            feishu_app_id=os.getenv("FEISHU_APP_ID", "").strip(),
            feishu_app_secret=os.getenv("FEISHU_APP_SECRET", "").strip(),
            feishu_spreadsheet_token=os.getenv("FEISHU_SPREADSHEET_TOKEN", "").strip(),
            feishu_sheet_id=os.getenv("FEISHU_SHEET_ID", "").strip(),
            feishu_wiki_node_token=wiki_node_token,
            feishu_spreadsheet_url=spreadsheet_url,
        )

    @property
    def feishu_configured(self) -> bool:
        return bool(
            self.feishu_app_id
            and self.feishu_app_secret
            and (self.feishu_spreadsheet_token or self.feishu_wiki_node_token)
        )

    def require_ai_config(self) -> None:
        missing = []
        if not self.dashscope_api_key:
            missing.append("DASHSCOPE_API_KEY")
        if not self.dashscope_base_url:
            missing.append("DASHSCOPE_BASE_URL")
        if not self.qwen_vl_model:
            missing.append("QWEN_VL_MODEL")
        if missing:
            names = "、".join(missing)
            raise RuntimeError(f"缺少 {names}，请复制 .env.example 为 .env 并填写。")
