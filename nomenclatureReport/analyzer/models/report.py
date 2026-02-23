from __future__ import annotations

from dataclasses import dataclass

from nomenclatureReport.analyzer.models.issue import Issue


@dataclass(frozen=True)
class Report:
    issues: list[Issue]
    missing_rule_ids: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary(),
            "issues": [issue.to_dict() for issue in self.issues],
            "missing_rule_ids": self.missing_rule_ids,
        }

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for issue in self.issues:
            counts[issue.severity] = counts.get(issue.severity, 0) + 1
        return counts

    def to_text(self) -> str:
        lines = ["Nomenclature Report"]
        summary = self.summary()
        if summary:
            summary_items = ", ".join(
                f"{severity}: {count}" for severity, count in sorted(summary.items())
            )
            lines.append(f"Summary: {summary_items}")
        else:
            lines.append("Summary: no issues found")
        if self.missing_rule_ids:
            lines.append(f"Missing rule implementations: {', '.join(self.missing_rule_ids)}")

        for issue in self.issues:
            lines.append(
                f"[{issue.severity}] {issue.rule_id} {issue.component_name} "
                f"({issue.component_type}) - {issue.message} "
                f"[{issue.component_path}]",
            )
        return "\n".join(lines)
