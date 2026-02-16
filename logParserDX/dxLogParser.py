#!/usr/bin/env python3
"""
Salesforce DX Log Parser
Generates user-friendly HTML reports from validation/deployment results
"""

import os.path
import jinja2
from jinja2 import TemplateNotFound
from datetime import datetime

from modules.utils import TEMPLATE_FILE, generateComponentDict, generateTestDict, PWD
from modules.utils.argparser import parseArgs

__version__ = "1.1.0"


class InputFileException(Exception):
    """Exception raised when input file does not exist"""
    pass


def prevalidations(args):
    """Validate input file exists"""
    if not os.path.exists(args.input_path):
        raise InputFileException(f"Input file not found: {args.input_path}")


def format_datetime(value, format="%Y-%m-%d %H:%M:%S"):
    """Format datetime for Jinja2 template"""
    return value.strftime(format)


def infer_root_cause(component_dict, test_result_dict, sfdx_status):
    """Infer a concise root cause message for report header."""
    if sfdx_status == "Success":
        return "success", "Deployment and test validations completed successfully."

    if component_dict:
        return "error", "Deployment failed due to component validation errors."

    summary = test_result_dict.get("summary", {})
    failures = test_result_dict.get("failures", [])
    coverage_warnings = test_result_dict.get("coverage_warnings", [])
    flow_coverage_warnings = test_result_dict.get("flow_coverage_warnings", [])

    if failures:
        return "error", "Deployment failed due to Apex test execution failures."
    if coverage_warnings:
        return "error", "Deployment failed due to Apex code coverage requirements not met."
    if flow_coverage_warnings:
        return "error", "Deployment failed due to Flow coverage warnings."
    if summary.get("no_tests_executed"):
        return "warning", "Tests are enabled but no tests were executed in this run."

    return "error", "Deployment failed due to validation/test issues. Review detailed sections."


def main():
    args = parseArgs()
    
    if args.option == 'version':
        print(__version__)
        exit(0)

    elif args.option == 'logParser':
        prevalidations(args)
        
        (sfdx_status, componentDict, errorNumber, sfdx_operation,
         componentHeaders, json_data) = generateComponentDict(args.input_path)
        testResultDict = generateTestDict(json_data)

        # Sort test coverage dictionary for better view on report
        coverage_by_class = testResultDict.get("coverage_by_class", {})
        testResultDict["coverage_by_class"] = {
            key: value
            for key, value in sorted(coverage_by_class.items(), key=lambda item: item[1])
        }

        has_component_errors = bool(componentDict)
        has_test_issues = bool(testResultDict.get("summary", {}).get("has_issues", False))
        is_full_success = sfdx_status == "Success" and not has_component_errors and not has_test_issues
        root_cause_level, root_cause_message = infer_root_cause(
            component_dict=componentDict,
            test_result_dict=testResultDict,
            sfdx_status=sfdx_status,
        )
        
        try:
            loader = jinja2.FileSystemLoader(searchpath=(f'{PWD}/resources/'))
            template_env = jinja2.Environment(loader=loader)
            template_env.globals['now'] = datetime.utcnow
            template_env.filters['date'] = format_datetime
            template = template_env.get_template(TEMPLATE_FILE)
            
            report_file = template.render(
                componentDict=componentDict,
                errorNumber=errorNumber,
                sfdx_operation=sfdx_operation,
                componentHeaders=componentHeaders,
                testResultDict=testResultDict,
                sfdx_status=sfdx_status,
                has_component_errors=has_component_errors,
                has_test_issues=has_test_issues,
                is_full_success=is_full_success,
                root_cause_level=root_cause_level,
                root_cause_message=root_cause_message,
            )

            with open(f'{args.output_path}', 'w+', encoding='utf-8') as output_file:
                output_file.write(report_file)
            
            print(f"Report generated successfully: {args.output_path}")

        except TemplateNotFound as exc:
            print(f"Cannot find {exc} in {PWD}/resources/")
            exit(1)


if __name__ == "__main__":
    main()
