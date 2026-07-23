import pytest
import requests

from recruit_bot.wechat_article import WeChatArticleReader


@pytest.mark.parametrize(
    "url",
    [
        "http://mp.weixin.qq.com/s/example",
        "https://example.com/s/example",
        "https://mp.weixin.qq.com.evil.example/s/example",
    ],
)
def test_rejects_non_wechat_urls(url):
    with pytest.raises(ValueError):
        WeChatArticleReader.validate_url(url)


def test_accepts_wechat_article_url():
    url = "https://mp.weixin.qq.com/s/example?scene=1"
    assert WeChatArticleReader.validate_url(url) == url


def test_retries_transient_connection_error(monkeypatch):
    reader = WeChatArticleReader()
    expected = requests.Response()
    expected.status_code = 200
    attempts = iter([requests.exceptions.SSLError("temporary EOF"), expected])

    def fake_get(*args, **kwargs):
        result = next(attempts)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(reader.session, "get", fake_get)
    monkeypatch.setattr("recruit_bot.wechat_article.time.sleep", lambda _: None)

    assert reader._get_with_retry("https://mp.weixin.qq.com/s/example") is expected
