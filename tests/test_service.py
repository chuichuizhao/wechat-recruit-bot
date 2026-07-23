from recruit_bot.service import RecruitmentService
from recruit_bot.wechat_article import Article


class FakeAnalyzer:
    def __init__(self):
        self.text = None
        self.article = None

    def analyze_text(self, text):
        self.text = text
        return "text-result"

    def analyze_article(self, text, images, source_url):
        self.article = (text, images, source_url)
        return "article-result"


class FakeReader:
    def read(self, url):
        return Article("招聘标题", "招聘正文", (), url)

    def download_image(self, url):
        raise AssertionError("文章没有图片，不应下载")


def test_plain_text_uses_text_pipeline():
    analyzer = FakeAnalyzer()
    service = RecruitmentService(FakeReader(), analyzer)

    result = service.process("快手实习生招聘，简历投递：hr@example.com")

    assert result == "text-result"
    assert analyzer.text == "快手实习生招聘，简历投递：hr@example.com"
    assert analyzer.article is None


def test_wechat_url_uses_article_pipeline():
    analyzer = FakeAnalyzer()
    service = RecruitmentService(FakeReader(), analyzer)
    url = "https://mp.weixin.qq.com/s/example"

    result = service.process(url)

    assert result == "article-result"
    assert analyzer.text is None
    assert analyzer.article == ("标题：招聘标题\n招聘正文", [], url)
