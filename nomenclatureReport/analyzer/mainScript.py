from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from nomenclatureReport.analyzer.engine.component_loader import load_components
from nomenclatureReport.analyzer.engine.rule_engine import RuleEngine
from nomenclatureReport.analyzer.models.component import Component
from nomenclatureReport.analyzer.models.report import Report
from nomenclatureReport.analyzer.reporting.html_renderer import HtmlReportRenderer
from nomenclatureReport.analyzer.rules.registry import RULE_REGISTRY
from nomenclatureReport.analyzer.utils.fs import resolve_path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze Salesforce project nomenclature using rules.json.",
    )
    parser.add_argument(
        "--project-path",
        required=True,
        help="Root path of the Salesforce DX project to analyze.",
    )
    parser.add_argument(
        "--rules",
        default=str(
            Path(__file__).resolve().parents[1] / "rules.json",
        ),
        help="Path to nomenclature rules.json.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional output file path for the report (JSON).",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text", "html"),
        default="json",
        help="Output format to print to stdout.",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    project_path = resolve_path(args.project_path)
    rules_path = resolve_path(args.rules)

    components, standard_value_sets = load_components(project_path)

    engine = RuleEngine(
        rules_path=rules_path,
        rule_registry=RULE_REGISTRY,
        standard_value_sets=standard_value_sets,
    )
    report = engine.evaluate(components)

    if args.format == "html":
        output_path = resolve_path(args.output) if args.output else Path.cwd() / "nomenclature_report.html"
        write_html_report(
            report=report,
            output_path=output_path,
            project_path=project_path,
            rules_path=rules_path,
            components=components,
        )
    else:
        print_report(report, output_format=args.format)
        if args.output:
            write_report(report, resolve_path(args.output))

    return 0


def print_report(report: Report, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=True))
        return

    print(report.to_text())


def write_report(report: Report, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def write_html_report(
    report: Report,
    output_path: Path,
    project_path: Path,
    rules_path: Path,
    components: list[Component],
) -> None:
    template_dir = Path(__file__).resolve().parent / "templates"
    renderer = HtmlReportRenderer(template_dir=template_dir)
    html = renderer.render(
        report=report,
        project_path=project_path,
        rules_path=rules_path,
        components=components,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
