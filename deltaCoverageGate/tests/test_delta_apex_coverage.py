from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

VALIDATION_DIR = Path(__file__).resolve().parents[1]
import sys

if str(VALIDATION_DIR) not in sys.path:
    sys.path.insert(0, str(VALIDATION_DIR))

from metrics.delta_apex_coverage import (  # noqa: E402
    EXIT_CODE_ERROR,
    EXIT_CODE_FAIL,
    EXIT_CODE_OK,
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_PASS_NA,
    evaluate_delta_apex_coverage,
)


class DeltaApexCoverageEvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        self.validate_with_coverage = json.loads(
            (fixtures_dir / "validate_with_coverage.json").read_text(encoding="utf-8")
        )
        self.validate_missing_coverage = json.loads(
            (fixtures_dir / "validate_missing_coverage.json").read_text(
                encoding="utf-8"
            )
        )

    def _build_src_to_deploy(
        self, members: list[str] | dict[str, str], default_content: str = "// test"
    ) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="delta-apex-"))
        file_entries = (
            members.items()
            if isinstance(members, dict)
            else ((member, default_content) for member in members)
        )
        for member, content in file_entries:
            file_path = temp_dir / member
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return temp_dir

    def test_pass_with_weighted_formula_and_exclusions(self) -> None:
        src_to_deploy = self._build_src_to_deploy(
            [
                "classes/MyService.cls",
                "classes/MyServiceTest.cls",
                "classes/MyZeroClass.cls",
                "classes/IGNORE.cls-meta.xml",
            ]
        )
        payload, exit_code = evaluate_delta_apex_coverage(
            src_to_deploy=src_to_deploy,
            validate_payload=self.validate_with_coverage,
            threshold_raw="75",
        )

        self.assertEqual(STATUS_PASS, payload["status"])
        self.assertEqual(EXIT_CODE_OK, exit_code)
        self.assertEqual(1, payload["delta_apex_members_gated"])
        self.assertEqual(1, payload["delta_apex_members_test_excluded"])
        self.assertEqual(1, payload["delta_apex_members_non_executable"])
        self.assertEqual(8, payload["coverage_sum_covered"])
        self.assertEqual(10, payload["coverage_sum_total"])
        self.assertEqual(80.0, payload["coverage_pct"])

    def test_excludes_istest_class_when_name_is_not_conventional(self) -> None:
        src_to_deploy = self._build_src_to_deploy(
            {
                "classes/MyService.cls": "public class MyService {}",
                "classes/QualityGateSpec.cls": "@IsTest\nprivate class QualityGateSpec {}",
            }
        )
        payload, exit_code = evaluate_delta_apex_coverage(
            src_to_deploy=src_to_deploy,
            validate_payload=self.validate_with_coverage,
            threshold_raw="75",
        )

        self.assertEqual(STATUS_PASS, payload["status"])
        self.assertEqual(EXIT_CODE_OK, exit_code)
        self.assertEqual(1, payload["delta_apex_members_gated"])
        self.assertEqual(1, payload["delta_apex_members_test_excluded"])
        self.assertEqual(["qualitygatespec"], payload["delta_apex_test_excluded_members"])
        self.assertEqual([], payload["delta_apex_unmatched_members"])

    def test_fail_when_weighted_coverage_below_threshold(self) -> None:
        src_to_deploy = self._build_src_to_deploy(
            ["classes/MyService.cls", "classes/MyOtherService.cls"]
        )
        payload, exit_code = evaluate_delta_apex_coverage(
            src_to_deploy=src_to_deploy,
            validate_payload=self.validate_with_coverage,
            threshold_raw="90",
        )

        self.assertEqual(STATUS_FAIL, payload["status"])
        self.assertEqual(EXIT_CODE_FAIL, exit_code)
        self.assertEqual(8, payload["coverage_sum_covered"])
        self.assertEqual(15, payload["coverage_sum_total"])
        self.assertAlmostEqual(53.33, payload["coverage_pct"], places=2)

    def test_pass_na_when_no_apex_delta(self) -> None:
        src_to_deploy = self._build_src_to_deploy(["objects/Foo.object-meta.xml"])
        payload, exit_code = evaluate_delta_apex_coverage(
            src_to_deploy=src_to_deploy,
            validate_payload=self.validate_with_coverage,
            threshold_raw="85",
        )

        self.assertEqual(STATUS_PASS_NA, payload["status"])
        self.assertEqual(EXIT_CODE_OK, exit_code)
        self.assertEqual(0, payload["delta_apex_members_total"])

    def test_error_when_code_coverage_missing_with_apex_delta(self) -> None:
        src_to_deploy = self._build_src_to_deploy(["classes/MyService.cls"])
        payload, exit_code = evaluate_delta_apex_coverage(
            src_to_deploy=src_to_deploy,
            validate_payload=self.validate_missing_coverage,
            threshold_raw="85",
        )

        self.assertEqual(STATUS_ERROR, payload["status"])
        self.assertEqual(EXIT_CODE_ERROR, exit_code)
        self.assertIn("missing/empty", payload["status_message"])

    def test_error_when_executable_member_unmatched(self) -> None:
        src_to_deploy = self._build_src_to_deploy(
            ["classes/MyService.cls", "classes/UnmatchedClass.cls"]
        )
        payload, exit_code = evaluate_delta_apex_coverage(
            src_to_deploy=src_to_deploy,
            validate_payload=self.validate_with_coverage,
            threshold_raw="85",
        )

        self.assertEqual(STATUS_ERROR, payload["status"])
        self.assertEqual(EXIT_CODE_ERROR, exit_code)
        self.assertEqual(["unmatchedclass"], payload["delta_apex_unmatched_members"])

    def test_non_test_class_without_istest_still_requires_coverage_row(self) -> None:
        src_to_deploy = self._build_src_to_deploy(
            {
                "classes/MyService.cls": "public class MyService {}",
                "classes/QualityGateSpec.cls": "public class QualityGateSpec {}",
            }
        )
        payload, exit_code = evaluate_delta_apex_coverage(
            src_to_deploy=src_to_deploy,
            validate_payload=self.validate_with_coverage,
            threshold_raw="85",
        )

        self.assertEqual(STATUS_ERROR, payload["status"])
        self.assertEqual(EXIT_CODE_ERROR, exit_code)
        self.assertEqual(["qualitygatespec"], payload["delta_apex_unmatched_members"])

    def test_threshold_fallback_and_clamp_warning(self) -> None:
        src_to_deploy = self._build_src_to_deploy(["classes/MyService.cls"])
        payload, exit_code = evaluate_delta_apex_coverage(
            src_to_deploy=src_to_deploy,
            validate_payload=self.validate_with_coverage,
            threshold_raw="500",
        )

        self.assertEqual(STATUS_FAIL, payload["status"])
        self.assertEqual(EXIT_CODE_FAIL, exit_code)
        self.assertEqual(100.0, payload["threshold_effective"])
        self.assertTrue(payload["warnings"])


if __name__ == "__main__":
    unittest.main()

