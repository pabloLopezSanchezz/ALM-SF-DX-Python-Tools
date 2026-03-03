# Delta Apex Coverage Gate Evaluator

Use `evaluate_delta_apex_coverage.py` to compute the delta-only Apex gate status from:

- `srcToDeploy` (filesystem scan for `.cls` and `.trigger`)
- `validate.json` (`runTestResult.codeCoverage`)

## Usage

```bash
python3 AP_CODE-TEMPLATES/validation/evaluate_delta_apex_coverage.py \
  --src-to-deploy /path/to/srcToDeploy \
  --validate-json /path/to/validate.json \
  --output /path/to/artifacts_folder/delta_apex_coverage_gate.json
```

Threshold precedence:

1. `--threshold` CLI arg (if provided)
2. `DELTA_APEX_COVERAGE_THRESHOLD`
3. Fallback `80` (warning emitted)

Effective threshold is clamped to `[0,100]`.

Exit codes:

- `0`: `PASS` or `PASS_NA`
- `10`: `FAIL`
- `20`: `ERROR`

The script writes a machine-readable JSON payload to stdout (and to `--output` when provided), including gate status, message, counts, sums, and warning details.

