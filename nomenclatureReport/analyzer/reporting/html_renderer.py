from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from nomenclatureReport.analyzer.models.component import Component
from nomenclatureReport.analyzer.models.issue import Issue
from nomenclatureReport.analyzer.models.report import Report
from nomenclatureReport.analyzer.utils.fs import read_json


@dataclass(frozen=True)
class HtmlIssueView:
    rule_id: str
    severity: str
    message: str
    component_name: str
    component_path: str
    component_type: str
    pending_review: bool
    severity_class: str
    severity_badge: str


class HtmlReportRenderer:
    def __init__(self, template_dir: Path) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render(
        self,
        report: Report,
        project_path: Path,
        rules_path: Path,
        components: list[Component],
    ) -> str:
        template = self._env.get_template("report.html.j2")
        context = build_context(
            report=report,
            project_path=project_path,
            rules_path=rules_path,
            components=components,
        )
        return template.render(**context)


def build_context(
    report: Report,
    project_path: Path,
    rules_path: Path,
    components: list[Component],
) -> dict[str, object]:
    issues_view = [build_issue_view(issue) for issue in report.issues]
    severity_counts = Counter(issue.severity for issue in report.issues)
    pending_review_count = sum(1 for issue in report.issues if issue.pending_review)
    total_issues = len(report.issues)
    total_components_analyzed = len(components)

    component_counts = Counter()
    for component in components:
        for component_type in component.component_types:
            component_counts[component_type] += 1

    issue_rule_counts = Counter(issue.rule_id for issue in report.issues)
    top_rules = issue_rule_counts.most_common(6)
    severity_data = [
        {
            "label": "Errors",
            "value": severity_counts.get("ERROR", 0),
            "color": "#f78154",
        },
        {
            "label": "Warnings",
            "value": severity_counts.get("WARNING", 0),
            "color": "#805100",
        },
        {
            "label": "Info",
            "value": max(total_issues - severity_counts.get("ERROR", 0) - severity_counts.get("WARNING", 0), 0),
            "color": "#141613",
        },
    ]

    component_data = [
        {"label": name, "value": count}
        for name, count in component_counts.most_common(8)
    ]
    rule_catalog = load_rule_catalog(rules_path)
    top_rules_data = [
        {
            "label": rule_id,
            "value": count,
            "title": rule_catalog.get(rule_id, {}).get("rule", rule_id),
            "description": rule_catalog.get(rule_id, {}).get("description", ""),
        }
        for rule_id, count in top_rules
    ]
    rule_stats = build_rule_stats(rule_catalog, issue_rule_counts)

    return {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "project_path": str(project_path),
        "rules_path": str(rules_path),
        "issues": issues_view,
        "total_issues": total_issues,
        "total_components_analyzed": total_components_analyzed,
        "error_count": severity_counts.get("ERROR", 0),
        "warning_count": severity_counts.get("WARNING", 0),
        "pending_review_count": pending_review_count,
        "component_counts": component_counts,
        "top_rules": top_rules,
        "severity_data": severity_data,
        "component_data": component_data,
        "top_rules_data": top_rules_data,
        "rule_stats": rule_stats,
        "rule_catalog": rule_catalog,
        "missing_rule_ids": report.missing_rule_ids,
    }


def load_rule_catalog(rules_path: Path) -> dict[str, dict[str, str]]:
    catalog: dict[str, dict[str, str]] = {}
    try:
        raw_rules = read_json(rules_path)
    except OSError:
        return catalog
    for raw in raw_rules:
        rule_id = raw.get("ruleId")
        if not rule_id:
            continue
        catalog[rule_id] = {
            "rule": str(raw.get("rule", "")),
            "description": str(raw.get("description", "")),
            "severity": str(raw.get("severity", "")),
        }
    return catalog


def build_rule_stats(
    rule_catalog: dict[str, dict[str, str]],
    issue_rule_counts: Counter[str],
) -> list[dict[str, object]]:
    stats: list[dict[str, object]] = []
    for rule_id in sorted(rule_catalog.keys()):
        rule_data = rule_catalog[rule_id]
        count = int(issue_rule_counts.get(rule_id, 0))
        stats.append(
            {
                "rule_id": rule_id,
                "title": rule_data.get("rule", rule_id),
                "description": rule_data.get("description", ""),
                "severity": rule_data.get("severity", ""),
                "count": count,
                "triggered": count > 0,
            }
        )
    return stats


def build_issue_view(issue: Issue) -> HtmlIssueView:
    severity_class = {
        "ERROR": "text-red-700 bg-red-50 ring-red-600/20",
        "WARNING": "text-amber-700 bg-amber-50 ring-amber-600/20",
    }.get(issue.severity, "text-slate-700 bg-slate-50 ring-slate-600/20")

    severity_badge = {
        "ERROR": "bg-red-600 text-white",
        "WARNING": "bg-amber-500 text-white",
    }.get(issue.severity, "bg-slate-500 text-white")

    return HtmlIssueView(
        rule_id=issue.rule_id,
        severity=issue.severity,
        message=issue.message,
        component_name=issue.component_name,
        component_path=str(issue.component_path),
        component_type=issue.component_type,
        pending_review=issue.pending_review,
        severity_class=severity_class,
        severity_badge=severity_badge,
    )
