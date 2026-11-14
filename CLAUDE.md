# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

BG is a Chinese-language home agent: a terminal REPL backed by a LangGraph tool-calling loop, with Home Assistant exposed to it over MCP.

## Commands

```sh
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt   # setup
.venv/bin/python main.py                                                # run the REPL
```

`.env` must define `ANTHROPIC_API_KEY`, `HA_URL` and `HA_TOKEN`. There are no tests, linter or build step.

Inside the REPL, `/thread <id>` switches conversation (default is `1`) and `exit` quits.

## Architecture

- `main.py` builds a two-node `StateGraph(MessagesState)`: `agent_node` calls Claude, and routes to `tools_node` while the last message has tool calls, looping back until it has none. `graph.png` is this graph and is regenerated on every startup.
- `ha.py` holds the single module-level `MultiServerMCPClient` (server name `"ha"`, `{HA_URL}/api/mcp`). Both `tools.py` and `prompt.py` go through it, so all Home Assistant access comes from this one client.
- `tools.py` returns the tools the model sees, which are currently only those discovered from Home Assistant at startup. To add a local tool, include it in the list returned by `get_tools()`.
- `prompt.py` builds the system prompt by appending Home Assistant's `"Device control"` MCP prompt to `SYSTEM_PROMPT`. The result is computed once at startup and prepended on each model call in `agent_node`, so it is never stored in the checkpointed messages.
- Conversation state persists across runs in `data/bg.db` through `AsyncSqliteSaver`, keyed by `thread_id`. Logs go to `data/bg.log`. `data/` is gitignored.

## Failure behavior

- Missing `HA_URL` or `HA_TOKEN` crashes at import, because `ha.py` reads `os.environ` directly.
- An unreachable Home Assistant does not stop startup. `get_tools()` returns an empty list and `get_ha_prompt()` falls back to a placeholder string, so the agent runs with no tools. Check the startup output or `data/bg.log` when it seems unable to control devices.
- Tool execution errors are caught by `on_tool_error` and returned to the model as tool messages, so they do not end the turn.
- `draw_mermaid_png()` in `main()` uses LangGraph's default renderer, which calls an external service. A failure there aborts startup.

## Conventions

- User-facing output, log messages and the system prompt are in Chinese, with technical terms and proper nouns left in English as `SYSTEM_PROMPT` specifies.
- Startup and error events are reported twice, with `print` for the terminal and `logger` for the file. New startup steps follow the same pattern.
