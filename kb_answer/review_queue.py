"""AI review queue registration stub (L0 level).

Answers are registered at level L0 -- internal staff reference only, never sent
to members directly. The queue stub appends one registration payload per answer
to a JSONL file; the real AI review queue (S5) plugs in at this boundary (see
README "AI review queue integration").
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LEVEL = "L0"


class L0ReviewQueue:
    """Registration-only stub. There is deliberately NO outward-send path:
    the queue accepts registrations and reads them back, nothing else."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def register(self, record: dict[str, Any], **context: Any) -> dict[str, Any]:
        payload = {
            "level": LEVEL,
            "internal_only": True,
            "audience": "staff_only",
            "dispatch": "internal_review",
            "question": context.get("question"),
            "evidence_set_id": context.get("evidence_set_id"),
            "item": record,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        return payload

    def load(self) -> list[dict[str, Any]]:
        out = []
        if not self.path.exists():
            return out
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out
