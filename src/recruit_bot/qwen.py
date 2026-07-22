from __future__ import annotations

import base64
import json
from dataclasses import dataclass

from openai import OpenAI

from .config import Settings


SYSTEM_PROMPT = """你是专业的招聘信息整理助手。只依据用户提供的文字和图片提取信息，不要猜测。
必须返回合法 JSON，字段固定为：公司、类别、岗位、地点、投递网址、截止时间、摘要、信息缺失。
类别只能是“实习生招聘”“校园招聘”“社会招聘”或“未知”。岗位、地点、信息缺失是字符串数组。
时间范围取与报名或投递相关的结束日期；不要把面试或入职时间误认为截止日期。未知字段使用“未知”或空数组。"""


@dataclass(frozen=True)
class RecruitmentSummary:
    company: str
    category: str
    jobs: tuple[str, ...]
    locations: tuple[str, ...]
    apply_url: str
    deadline: str
    summary: str
    missing: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict) -> "RecruitmentSummary":
        return cls(
            company=str(data.get("公司") or "未知"),
            category=str(data.get("类别") or "未知"),
            jobs=tuple(str(x) for x in (data.get("岗位") or []) if x),
            locations=tuple(str(x) for x in (data.get("地点") or []) if x),
            apply_url=str(data.get("投递网址") or "未知"),
            deadline=str(data.get("截止时间") or "未知"),
            summary=str(data.get("摘要") or ""),
            missing=tuple(str(x) for x in (data.get("信息缺失") or []) if x),
        )

    def format_for_wechat(self) -> str:
        jobs = "\n".join(f"• {job}" for job in self.jobs) or "未知"
        locations = "、".join(self.locations) or "未知"
        missing = "、".join(self.missing) or "无"
        return (
            f"【招聘整理】\n"
            f"公司：{self.company}\n"
            f"类别：{self.category}\n"
            f"地点：{locations}\n"
            f"截止时间：{self.deadline}\n"
            f"投递地址：{self.apply_url}\n\n"
            f"岗位：\n{jobs}\n\n"
            f"摘要：{self.summary or '未知'}\n"
            f"缺失信息：{missing}"
        )


class QwenRecruitmentAnalyzer:
    def __init__(self, settings: Settings) -> None:
        settings.require_api_key()
        self.model = settings.qwen_vl_model
        self.client = OpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
        )

    def analyze(
        self,
        text: str,
        images: list[tuple[bytes, str]] | None = None,
        source_url: str = "",
    ) -> RecruitmentSummary:
        content: list[dict] = [
            {
                "type": "text",
                "text": (
                    "请提取以下招聘信息并输出 JSON。\n"
                    f"来源：{source_url or '用户直接发送'}\n"
                    f"正文：\n{text[:20_000]}"
                ),
            }
        ]
        for image_bytes, mime_type in images or []:
            encoded = base64.b64encode(image_bytes).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
                }
            )

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        raw = completion.choices[0].message.content or "{}"
        return RecruitmentSummary.from_dict(json.loads(raw))
