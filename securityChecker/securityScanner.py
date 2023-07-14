import lxml
import os
import csv
from modules.utils import (PARSER, ET, createReport,
                           checkUserPermissions, checkLoginIP,
                           checkObjectPermission, checkUserPSAssingment, INVALID_APEX_RULES )
from modules.utils import argparser
from modules.models import ObjectSecurity


def main():

    args = argparser.parseArgs()

    invalidProfiles                          = profilesChecker( args.pathToSrc )
    invalidPermissionSets                    = permissionSetsChecker( args.pathToSrc )
    externalSharingList, internalSharingList = objectChecker( args.pathToSrc )

    invalidApexClasses = apexChecker( args.pathToPmdReport ) if args.pathToPmdReport else []

    createReport( args.reportPath, invalidProfiles, invalidPermissionSets, externalSharingList, internalSharingList, invalidApexClasses )


def profilesChecker(pathToSrc):
    mapInvalidProfiles = {}
    checkPermissions( pathToSrc, 'profiles', mapInvalidProfiles )
    return mapInvalidProfiles


def permissionSetsChecker(pathToSrc):
    mapInvalidPermissionSets = {}
    checkPermissions( pathToSrc, 'permissionsets', mapInvalidPermissionSets )
    checkUserPSAssingment( mapInvalidPermissionSets )

    return mapInvalidPermissionSets


def checkPermissions(pathToSrc, folderPath, mapInvalidPermissions):
    metadataPath = os.path.join( pathToSrc, folderPath )

    if not os.path.isdir( metadataPath ):
        print( f'WARNING: {folderPath} folder not found, skipping analysis' )
    else:
        for fileName in os.listdir( metadataPath ):
            fullmetadataPath        = os.path.join( pathToSrc, folderPath, fileName )
            tree                    = ET.parse(fullmetadataPath, parser=PARSER)
            userPermissionList      = tree.xpath('//*[local-name() = "userPermissions"]')
            loginIPRangesList       = tree.xpath('//*[local-name() = "loginIpRanges"]')
            objectPermissionList    = tree.xpath('//*[local-name() = "objectPermissions"]')
            fileName                = fileName.split( '.' )[ 0 ]
            checkUserPermissions( userPermissionList, mapInvalidPermissions, fileName )
            checkLoginIP( loginIPRangesList, mapInvalidPermissions, fileName )
            checkObjectPermission( objectPermissionList, mapInvalidPermissions, fileName )


def apexChecker(pathToPmdReport):
    mapInvalidApexClasses = {}

    if not os.path.isfile( pathToPmdReport ):
        print( f'WARNING: PMD report not found, skipping analysis' )
    else:
        with open( pathToPmdReport, 'r' ) as pmdReport:
            csvContent = csv.DictReader( pmdReport )
            for issue in csvContent:
                ruleName = issue[ 'Rule' ]
                if ruleName in INVALID_APEX_RULES:
                    className = issue[ 'File' ]
                    if '\\classes\\' in className:
                        className = className.split( '\\classes\\' )[ 1 ]
                    elif '\\triggers\\' in className:
                        className = className.split( '\\triggers\\' )[ 1 ]

                    if className not in mapInvalidApexClasses:
                        mapInvalidApexClasses[ className ] = {}
                    if ruleName not in mapInvalidApexClasses[ className ]:
                        mapInvalidApexClasses[ className ][ ruleName ] = []
                    mapInvalidApexClasses[ className ][ ruleName ].append( issue )

    return mapInvalidApexClasses


def objectChecker(pathToSrc):
    objectSecurityMap   = {}
    externalSharingList = []
    internalSharingList = []

    objectPath = os.path.join( pathToSrc, 'objects' )

    if not os.path.isdir( objectPath ):
        print( f'WARNING: objects folder not found, skipping Sharing Model analysis' )
    else:
        for customObject in os.listdir( objectPath ):
            fullObjectPath = os.path.join( pathToSrc, 'objects', customObject, f'{customObject}.object-meta.xml' )

            xmlns   = 'http://soap.sforce.com/2006/04/metadata'
            mapXmln = { 'x' : xmlns }

            tree                 = ET.parse(fullObjectPath, parser=PARSER)
            label                = tree.xpath( '/x:CustomObject/x:label/text()', namespaces=mapXmln )
            objectLabel          = label[ 0 ] if label else customObject
            sharingModel         = tree.xpath( '/x:CustomObject/x:sharingModel/text()', namespaces=mapXmln )
            externalSharingModel = tree.xpath( '/x:CustomObject/x:externalSharingModel/text()', namespaces=mapXmln )

            if ( len( sharingModel ) > 0 ) and ( 'Read' in str( sharingModel[0] ) ):
                internalSharingList.append( { 'label' : objectLabel, 'apiName' : customObject, 'sharingModel' : str( sharingModel[0] ) } )

            if ( len( externalSharingModel ) > 0 ) and ( 'Read' in str( externalSharingModel[0] ) ):
                externalSharingList.append( { 'label' : objectLabel, 'apiName' : customObject, 'sharingModel' : str( externalSharingModel[0] ) } )

            objSecurity = ObjectSecurity(sharingModel, externalSharingModel)
            objectSecurityMap[customObject] = objSecurity

    return externalSharingList, internalSharingList


if __name__ == "__main__":
    main()
