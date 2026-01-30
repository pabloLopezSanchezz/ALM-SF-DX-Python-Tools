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

        # Sort the TestResult Dictionary for better view on report
        testResultDict = {k: v for k, v in sorted(testResultDict.items(), key=lambda item: item[1])}
        
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
                sfdx_status=sfdx_status
            )

            with open(f'{args.output_path}', 'w+', encoding='utf-8') as output_file:
                output_file.write(report_file)
            
            print(f"Report generated successfully: {args.output_path}")

        except TemplateNotFound as exc:
            print(f"Cannot find {exc} in {PWD}/resources/")
            exit(1)


if __name__ == "__main__":
    main()
