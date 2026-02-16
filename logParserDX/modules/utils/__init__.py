import json
import os
import __main__

PWD = os.path.dirname(os.path.realpath(__main__.__file__))
TEMPLATE_FILE = "expPanel.html"
JSON_FILE = 'validateReport.json'


def generateTestDict(json_data):
    """Generate structured dictionary with test execution and coverage results."""
    result_data = json_data.get("result", {})
    details_data = result_data.get("details", {})
    run_test_result = details_data.get("runTestResult", {})

    coverage_by_class = {}
    for test in _as_list(run_test_result.get("codeCoverage", [])):
        test_name = test.get("name")
        if not test_name:
            continue
        test_coverage = getTestCoverage(
            test.get("numLocations", 0),
            test.get("numLocationsNotCovered", 0),
        )
        coverage_by_class[test_name] = test_coverage

    failures = []
    for failure in _as_list(run_test_result.get("failures", [])):
        failures.append(
            {
                "name": failure.get("name", "Unknown"),
                "methodName": failure.get("methodName", ""),
                "message": failure.get("message", "No message"),
                "stackTrace": failure.get("stackTrace", ""),
            }
        )

    coverage_warnings = []
    for warning in _as_list(run_test_result.get("codeCoverageWarnings", [])):
        coverage_warnings.append(
            {
                "name": warning.get("name", "Unknown"),
                "message": warning.get("message", "No message"),
            }
        )

    flow_coverage_warnings = []
    for warning in _as_list(run_test_result.get("flowCoverageWarnings", [])):
        flow_coverage_warnings.append(
            {
                "name": warning.get("name", "Unknown"),
                "message": warning.get("message", "No message"),
            }
        )

    num_tests_run = int(run_test_result.get("numTestsRun", 0))
    num_failures = int(run_test_result.get("numFailures", len(failures)))
    num_tests_total = int(result_data.get("numberTestsTotal", 0))
    tests_enabled = bool(result_data.get("runTestsEnabled", False))

    has_issues = (
        num_failures > 0
        or len(coverage_warnings) > 0
        or len(flow_coverage_warnings) > 0
    )

    return {
        "coverage_by_class": coverage_by_class,
        "failures": failures,
        "coverage_warnings": coverage_warnings,
        "flow_coverage_warnings": flow_coverage_warnings,
        "summary": {
            "num_tests_run": num_tests_run,
            "num_failures": num_failures,
            "num_tests_total": num_tests_total,
            "tests_enabled": tests_enabled,
            "no_tests_executed": tests_enabled and num_tests_run == 0 and num_tests_total == 0,
            "has_issues": has_issues,
        },
    }


def getTestCoverage(totalLines, linesNotCovered):
    """Calculate test coverage percentage"""
    totalLines = int(totalLines)
    linesNotCovered = int(linesNotCovered)
    if 0 != totalLines:
        testNotCoverage = (100 * linesNotCovered) / totalLines
        return round(100 - testNotCoverage, 2)
    else:
        return 0


def generateComponentDict(input_path):
    """Generate dictionary with component failures from validation/deploy result"""
    componentDict = {}
    componentHeaders = {}
    
    with open(f'{input_path}') as json_file:
        json_data = json.load(json_file)
        try:
            result_data = json_data["result"]
            details_data = result_data.get("details", {})
            sfdx_operation = "Validate" if result_data["checkOnly"] else "Deploy"
            componentFailure = _as_list(details_data.get("componentFailures", []))
            result_status = str(result_data.get("status", "")).lower()
            result_success = bool(result_data.get("success", True))
            has_component_failures = len(componentFailure) > 0
            sfdx_status = (
                "Error"
                if (not result_success or result_status in {"failed", "error", "canceled"} or has_component_failures)
                else "Success"
            )
        except KeyError as e:
            print(f"[ERROR] Value {e} did not find on {input_path}. Check validate.json.")
            exit(1)
            
        if componentFailure:
            for index in range(len(componentFailure)):
                if componentFailure[index]['componentType'] in componentDict:
                    componentDict[componentFailure[index]['componentType']].append(
                        generateFailureDict(componentFailure, index))
                else:
                    listComponents = []
                    listComponents.append(generateFailureDict(componentFailure, index))
                    componentDict[componentFailure[index]['componentType']] = listComponents

                with open(f'{PWD}/resources/validateReport.json', 'w+', encoding='utf-8') as output_file:
                    json.dump(componentDict, output_file, ensure_ascii=False, indent=4)

            componentHeaders = generateHeaders(componentDict)
            return (sfdx_status, componentDict, len(componentFailure), sfdx_operation,
                    componentHeaders, json_data)
        else:
            return sfdx_status, {}, 0, sfdx_operation, {}, json_data


def valueInListChecker(globalHeaderList, headerList):
    """Check if header values exist in global list"""
    set_difference = set(headerList) - set(globalHeaderList)
    list_difference = list(set_difference)
    if list_difference:
        globalHeaderList.extend(list_difference)
        return globalHeaderList
    else:
        return globalHeaderList


def generateHeaders(componentDict):
    """Generate headers for component tables"""
    additionalHeaders = {}
    componentHeaders = []
    for keyComponent, dataList in componentDict.items():
        for valueList in dataList:
            for data in valueList.values():
                componentHeaders = valueInListChecker(componentHeaders, list(data.keys()))
        additionalHeaders[keyComponent] = True if 'lineNumber' in componentHeaders else False
        componentHeaders = []
    return additionalHeaders


def generateFailureDict(componentFailure, index):
    """Generate dictionary for a single component failure"""
    dictDataComponent = {}
    dictDataAuxComponent = {}

    dictDataAuxComponent['problem'] = componentFailure[index]['problem'].replace('<', '').replace('>', '')
    dictDataAuxComponent['problemType'] = componentFailure[index]['problemType']
    dictDataAuxComponent['componentType'] = componentFailure[index]['componentType']
    if "lineNumber" in componentFailure[index]:
        dictDataAuxComponent['lineNumber'] = componentFailure[index]['lineNumber']

    dictDataComponent[componentFailure[index]['fullName']] = dictDataAuxComponent
    return dictDataComponent


def _as_list(value):
    """Normalize scalar/object/list values to a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
