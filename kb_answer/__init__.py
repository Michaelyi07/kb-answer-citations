"""kb_answer — citation-grounded answer generation for the member-space knowledge base.

Components:
- schema.py    JSON Schema (Draft 2020-12) for model output + validation helper
- renderer.py  render an answer dict to Markdown with [n] citation marks
- recorder.py  file-backed S5-GW interface stub recording prompt/model metadata per answer
"""

PROMPT_ID = "kb_answer/v1"
PROMPT_VERSION = 1

__all__ = ["PROMPT_ID", "PROMPT_VERSION"]
