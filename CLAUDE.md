# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

BG is a Chinese-language home agent: a terminal REPL backed by a LangGraph tool-calling loop, with Home Assistant exposed to it over MCP.

This is also the owner's LangGraph learning project. For the Python agent code, the owner writes the code: explain designs and APIs and review their changes, but do not edit project files unless they explicitly ask.

## Commands

Dependencies are managed with uv (`pyproject.toml`, `uv.lock`, Python pinned to 3.11 in `.python-version`). Run everything from this directory; activating `.venv` is not needed.

```sh
uv sync                          # create/refresh .venv from uv.lock
cp .env.example .env             # then fill in ANTHROPIC_API_KEY, HA_URL, HA_TOKEN
uv run main.py                   # run the REPL
uv run pytest                    # unit tests (no network, no .env needed)
uv run -m evals.snapshot         # re-snapshot Home Assistant tools + prompt (needs HA)
uv run -m evals.run_eval         # run the eval (calls the Claude API, costs money)
uv add <pkg> / uv add --dev <pkg>
```

Inside the REPL, `/thread <id>` switches conversation (default is `1`) and `exit` quits.

Do not run the full eval without asking the owner first; prefer running only the affected cases.

## Architecture

- `main.py` builds a two-node `StateGraph(MessagesState)` in `build_app(tools, prompts, model, checkpointer)`: `agent_node` calls the model, and `route` sends it to `tools_node` while the last message has tool calls, looping back until it has none. `build_app` takes the model and tools as parameters so the eval can reuse the same graph with fake tools.
- `ha.py` exposes `create_ha_client()`, which builds a `MultiServerMCPClient` (server name `"ha"`, `{HA_URL}/api/mcp`) from the environment when called. The client only stores config; each MCP call opens its own session, so creating one per call is cheap.
- `tools.py` returns the tools the model sees, which are currently only those discovered from Home Assistant at startup. To add a local tool, include it in the list returned by `get_tools()`.
- `prompt.py` builds the system prompt by appending Home Assistant's `"Device control"` MCP prompt to `SYSTEM_PROMPT`. It is computed once at startup and prepended on each model call in `agent_node`, so it is never stored in the checkpointed messages.
- `config.py` holds constants: model name and timeout, HA prompt name and timeout, and all paths under `data/` and `evals/`.
- `logger.py` provides `register_agent_logger()`, which attaches the `data/bg.log` file handler to the `"bg"` logger.
- Conversation state persists across runs in `data/bg.db` through `AsyncSqliteSaver`, keyed by `thread_id`.

## Evals

- `evals/snapshot.py` saves Home Assistant's tool definitions and prompt to `data/snapshots/ha.json`. Re-run it when HA devices, tools or version change.
- `evals/run_eval.py` rebuilds those tools as `StructuredTool`s whose coroutine is a fake (per-tool return values in `FAKE_FUNC_RETURN_VALUE`, default `"operation success"`), so evals never touch real devices. It runs every input in `evals/cases.json` through `build_app` and writes results to `data/eval_runs/<start time>.json`.
- A case passes when all `expected_tools` were called (extra calls are allowed), no tool was called when `expected_tools` is empty, and no `ToolMessage` has `status == "error"`. Tool arguments are not checked yet.
- Check `final_reply` in the results as well as the score: a broken fake once scored 8/8 while every reply was an apology.

## Failure behavior

- A missing `ANTHROPIC_API_KEY` is not checked at startup. The first turn fails with "Connection error." (an empty `Bearer` header is rejected locally), which `main.py` reports as a connection problem.
- Missing `HA_URL`/`HA_TOKEN`, or a Home Assistant that does not answer within `HA_CONN_TIMEOUT`, does not stop startup: `get_tools()` returns an empty list and `get_prompts()` uses a placeholder, so BG runs without device control. It only reconnects on restart.
- Each REPL turn has its own try/except. Connection errors, 429 and 5xx print a message and the REPL continues; 401 exits; other 4xx print a "check config" message and continue. The Anthropic SDK already retries twice before an error reaches this code.
- A failed turn leaves its `HumanMessage` checkpointed (it is written before `agent_node` runs), so the next turn's model call sees both messages. This is a known, accepted behavior for now.
- Tool execution errors are caught by `on_tool_error` and returned to the model as tool messages. An MCP result marked `isError` is turned into `ToolMessage(status="error")` by the adapter itself, without going through `on_tool_error`. Whether Home Assistant uses `isError` or only the message content to report failures has not been verified yet.

## Conventions

- User-facing output, log messages and the system prompt are in Chinese, with technical terms and proper nouns left in English as `SYSTEM_PROMPT` specifies.
- Startup and error events are reported twice, with `print` for the terminal and `logger` for the file.
- Modules get the logger with `logging.getLogger("bg")` at the top and never attach handlers. Only entry points (`if __name__ == "__main__":`) call `load_dotenv()` and `register_agent_logger()`. `run_eval` does not register the file handler, so evals do not write to `bg.log`.
- Keep imports free of side effects: no reading `os.environ` or connecting to services at import time. (`main.py` still creates `data/` at import, and `run_eval.py` creates its output directories.)
- Constants go in `config.py`; secrets and per-machine values go in `.env`, with names listed in `.env.example`.

## Privacy

- `data/` (database, logs, snapshots, eval results) and `.env` are private and gitignored. Never print `HA_TOKEN`.
- Unfiltered `GetLiveContext` output includes the home's location. Do not copy it into committed files.
- When probing Home Assistant, only call read-only tools (`GetLiveContext`, `GetDateTime`). Never call device-control tools in tests or evals.

## Other directories

- `dashboard/` is a separate React + Vite prototype (BG Studio) driven by simulated events. It is not connected to the Python agent. See its own README.
- `viz/` is a local, gitignored 3D visualization prototype.
