# NodeSeek-Signin

NodeSeek论坛签到，借助github action或青龙面板 自动触发。支持随机签到和固定签到模式。

## Action

需要自行在setting中添加 Repository secrets

如果显示"USER NOT FOUND"或显示实际响应内容显示html就是cookie失效了需要重新抓

| 名称 | 含义 |
| --- | --- |
| NS_COOKIE | 论坛用户cookie，自行在浏览器F12中查看 |
| NS_RANDOM | 是否启用随机签到，true为随机签到，false为固定签到，默认为true |
| TG_BOT_TOKEN | tg 机器人的 TG_BOT_TOKEN，例：1407203283:AAG9rt-6RDaaX0HBLZQq0laNOh898iFYaRQ，非必需 |
| TG_USER_ID | tg 机器人的 TG_USER_ID，例：1434078534，非必需 |
| TG_THREAD_ID | tg 机器人的 TG_THREAD_ID 超级群组话题id，非必需 |
| PROXY | 代理服务器地址，格式如：http://username:password@127.0.0.1:7890 或 http://127.0.0.1:7890，非必需 |
| USE_PROXY | 是否使用代理，true或false，默认为false，非必需 |
| CLIENTT_KEY | 验证码服务的客户端密钥，非必需。注册链接：[YesCaptcha](https://yescaptcha.com/i/k2Hy3Q)。注册联系客服送余额大概可以使用60次登录 |
| USER | 论坛用户名，非必需 |
| PASS | 论坛密码，非必需 |

## 青龙面板

```bash
ql raw https://raw.githubusercontent.com/Banezzz/NodeSeek-Signin/main/nodeseek_sign.py
```

## 功能特点

- ✅ 支持随机/固定签到模式
  - 通过环境变量 `NS_RANDOM` 控制
  - `true`: 随机签到（默认）
  - `false`: 固定签到
- ✅ 自动处理验证码
- ✅ Cookie失效自动重新登录
- ✅ 支持代理设置
- ✅ Telegram 通知
- ✅ 详细的运行状态和环境信息
- ✅ 完善的错误处理机制

## 通知示例

```
=== NodeSeek 签到通知 ===
时间：2024-03-13 10:30:45
状态：✅ 签到成功
详情：签到成功！获得7个鸡腿，当前共有1054个鸡腿
请求耗时：0.82秒
随机签到：已开启
代理状态：未使用

运行环境：
- Python版本：3.9.7
- 操作系统：darwin
- 启用代理：否
- 随机签到：是
==================
```
