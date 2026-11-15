from pathlib import Path

MODEL_NAME = "claude-haiku-5-5"
MODEL_TIMEOUT = 10
HA_PROMPT_NAME = 'Device control'

DB_PATH = Path(__file__).resolve().parent / "data" / "bg.db"
LOG_PATH = Path(__file__).resolve().parent / "data" / "bg.log"
SNAPSHOT_DIR = (
    Path(__file__).resolve().parent.parent
    / "data" / "snapshots"
)

EVALS_DIR = (
    Path(__file__).resolve().parent
)

EVAL_RUNS_DIR = (
    Path(__file__).resolve().parent.parent
    / "data" / "eval_runs"
)

SNAPSHOTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data" / "snapshots"
)

