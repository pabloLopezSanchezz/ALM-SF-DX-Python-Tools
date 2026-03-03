"""Delta-only Apex coverage evaluator.

This module implements the policy contract described in:
docs/agent-hub/plans/2026-03-02-delta-gate-readiness-contract.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_PASS_NA = "PASS_NA"
STATUS_ERROR = "ERROR"

EXIT_CODE_OK = 0
EXIT_CODE_FAIL = 10
EXIT_CODE_ERROR = 20

FALLBACK_THRESHOLD = 80.0


@dataclass(frozen=True)
class ThresholdResult:
    raw_value: str | None
    effective: float
    warnings: list[str]


def normalize_threshold(raw_value: str | None) -> ThresholdResult:
    """Parse threshold with fallback+clamp policy."""
    warnings: list[str] = []
    candidate: float

    if raw_value is None or raw_value.strip() == "":
        candidate = FALLBACK_THRESHOLD
        warnings.append(
            "DELTA_APEX_COVERAGE_THRESHOLD missing/empty; using fallback 80."
        )
    else:
        try:
            candidate = float(raw_value)
        except ValueError:
            candidate = FALLBACK_THRESHOLD
            warnings.append(
                "DELTA_APEX_COVERAGE_THRESHOLD non-numeric; using fallback 80."
            )

    clamped = max(0.0, min(100.0, candidate))
    if clamped != candidate:
        warnings.append(
            f"DELTA_APEX_COVERAGE_THRESHOLD clamped from {candidate} to {clamped}."
        )

    return ThresholdResult(raw_value=raw_value, effective=clamped, warnings=warnings)


def _scan_delta_apex_members(src_to_deploy: Path) -> set[str]:
    members: set[str] = set()
    if not src_to_deploy.exists():
        return members

    for file_path in src_to_deploy.rglob("*"):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix in {".cls", ".trigger"}:
            members.add(file_path.stem.lower())
    return members


def _extract_code_coverage_rows(validate_payload: dict[str, Any]) -> list[dict[str, Any]] | None:
    paths = (
        ("result", "details", "runTestResult", "codeCoverage"),
        ("result", "runTestResult", "codeCoverage"),
        ("runTestResult", "codeCoverage"),
    )
    for path in paths:
        node: Any = validate_payload
        for key in path:
            if not isinstance(node, dict) or key not in node:
                node = None
                break
            node = node[key]
        if node is not None:
            if isinstance(node, list):
                return node
            return []
    return None


def _coverage_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        key = name.strip().lower()
        if key not in indexed:
            indexed[key] = row
    return indexed


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _build_payload(**kwargs: Any) -> dict[str, Any]:
    payload = dict(kwargs)
    payload["coverage_pct"] = round(payload["coverage_pct"], 2)
    payload["threshold_effective"] = round(payload["threshold_effective"], 2)
    return payload


def evaluate_delta_apex_coverage(
    src_to_deploy: Path,
    validate_payload: dict[str, Any],
    threshold_raw: str | None,
) -> tuple[dict[str, Any], int]:
    """Evaluate delta-only Apex coverage status and diagnostics payload."""
    threshold = normalize_threshold(threshold_raw)
    delta_members = _scan_delta_apex_members(src_to_deploy)

    base_payload = {
        "delta_apex_members_total": len(delta_members),
        "delta_apex_members_gated": 0,
        "delta_apex_members_test_excluded": 0,
        "delta_apex_members_non_executable": 0,
        "delta_apex_members_unmatched": 0,
        "coverage_sum_covered": 0,
        "coverage_sum_total": 0,
        "coverage_pct": 0.0,
        "threshold_effective": threshold.effective,
        "status": STATUS_PASS_NA,
        "status_message": "No Apex delta detected; coverage gate not applicable.",
        "warnings": threshold.warnings,
        "delta_apex_unmatched_members": [],
        "delta_apex_non_executable_members": [],
        "delta_apex_test_excluded_members": [],
    }

    if not delta_members:
        return _build_payload(**base_payload), EXIT_CODE_OK

    coverage_rows = _extract_code_coverage_rows(validate_payload)
    if not coverage_rows:
        payload = _build_payload(
            **{
                **base_payload,
                "status": STATUS_ERROR,
                "status_message": (
                    "Apex delta exists but validate.json has missing/empty "
                    "runTestResult.codeCoverage."
                ),
            }
        )
        return payload, EXIT_CODE_ERROR

    index = _coverage_index(coverage_rows)
    test_excluded_members = sorted(
        member for member in delta_members if member.endswith("test")
    )
    candidate_members = sorted(delta_members.difference(test_excluded_members))
    unmatched_members = [member for member in candidate_members if member not in index]

    if unmatched_members:
        payload = _build_payload(
            **{
                **base_payload,
                "delta_apex_members_test_excluded": len(test_excluded_members),
                "delta_apex_members_unmatched": len(unmatched_members),
                "delta_apex_unmatched_members": unmatched_members,
                "delta_apex_test_excluded_members": test_excluded_members,
                "status": STATUS_ERROR,
                "status_message": (
                    "Executable delta Apex members are missing coverage rows: "
                    + ", ".join(unmatched_members)
                ),
            }
        )
        return payload, EXIT_CODE_ERROR

    sum_covered = 0
    sum_total = 0
    non_executable_members: list[str] = []

    for member in candidate_members:
        row = index[member]
        total = _to_int(row.get("numLocations"), default=0)
        not_covered = _to_int(row.get("numLocationsNotCovered"), default=0)

        if total <= 0:
            non_executable_members.append(member)
            continue

        covered = max(0, total - max(0, not_covered))
        sum_covered += covered
        sum_total += total

    gated_count = len(candidate_members) - len(non_executable_members)
    if sum_total == 0:
        payload = _build_payload(
            **{
                **base_payload,
                "delta_apex_members_gated": gated_count,
                "delta_apex_members_test_excluded": len(test_excluded_members),
                "delta_apex_members_non_executable": len(non_executable_members),
                "delta_apex_non_executable_members": non_executable_members,
                "delta_apex_test_excluded_members": test_excluded_members,
                "status": STATUS_PASS_NA,
                "status_message": (
                    "Apex delta has no executable non-test members; "
                    "coverage gate not applicable."
                ),
            }
        )
        return payload, EXIT_CODE_OK

    coverage_pct = (100.0 * sum_covered) / sum_total
    status = STATUS_PASS if coverage_pct >= threshold.effective else STATUS_FAIL
    exit_code = EXIT_CODE_OK if status == STATUS_PASS else EXIT_CODE_FAIL

    status_message = (
        f"Delta Apex coverage {coverage_pct:.2f}% meets threshold "
        f"{threshold.effective:.2f}%."
        if status == STATUS_PASS
        else (
            f"Delta Apex coverage {coverage_pct:.2f}% is below threshold "
            f"{threshold.effective:.2f}%."
        )
    )

    payload = _build_payload(
        **{
            **base_payload,
            "delta_apex_members_gated": gated_count,
            "delta_apex_members_test_excluded": len(test_excluded_members),
            "delta_apex_members_non_executable": len(non_executable_members),
            "coverage_sum_covered": sum_covered,
            "coverage_sum_total": sum_total,
            "coverage_pct": coverage_pct,
            "status": status,
            "status_message": status_message,
            "delta_apex_non_executable_members": non_executable_members,
            "delta_apex_test_excluded_members": test_excluded_members,
        }
    )
    return payload, exit_code

