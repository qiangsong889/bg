# BG

BG 是一个中文的家居 agent。现在是一个终端 REPL：你用文字说话，BG 用 LangGraph 的工具调用循环决定要不要调用 Home Assistant 的工具，然后用中文回复。

- 大脑：Claude（模型名在 `config.py`），通过 `langchain-anthropic` 调用。
- 工具：Home Assistant 自带的 MCP server，启动时自动发现所有工具，并把 HA 的 "Device control" prompt 拼进 system prompt。
- 记忆：对话按 `thread_id` 存在本地 SQLite（`data/bg.db`），重启后还在。

## 安装

需要先装 [uv](https://docs.astral.sh/uv/)（macOS：`brew install uv`）。Python 3.11 和所有依赖由 uv 按 `uv.lock` 安装，不需要手动装 Python。

```sh
uv sync
cp .env.example .env
```

然后在 `.env` 里填上：

| 变量 | 说明 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `HA_URL` | Home Assistant 地址，例如 `http://homeassistant.local:8123` |
| `HA_TOKEN` | Home Assistant 的长期访问令牌 |

## 使用

```sh
uv run main.py
```

- 直接输入中文或英文，例如"打开餐厅灯"、"现在几点"。
- `/thread <id>`：切换到另一个对话（默认是 `1`）。
- `exit`：退出。

Home Assistant 连不上时，BG 仍会启动，但不能控制设备，需要重启才会重新连接。日志写在 `data/bg.log`。

## 测试和 eval

```sh
uv run pytest                  # 单元测试，不联网，不需要 .env
uv run -m evals.snapshot       # 给 Home Assistant 的工具和 prompt 拍快照（需要连上 HA）
uv run -m evals.run_eval       # 跑 eval（会调用 Claude API，产生费用）
```

- **test** 测确定性的代码逻辑，免费，每次改动都可以跑。
- **eval** 测模型的行为：给一句话，看 BG 有没有调用正确的工具。它用快照里的工具定义和假的执行函数，**不会控制真实设备**。用例在 `evals/cases.json`，结果保存在 `data/eval_runs/`。
- HA 的设备、工具或版本变了以后，要重新拍快照。
- 看 eval 结果时不要只看分数，也要看每条的 `final_reply`。

## 项目结构

```
main.py          REPL 入口；build_app() 构建 LangGraph 图
tools.py         收集模型可用的工具（目前只有 HA）
prompt.py        system prompt + HA 的 MCP prompt
ha.py            create_ha_client()：按需创建 HA 的 MCP client
config.py        常量：模型名、超时、路径
logger.py        register_agent_logger()：由入口调用，日志写到 data/bg.log
evals/           快照、eval 用例和运行脚本
tests/           pytest 单元测试
data/            本地私有数据（数据库、日志、快照、eval 结果），不进 git
dashboard/       BG Studio 前端原型（模拟数据，尚未接入 agent），见其 README
```

## 配置约定

- 秘密和每台机器不同的值放 `.env`，变量名列在 `.env.example`。
- 其他常量放 `config.py`。
- 依赖用 `uv add <包名>`（开发工具用 `uv add --dev`）添加，不要用 pip。

## 隐私

`.env` 和 `data/` 都不进 git。`data/` 里的日志、快照和对话记录包含家里的设备信息，不要分享或提交。

## 路线图

接下来按顺序：

1. 防护和执行后确认：判断设备操作是否真的成功，失败时不说"已完成"。
2. 高风险操作先确认再执行（LangGraph interrupt）。
3. 接入邮件、日历等个人服务。
4. 长期记忆、定时任务、HTTP 接口和语音。
5. tracing（自部署 Langfuse）和本地模型，计划在新机器上做。
