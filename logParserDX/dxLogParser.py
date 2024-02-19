
import os.path

import jinja2
from jinja2 import TemplateNotFound

from modules.utils import TEMPLATE_FILE, generateComponentDict, generateTestDict, PWD
from modules.utils.argparser import parseArgs

__version__ = "1.0.1"


def prevalidations(args):
    if not os.path.exists( args.input_path ):
        raise inputFileException

def main():
    args = parseArgs()
    prevalidations(args)

    if args.option == 'version':
        print( __version__ )
        exit( 0 )

    elif args.option == 'logParser':
        (sfdx_status, componentDict, errorNumber, sfdx_operation,
        componentHeaders, json_data) = generateComponentDict(args.input_path)
        testResultDict               = generateTestDict(json_data)

        # Sort the TestResult Dictionary for better view on report
        testResultDict = {k: v for k, v in sorted(testResultDict.items(), key=lambda item: item[1])}
        try:
            loader          = jinja2.FileSystemLoader(searchpath=(f'{PWD}/resources/'))
            template_env    = jinja2.Environment(loader=loader)
            template        = template_env.get_template(TEMPLATE_FILE)
            report_file     = template.render(componentDict =componentDict,
                                            errorNumber     =errorNumber,
                                            sfdx_operation  =sfdx_operation,
                                            componentHeaders=componentHeaders,
                                            testResultDict  =testResultDict,
                                            sfdx_status     =sfdx_status)

            with open(f'{args.output_path}', 'w+', encoding='utf-8') as output_file:
                output_file.write(report_file)

        except TemplateNotFound as exc:
            print(f" Cannot found {exc} in {PWD}/resources/templates/")


if __name__ == "__main__":
    main()
