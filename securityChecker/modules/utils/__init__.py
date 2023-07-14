import os
import jinja2
from jinja2 import TemplateNotFound
import __main__
from lxml import etree as ET
import math
import json
from pprint import pprint


PARSER                   = ET.XMLParser(remove_comments=False, remove_blank_text=True, encoding="utf-8")
PWD                      = os.path.dirname(os.path.realpath(__main__.__file__))
TEMPLATE_FILE            = "securityTemplate.html"
MAX_IP_ALLOWED           = 256
PS_USER_ASSINGMENT_JSON  = os.path.join(PWD, "resources", "query_output", "PermissionSetAssignment.json")
INVALID_USER_PERMISSIONS = [
    "ModifyAllData", "ViewAllData", "AuthorApex", "AssignPermissionSets",
    "EditReadonlyFields", "ModifyMetadata", "ViewSetup"
]
INVALID_APEX_RULES = [ 
    'ApexCRUDViolation', 'ApexDangerousMethods', 'ApexOpenRedirect', 'ApexSharingViolations', 'ApexSOQLInjection', 
    'ApexXSSFromURLParam', 'SecurityAuraEnabledMethods', 'SecurityAuraEnabledQueries'
]

def checkUserPermissions(userPermissionList, invalidProfile, filename):
    # COMPRUEBO USERS PERMISSIONS QUE NO CUMPLEN CON LOS REQUISITOS DE LA LISTA invalidUserPermissions
    for userPermission in userPermissionList:

        userPermissionName  = userPermission.getchildren()[1].text
        userPermissionValue = userPermission.getchildren()[0].text

        if any(ext in userPermissionName for ext in INVALID_USER_PERMISSIONS) and ("true" in userPermissionValue):
            if filename not in invalidProfile.keys() :
                dictAux = dict()
                dictAux["userPermission"] = list()
                invalidProfile[filename] = dictAux

            invalidProfile[filename]["userPermission"].append(userPermissionName)


def checkLoginIP(loginIPRangesList, invalidProfile, filename):
    if len(loginIPRangesList) != 0:
        for loginIpRange in loginIPRangesList:
            for loginIPChild in loginIpRange.getchildren():
                if "endAddress" in loginIPChild.tag:
                    endAddress = loginIPChild.text
                if "startAddress" in loginIPChild.tag:
                    startAddress = loginIPChild.text

            endAddressConverted     = calculateIpRange(endAddress)
            startAddressConverted   = calculateIpRange(startAddress)

            if (endAddressConverted - startAddressConverted) > MAX_IP_ALLOWED:
                if filename not in invalidProfile.keys():
                    invalidProfile[filename] = dict()
                if "loginIPRanges" not in invalidProfile[filename].keys() :
                    invalidProfile[filename]["loginIPRanges"] = True


def checkObjectPermission(objectPermissionList, invalidProfile, filename):
    if len(objectPermissionList) == 0:
        return invalidProfile
    else:
        for objectPermission in objectPermissionList:
            modifyAllRecords = objectPermission.getchildren()[4].text
            objectName       = objectPermission.getchildren()[5].text
            viewAllRecords   = objectPermission.getchildren()[6].text
            permissionList   = []

            if "true" in modifyAllRecords:
                permissionList.append("<b>ModifyAllRecords</b>")
            if "true" in viewAllRecords:
                permissionList.append("ViewAllRecords")
            if len(permissionList) > 0:
                if filename not in invalidProfile.keys():
                    invalidProfile[filename] = dict()
                if "objectPermissions" not in invalidProfile[filename].keys() :
                    invalidProfile[filename]["objectPermissions"] = dict()
                invalidProfile[filename]["objectPermissions"][objectName] = " & ".join(permissionList)


def calculateIpRange(address):
    addressList   = address.split(".")

    addressRange  = (((int(addressList[0]))*math.pow(256, 3)) + ((int(addressList[1]))*math.pow(256, 2)) +
                      ((int(addressList[2]))*256) + int(addressList[3]))
    return addressRange


def checkUserPSAssingment(invalidProfile):
    print( PWD )
    if not os.path.isfile( PS_USER_ASSINGMENT_JSON ):
        print( PWD )
        print( 'WARNING: Permission Set Assignment file not found, skipping assignment analysis' )
    else:
        with open( PS_USER_ASSINGMENT_JSON, 'r+' ) as file:
            queryMap = json.loads( file.read() )

            for queryResult in queryMap[ 'records' ]:
                userSet     = set()
                user        = queryResult[ 'Assignee' ][ 'Name' ]
                assignedPS  = queryResult[ 'PermissionSet' ][ 'Name' ]

                if assignedPS in invalidProfile.keys():
                    if 'userAssignment' not in invalidProfile[ assignedPS ].keys():
                        userSet.add(user)
                    else:
                        userSet = invalidProfile[ assignedPS ][ 'userAssignment' ]
                        userSet.add(user)
                    invalidProfile[ assignedPS ][ 'userAssignment' ] = userSet


def createReport(reportPath, invalidProfiles, invalidPermissionSets, externalSharingList, internalSharingList, invalidApexClasses):
    try:
        loader          = jinja2.FileSystemLoader( searchpath=( f'{PWD}/resources/' ) )
        template_env    = jinja2.Environment( loader=loader )
        template        = template_env.get_template( TEMPLATE_FILE )

        reportBody = template.render(
            invalidProfiles=invalidProfiles, invalidPermissionSets=invalidPermissionSets,
            externalSharingList=externalSharingList, internalSharingList=internalSharingList,
            invalidApexClasses=invalidApexClasses
        )

        with open( reportPath, 'w+', encoding='utf-8' ) as reportFile:
            reportFile.write(reportBody)

    except TemplateNotFound as exc:
        print( f'Cannot found {exc} in {PWD}/resources/' )
