import pytest

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
