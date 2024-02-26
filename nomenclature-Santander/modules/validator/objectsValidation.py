import re
import os
import xml.etree.ElementTree as ET
from modules.utils.utilities import checkDescription, checkNomenclatureGeneral, deleteExtension


def checkCustomObject(dir, folder, objectName, objToDeploy, incorrectOBJ, incorrectFLD, incorrectVLR, incorrectRTP, incorrectDescription):
    
    #Custom object -> report if invalid nomenclature
    for subfolder in os.listdir(f'{dir}/{folder}/{objectName}'):
        if subfolder.endswith('-meta.xml') and '__' in objectName:      # If is not subfolder and it is object name
            # Object
            object = subfolder
            object = object.replace('-meta.xml', '')
            object = ''.join(object.split('.')[0:-1])

            # Types of object:
            if object.endswith('__c'):
                
                reportName = object
                apiName = object.split('__')[0]         # remove __c, split for __ and keep only first one, the apiName
                checkNomenclatureGeneral(reportName, apiName, incorrectOBJ) 
                pathSrc = os.path.join(dir, folder, objectName, subfolder)
                checkObjectDescription(pathSrc, apiName, incorrectDescription)
                

        elif not subfolder.endswith('-meta.xml'):   #is a subfolder, it could be fields, recordTypes, validationRules
            objToDeploy.append(subfolder)
            # Subfolder
            for fileName in os.listdir(f'{dir}/{folder}/{objectName}/{subfolder}'):
                if 'fields' in subfolder:
                    # remove field-meta.xml from every field in folder
                    #if fileName.endswith('-meta.xml'):
                    #    fileName = fileName.replace('-meta.xml','')
                    apiName = fileName.split('.')[0]
                    reportName = objectName + '.' + fileName

                    if '__' in apiName:
                        apiName = apiName.split('__')[0]

                    checkNomenclatureFields(reportName, apiName, incorrectFLD)
                    pathSrc = os.path.join(dir, folder, objectName, subfolder,fileName)
                    checkDescription(pathSrc, reportName, apiName, incorrectDescription)
                
                elif 'validationRules' in subfolder:
                    apiName = fileName.split('.')[0]
                    reportName = objectName + '.' + fileName
                    checkNomenclatureGeneral(reportName, apiName, incorrectVLR)
                    pathSrc = os.path.join(dir, folder, objectName, subfolder,fileName)
                    checkDescription(pathSrc, reportName, apiName, incorrectDescription)
                    
                elif 'recordType' in subfolder:
                    reportName = objectName + '.' + fileName
                    if not fileName.startswith( objectName ) :
                        incorrectRTP.append(reportName)
                    else:
                        checkNomenclatureGeneral(reportName, apiName, incorrectRTP)


def checkNomenclatureFields(fileName, apiName, incorrectName):
    # Check extension (name.extension-meta.xml or name.extension)
    fileName = deleteExtension(fileName)
    apiName = deleteExtension(apiName)
    prefixList = ['AUT', 'FOR', 'RUP', 'LKP', 'MSD', 'ELR', 'CHK', 'CUR', 'DAT', 'DTM', 'EML', 'GEO', 'NUM', 'PCT', 'PHO', 'PCK', 'TXT', 'TIM', 'ADD']
    typeList = ['AutoNumber', 'Formula', 'Roll-Up Summary', 'Lookup Relationship', 'Master-Detail Relationship', 'External Lookup Relationship', 'Checkbox', 'Currency', 'Date', 'Date/Time', 'Email', 'Geolocation', 'Number', 'Percent', 'Phone', 'Picklist', 'Picklist', 'Time', 'Address']

    if not '_' in apiName:
        # Invalid name
        incorrectName.append(fileName)
    else:
        if (len(apiName.split('_')) == 3) :
            if  not (  apiName.split('_')[1] in prefixList ) or not (  (apiName.split('_')[2])[0].istitle() ) :
                incorrectName.append(fileName)
                
        else:
            # Invalid fileName
            incorrectName.append(fileName)

    return incorrectName


def checkObjectDescription(pathSrc, apiName, withoutDescription):
    pattern = re.compile(r'\[[A-Z]{3}\]')
    try:
        
        tree = ET.parse(pathSrc)
        root = tree.getroot()
                    
        description = root.find('{http://soap.sforce.com/2006/04/metadata}description')
        if description is None:
            withoutDescription.append(apiName)
        
        else: 
            description_text = description.text  # Obtenemos el texto del tag 'description'
            if description_text is not None:
                if not pattern.match(description.text.strip()):
                    withoutDescription.append(apiName)
                    
            else:
                withoutDescription.append(apiName)
            
        return withoutDescription
        
    except Exception as e:
        print(f'Error while read new file {apiName}. Error: {str(e)}')
