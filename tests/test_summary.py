from recruit_bot.qwen import RecruitmentSummary, normalize_apply_contact
from recruit_bot.bot import format_feishu_success


def test_formats_summary_for_wechat():
    summary = RecruitmentSummary.from_dict(
        {
            "公司": "示例公司",
            "类别": "校园招聘",
            "岗位": ["科技类-AI工程师", "产品类-产品经理"],
            "地点": ["上海"],
            "投递网址": "https://example.com/jobs",
            "截止时间": "7月30日",
            "摘要": "面向应届毕业生招聘。",
            "信息缺失": [],
        }
    )
    output = summary.format_for_wechat()
    assert "示例公司" in output
    assert "科技类-AI工程师" in output
    assert "7月30日" in output
    assert "地点：" not in output
    assert "摘要：" not in output
    assert "缺失信息：" not in output
    assert "公司：示例公司\n\n类别：校园招聘\n\n截止时间：7月30日\n\n投递地址：" in output


def test_formats_single_job_feishu_confirmation():
    output = format_feishu_success("快手", "实习生招聘", ("策略产品实习生",), 3)
    assert output == "快手-策略产品实习生\n\n已保存到飞书表格\n\n还有 3 个未投递"


def test_formats_multiple_jobs_feishu_confirmation():
    output = format_feishu_success("快手", "实习生招聘", ("产品实习生", "运营实习生"), 8)
    assert output == "快手-实习生招聘\n\n已保存到飞书表格\n\n还有 8 个未投递"


def test_normalizes_list_apply_url_and_ignores_wechat_source():
    assert normalize_apply_contact(["https://job.icbc.com.cn", "中国工商银行人才招聘微信公众号"]) == (
        "https://job.icbc.com.cn"
    )
    assert normalize_apply_contact(["https://mp.weixin.qq.com/s/example"]) == "未知"


def test_normalizes_email_apply_contact():
    assert normalize_apply_contact(["简历投递：hr@example.com"]) == "hr@example.com"


def test_normalizes_rich_text_object_and_literal_string():
    assert normalize_apply_contact({"text": "https://jobs.example.com", "type": "text"}) == (
        "https://jobs.example.com"
    )
    assert normalize_apply_contact("{'text': '[', 'type': 'text'}") == "未知"
    assert normalize_apply_contact("['https://jobs.example.com', '招聘公众号']") == "https://jobs.example.com"
