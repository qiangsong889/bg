from pathlib import Path

MODEL_NAME = "claude-haiku-5-5"
MODEL_TIMEOUT = 10
HA_PROMPT_NAME = 'Device control'
HA_CONN_TIMEOUT = 5

DB_PATH = Path(__file__).resolve().parent / "data" / "bg.db"
LOG_PATH = Path(__file__).resolve().parent / "data" / "bg.log"

SNAPSHOTS_DIR = (
    Path(__file__).resolve().parent
    / "data" / "snapshots"
)

EVALS_DIR = (
    Path(__file__).resolve().parent
    / "evals"
)

EVAL_RUNS_DIR = (
    Path(__file__).resolve().parent
    / "data" / "eval_runs"
)


