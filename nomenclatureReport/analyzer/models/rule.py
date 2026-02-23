from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Rule:
    rule_id: str
    component_type: str
    rule: str
    severity: str
    pending_review: bool
    description: str
    example: str
    applies_when: dict[str, Any] | None = None
