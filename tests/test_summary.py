from recruit_bot.qwen import RecruitmentSummary


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
