from datetime import datetime, timezone
import json
import time
from pathlib import Path


class Recorder:
    def __init__(self, path: Path | None = None):
        self.path = path
        self.events: list[dict] = []
        self.started_ns = time.monotonic_ns()

    def emit(self, event: str, **fields) -> dict:
        row = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
               "elapsed_us": (time.monotonic_ns() - self.started_ns) // 1000,
               "event": event, **fields}
        self.events.append(row)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row
