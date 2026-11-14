import logging
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / "data" / "bg.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("bg")
logger.setLevel(logging.INFO)

handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s"))
logger.addHandler(handler)
