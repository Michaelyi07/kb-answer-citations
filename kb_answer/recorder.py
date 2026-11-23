"""File-backed S5-GW interface stub.

The real model gateway (S5-GW) is out of scope for S3-KB-020; per the unified
technical agreement this module is the agreed interface stub: every answer is
recorded as one JSONL line carrying the prompt version and model identity, so
swapping in the real gateway later requires no prompt or schema change.
Connection points: README.md section "S5-GW integration".
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kb_answer import PROMPT_ID, PROMPT_VERSION

RECORD_FIELDS = (
    "prompt_id",
    "prompt_version",
    "model_name",
    "model_version",
    "response_digest",
    "recorded_at",
    "response",
)


def response_digest(response: dict[str, Any]) -> str:
    """Stable sha256 over the canonical JSON of an answer object."""
    canonical = json.dumps(response, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def make_record(
    response: dict[str, Any],
    model_name: str,
    model_version: str,
    *,
    prompt_id: str = PROMPT_ID,
    prompt_version: int = PROMPT_VERSION,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Build one answer record. recorded_at defaults to current UTC time (ISO-8601)."""
    if not model_name:
        raise ValueError("model_name must be non-empty")
    return {
        "prompt_id": prompt_id,
        "prompt_version": prompt_version,
        "model_name": model_name,
        "model_version": model_version,
        "response_digest": response_digest(response),
        "recorded_at": recorded_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "response": response,
    }


def write_records(records: list[dict[str, Any]], path: str | Path) -> Path:
    """Append records to a JSONL file (one compact JSON object per line)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        for rec in records:
            missing = [k for k in RECORD_FIELDS if k not in rec]
            if missing:
                raise ValueError(f"record missing fields: {missing}")
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    return p


def load_records(path: str | Path) -> list[dict[str, Any]]:
    """Read back all records from a JSONL file, in write order."""
    out: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
