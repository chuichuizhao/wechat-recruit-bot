from recruit_bot.feishu import FeishuSpreadsheetStore
from recruit_bot.qwen import RecruitmentSummary


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_appends_summary_to_spreadsheet(monkeypatch):
    store = FeishuSpreadsheetStore("app-id", "secret", "spreadsheet-token", "sheet-id")
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        if "tenant_access_token" in url:
            return FakeResponse({"code": 0, "tenant_access_token": "token"})
        if "dataValidation" in url:
            return FakeResponse({"code": 0, "msg": "success"})
        return FakeResponse({"code": 0, "data": {"updates": {"updatedRange": "sheet-id!A2:F2"}}})

    monkeypatch.setattr(store.session, "post", fake_post)
    monkeypatch.setattr(store.session, "put", lambda *args, **kwargs: FakeResponse({"code": 0}))
    def fake_get(url, **kwargs):
        if "sheets/query" in url:
            return FakeResponse(
                {"code": 0, "data": {"sheets": [{"sheet_id": "sheet-id", "grid_properties": {"row_count": 200}}]}}
            )
        return FakeResponse(
            {"code": 0, "data": {"valueRange": {"values": [["未投递"], ["已投递"], ["未投递"]]}}}
        )

    monkeypatch.setattr(store.session, "get", fake_get)
    summary = RecruitmentSummary.from_dict(
        {
            "公司": "快手",
            "类别": "实习生招聘",
            "岗位": ["策略产品实习生"],
            "投递网址": "hr@example.com",
            "截止时间": "未知",
        }
    )

    result = store.save(summary)
    assert result.updated_range == "sheet-id!A2:F2"
    assert result.unsubmitted_count == 2
    values = calls[2][1]["json"]["valueRange"]["values"]
    assert values == [["快手", "实习生招聘", "未知", "hr@example.com", "策略产品实习生", "未投递"]]


def test_resolves_wiki_sheet_and_only_worksheet(monkeypatch):
    store = FeishuSpreadsheetStore("app-id", "secret", wiki_node_token="wiki-token")
    responses = iter(
        [
            FakeResponse({"code": 0, "data": {"node": {"obj_type": "sheet", "obj_token": "sht-1"}}}),
            FakeResponse({"code": 0, "data": {"sheets": [{"sheet_id": "sheet-1"}]}}),
        ]
    )
    monkeypatch.setattr(store.session, "get", lambda *args, **kwargs: next(responses))

    assert store._resolve_target("tenant-token") == ("sht-1", "sheet-1")
