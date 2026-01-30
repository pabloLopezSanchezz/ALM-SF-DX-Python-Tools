"""Argparse Module for DX Log Parser"""

import argparse


def parseArgs():
    """Parse command line arguments"""

    description = ('Parser to generate a user-friendly report with '
                   'detailed information from failed validation/deployment tasks')
    parser = argparse.ArgumentParser(description=description)
    subparsers = parser.add_subparsers(help='commands', dest='option')
    subparsers.required = True

    subparsers.add_parser('version', help='Returns the version of the script')

    logExecHelp = 'Execute the generation of the report'
    logParser(subparsers.add_parser('logParser', help=logExecHelp))

    args = parser.parse_args()

    return args


def logParser(subparser):
    """Adds arguments for logParser subparser"""

    subparser.add_argument('-p', '--input-path', required=True,
                           help='Relative path to the validation Log (validate.json)')
    subparser.add_argument('-O', '--output-path', required=True,
                           help='Relative path to the output report (report.html)')
