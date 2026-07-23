import json
from datetime import datetime, timezone

from recruit_bot.inbox import InboxItem, JsonlInbox


def test_classifies_wechat_article_and_keeps_surrounding_text():
    item = InboxItem.from_message(
        "user-1",
        "帮我看看 https://mp.weixin.qq.com/s/example。谢谢",
        datetime(2026, 7, 22, tzinfo=timezone.utc),
    )

    assert item.kind == "wechat_article"
    assert item.urls == ("https://mp.weixin.qq.com/s/example",)
    assert item.text.startswith("帮我看看")


def test_plain_text_is_saved_as_utf8_jsonl(tmp_path):
    item = InboxItem.from_message("user-2", "这是一条文字消息")
    inbox_path = tmp_path / "inbox.jsonl"

    JsonlInbox(inbox_path).save(item)

    saved = json.loads(inbox_path.read_text(encoding="utf-8"))
    assert saved["sender_id"] == "user-2"
    assert saved["kind"] == "text"
    assert saved["text"] == "这是一条文字消息"
