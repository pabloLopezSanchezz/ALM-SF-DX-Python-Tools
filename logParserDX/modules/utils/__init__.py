import json
import os
import __main__

PWD = os.path.dirname(os.path.realpath(__main__.__file__))
TEMPLATE_FILE = "expPanel.html"
JSON_FILE = 'noTest.json'


def generateTestDict(json_data):
    testResultDict = {}

    if json_data['result']['numberTestsTotal'] != 0:
        try:
            testResultList = json_data['result']['details']['runTestResult']['codeCoverage']
            for test in testResultList:
                testCoverage = getTestCoverage(test['numLocations'], test['numLocationsNotCovered'])
                testResultDict[test['name']] = testCoverage
            return testResultDict
        except KeyError as e:
            print(f"No Key {e} in Validate.json")
            print(f"[TEST ERRORS - MAY BE ERRORS ON TEST EXECUTION]")
            return {}
    else:
        return testResultDict


def getTestCoverage(totalLines, linesNotCovered):
    totalLines = int(totalLines)
    linesNotCovered = int(linesNotCovered)
    if 0 != totalLines:
        testNotCoverage = (100*linesNotCovered)/totalLines
        return round(100 - testNotCoverage, 2)
    else:
        return 0


def generateComponentDict(input_path):
    componentDict       = {}
    componentHeaders    = {}
    with open(f'{input_path}') as json_file:
        json_data     = json.load(json_file)
        try:
            sfdx_operation= "Validate" if json_data['result']['checkOnly'] else "Deploy"
            sfdx_status   = "Error" if 'componentFailures' in json_data['result']['details'].keys() else "Success"
        except KeyError as e:
            print(f"[ERROR] Value {e} did not find on {input_path}. Check validate.json.")
            exit(1)
        if "Error" == sfdx_status:
            componentFailure= json_data['result']['details']['componentFailures']

            for index in range(len(componentFailure)):
                if componentFailure[index]['componentType'] in componentDict:
                    componentDict[componentFailure[index]['componentType']].append(
                                    generateFailureDict(componentFailure, index))

                else:
                    listComponents = []

                    listComponents.append(generateFailureDict(componentFailure, index))
                    componentDict[componentFailure[index]['componentType']] = listComponents

                with open(f'{PWD}/resources/validateReport.json', 'w+', encoding='utf-8') as output_file:
                    json.dump(componentDict, output_file, ensure_ascii=False,
                            indent=4)

            componentHeaders = generateHeaders(componentDict)
            return (sfdx_status, componentDict, len(componentFailure), sfdx_operation,
                    componentHeaders, json_data)
        else:
            return sfdx_status, {}, 0, sfdx_operation, {}, json_data



def valueInListChecker(globalHeaderList, headerList):
    set_difference = set(headerList) - set(globalHeaderList)
    list_difference = list(set_difference)
    if list_difference:
        globalHeaderList.extend(list_difference)
        return globalHeaderList
    else:
        return globalHeaderList


def generateHeaders(componentDict):
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
    dictDataComponent = {}
    dictDataAuxComponent = {}

    dictDataAuxComponent['problem'] = componentFailure[index]['problem'].replace('<', '').replace('>', '')
    dictDataAuxComponent['problemType'] = componentFailure[index]['problemType']
    dictDataAuxComponent['componentType'] = componentFailure[index]['componentType']
    if "lineNumber" in componentFailure[index]:
        dictDataAuxComponent['lineNumber'] = componentFailure[index]['lineNumber']

    dictDataComponent[componentFailure[index]['fullName']] = dictDataAuxComponent
    return dictDataComponent
