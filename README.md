# 微信招聘整理机器人

在微信中向专用机器人发送招聘文字或微信公众号文章链接，机器人会整理公司、招聘类型、岗位、地点、投递方式、截止时间和摘要。

> 微信接入使用第三方 `wechatbot-sdk`。它不是微信官方承诺稳定性的公共接口，请使用非重要账号、小范围测试，不要高频或批量发送。

## 1. 准备

原代码中的 DashScope Key 已暴露，请先在阿里云控制台删除它并创建新 Key。

```bash
cd "/Users/chenruizhao/Documents/微信机器人"
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

如果目前只需要接收消息，`.env` 中的 `DASHSCOPE_API_KEY` 可以留空；需要自动整理招聘信息时再填写。

## 2. 先测试招聘识别

```bash
python -m recruit_bot.main --text "某公司招聘产品经理，工作地点上海，7月30日截止"
python -m recruit_bot.main --url "https://mp.weixin.qq.com/s/..."
```

## 3. 启动微信机器人

```bash
python -m recruit_bot.main --bot
```

首次运行会显示二维码。扫码后向机器人发送招聘文字或公众号链接。凭证保存在项目的 `.data/` 中，不会进入 Git。

机器人会把每条文字或公众号链接追加保存到 `.data/inbox.jsonl`，并回复一个 8 位接收编号。配置了 `DASHSCOPE_API_KEY` 时，还会继续提取并回复招聘信息；未配置时仅负责可靠接收。

首次收到消息时，终端会打印发送者 ID。把自己的 ID 写入 `.env`：

```text
ALLOWED_USER_IDS=你的发送者ID
```

重启后机器人只响应允许列表中的用户。多个 ID 用英文逗号分隔。

## 4. 自动保存到飞书电子表格（可选）

1. 新建飞书电子表格，在第一行依次填写：`公司`、`类别`、`截止时间`、`投递地址`、`岗位`。
2. 在飞书开放平台创建企业自建应用，开通电子表格读写权限，并让该应用能够访问目标电子表格。
3. 从电子表格网址中取得 `spreadsheet_token`（`/sheets/` 后面的部分）和 `sheet_id`（网址中的 `sheet` 参数）。
4. 把配置写入本机 `.env`，不要把 App Secret 发给他人：

```text
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_SPREADSHEET_TOKEN=
FEISHU_SHEET_ID=
```

四项均填写后重启机器人。启动日志出现“飞书同步已启用”即表示配置已加载；每次招聘整理成功后，机器人会在电子表格末尾追加一行。

## 安全限制

- 链接只接受 `https://mp.weixin.qq.com` 公众号文章。
- 单篇文章最多处理 8 张正文图片，可在 `.env` 调整。
- 密钥、微信凭证和下载文件均被 Git 忽略。
- 不支持批量群发、自动加好友或其他高风险操作。
