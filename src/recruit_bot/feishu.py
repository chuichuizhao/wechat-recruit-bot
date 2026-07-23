from __future__ import annotations

from dataclasses import dataclass

import requests

from .qwen import RecruitmentSummary


STATUS_OPTIONS = ("未投递", "已投递", "一面", "二面", "offer")


@dataclass(frozen=True)
class FeishuSaveResult:
    updated_range: str
    unsubmitted_count: int


class FeishuSpreadsheetStore:
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        spreadsheet_token: str = "",
        sheet_id: str = "",
        wiki_node_token: str = "",
        timeout: int = 20,
    ) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.spreadsheet_token = spreadsheet_token
        self.sheet_id = sheet_id
        self.wiki_node_token = wiki_node_token
        self.timeout = timeout
        self.session = requests.Session()
        self._status_column_ready = False
        self._row_count: int | None = None

    def _tenant_access_token(self) -> str:
        response = self.session.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 0 or not payload.get("tenant_access_token"):
            raise RuntimeError(f"飞书鉴权失败：{payload.get('msg') or payload.get('code')}")
        return str(payload["tenant_access_token"])

    def _resolve_target(self, token: str) -> tuple[str, str]:
        spreadsheet_token = self.spreadsheet_token
        if not spreadsheet_token:
            response = self.session.get(
                "https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node",
                headers={"Authorization": f"Bearer {token}"},
                params={"token": self.wiki_node_token},
                timeout=self.timeout,
            )
            payload = response.json()
            node = payload.get("data", {}).get("node", {})
            if payload.get("code") != 0 or node.get("obj_type") != "sheet":
                raise RuntimeError(
                    "飞书知识库节点解析失败："
                    f"{payload.get('msg') or payload.get('code') or response.status_code}"
                )
            spreadsheet_token = str(node.get("obj_token") or "")

        sheet_id = self.sheet_id
        if not sheet_id:
            response = self.session.get(
                f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query",
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout,
            )
            payload = response.json()
            sheets = payload.get("data", {}).get("sheets", [])
            if payload.get("code") != 0 or len(sheets) != 1:
                raise RuntimeError(
                    "无法自动选择工作表："
                    f"{payload.get('msg') or '请填写 FEISHU_SHEET_ID'}"
                )
            sheet_id = str(sheets[0].get("sheet_id") or "")
            self._row_count = int(sheets[0].get("grid_properties", {}).get("row_count") or 0) or None

        return spreadsheet_token, sheet_id

    def _get_row_count(self, token: str, spreadsheet_token: str, sheet_id: str) -> int:
        if self._row_count is not None:
            return self._row_count
        response = self.session.get(
            f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query",
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout,
        )
        payload = self._require_success(response, "读取工作表行数")
        for sheet in payload.get("data", {}).get("sheets", []):
            if str(sheet.get("sheet_id")) == sheet_id:
                self._row_count = int(sheet.get("grid_properties", {}).get("row_count") or 0)
                break
        if not self._row_count or self._row_count < 2:
            raise RuntimeError("飞书工作表没有足够的可用行。")
        return self._row_count

    @staticmethod
    def _require_success(response: requests.Response, action: str) -> dict:
        payload = response.json()
        if payload.get("code") != 0:
            raise RuntimeError(f"飞书{action}失败：{payload.get('msg') or payload.get('code')}")
        return payload

    def _ensure_status_column(self, token: str, spreadsheet_token: str, sheet_id: str) -> None:
        if self._status_column_ready:
            return

        headers = {"Authorization": f"Bearer {token}"}
        row_count = self._get_row_count(token, spreadsheet_token, sheet_id)
        header_response = self.session.put(
            f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values",
            headers=headers,
            json={"valueRange": {"range": f"{sheet_id}!F1:F1", "values": [["投递状态"]]}},
            timeout=self.timeout,
        )
        self._require_success(header_response, "设置状态列标题")

        dropdown_response = self.session.post(
            f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/dataValidation",
            headers=headers,
            json={
                "range": f"{sheet_id}!F2:F{row_count}",
                "dataValidationType": "list",
                "dataValidation": {
                    "conditionValues": list(STATUS_OPTIONS),
                    "options": {
                        "multipleValues": False,
                        "highlightValidData": True,
                        "colors": ["#8F959E", "#3370FF", "#FF8800", "#7F3BF5", "#34C724"],
                    },
                },
            },
            timeout=self.timeout,
        )
        self._require_success(dropdown_response, "设置状态下拉选项")
        self._status_column_ready = True

    def _count_unsubmitted(self, token: str, spreadsheet_token: str, sheet_id: str) -> int:
        row_count = self._get_row_count(token, spreadsheet_token, sheet_id)
        response = self.session.get(
            f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{sheet_id}!F2:F{row_count}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout,
        )
        payload = self._require_success(response, "统计未投递数量")
        values = payload.get("data", {}).get("valueRange", {}).get("values", [])
        return sum(1 for row in values if row and str(row[0]).strip() == "未投递")

    def save(self, summary: RecruitmentSummary) -> FeishuSaveResult:
        token = self._tenant_access_token()
        spreadsheet_token, sheet_id = self._resolve_target(token)
        self._ensure_status_column(token, spreadsheet_token, sheet_id)
        url = (
            "https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/"
            f"{spreadsheet_token}/values_append"
        )
        response = self.session.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "valueRange": {
                    "range": f"{sheet_id}!A:F",
                    "values": [[
                        summary.company,
                        summary.category,
                        summary.deadline,
                        summary.apply_url,
                        "\n".join(summary.jobs) or "未知",
                        "未投递",
                    ]],
                }
            },
            timeout=self.timeout,
        )
        payload = self._require_success(response, "写入")
        return FeishuSaveResult(
            updated_range=str(payload.get("data", {}).get("updates", {}).get("updatedRange", "")),
            unsubmitted_count=self._count_unsubmitted(token, spreadsheet_token, sheet_id),
        )
