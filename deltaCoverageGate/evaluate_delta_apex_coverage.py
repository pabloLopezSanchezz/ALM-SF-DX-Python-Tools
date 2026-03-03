#!/usr/bin/env python3
"""CLI wrapper for delta-only Apex coverage gate evaluator."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from metrics.delta_apex_coverage import (
    EXIT_CODE_ERROR,
    evaluate_delta_apex_coverage,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate delta-only Apex coverage gate using srcToDeploy and validate.json."
        )
    )
    parser.add_argument(
        "--src-to-deploy",
        required=True,
        help="Path to srcToDeploy folder to scan for .cls/.trigger files.",
    )
    parser.add_argument(
        "--validate-json",
        required=True,
        help="Path to validate.json produced by sf project deploy report --json.",
    )
    parser.add_argument(
        "--threshold",
        default=None,
        help=(
            "Optional threshold override. If not supplied, reads "
            "DELTA_APEX_COVERAGE_THRESHOLD."
        ),
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional file path to write diagnostics JSON payload.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_json_path = Path(args.validate_json)

    if not validate_json_path.exists():
        payload = {
            "status": "ERROR",
            "status_message": f"validate.json not found at {validate_json_path}",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_CODE_ERROR

    try:
        with validate_json_path.open("r", encoding="utf-8") as handle:
            validate_payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        payload = {
            "status": "ERROR",
            "status_message": f"Could not parse validate.json: {exc}",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_CODE_ERROR

    threshold_raw = (
        args.threshold
        if args.threshold is not None
        else os.getenv("DELTA_APEX_COVERAGE_THRESHOLD")
    )
    payload, exit_code = evaluate_delta_apex_coverage(
        src_to_deploy=Path(args.src_to_deploy),
        validate_payload=validate_payload,
        threshold_raw=threshold_raw,
    )

    output = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + "\n", encoding="utf-8")
    print(output)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

