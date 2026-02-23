from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Issue:
    rule_id: str
    severity: str
    message: str
    component_name: str
    component_path: Path
    component_type: str
    pending_review: bool

    def to_dict(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "component_name": self.component_name,
            "component_path": str(self.component_path),
            "component_type": self.component_type,
            "pending_review": self.pending_review,
        }
