import os
import xml.etree.ElementTree as ET
import re
from modules.utils.argsParser import parseArgs
from modules.validator.classesValidation import checkClass
from modules.utils.utilities import checkNomenclatureGeneral, generate_html, checkDescription
from modules.validator.objectsValidation import checkCustomObject


def nomenclatureValidator(pathToSrc):
    incorrectLWC = []
    incorrectAPR = []
    incorrectVFP = []
    incorrectOBJ = []
    incorrectFLD = []
    incorrectVLR = []
    incorrectRTP = []
    incorrectCLS = []
    incorrectTest = []
    incorrectTRG = []
    objToDeploy = []
    incorrectDescription = []

    validEndingsClasses = ['VFController', 'Controller', 'Extension', 'Handler', 'Util', 'TriggerHandler', 'Batch', 'Scheduler', 'Queue']

    for folder in os.listdir(pathToSrc):
        print( f'Validating {folder}' )
                
        for fileName in os.listdir(f'{pathToSrc}/{folder}'):
            if 'objects' in folder:
                checkCustomObject(pathToSrc, folder, fileName,objToDeploy, incorrectOBJ, incorrectFLD, incorrectVLR, incorrectRTP, incorrectDescription)

            elif 'approvalProcesses' in folder:
                if fileName.endswith('-meta.xml'):
                    fileName = fileName.replace('-meta.xml','')
                apiName = fileName.split('.')[1]
                reportName = apiName
                checkNomenclatureGeneral(reportName, apiName, incorrectAPR)

            elif 'pages' in folder:
                if fileName.endswith('-meta.xml'):
                    fileName = fileName.replace('-meta.xml','')
                apiName = fileName.split('.')[0]
                reportName = apiName
                
                incorrectVFP = checkNomenclatureGeneral(reportName, apiName, incorrectVFP)

            elif  'lwc' in folder:
                if not fileName.split('.')[0].endswith('App'):
                    incorrectLWC.append(fileName)
                else:
                    if fileName.endswith('-meta.xml'):
                        fileName = fileName.replace('-meta.xml','')
                    apiName = fileName.split('.')[0]
                    reportName = apiName
                    
                    checkNomenclatureGeneral(reportName, apiName, incorrectLWC)

            elif 'classes' in folder:
                # Open the file
                classPath = os.path.join(pathToSrc, folder, fileName)
                if not fileName.endswith('-meta.xml'):
                    apiName = fileName.split('.')[0]
                    checkClass(classPath, apiName, validEndingsClasses, incorrectCLS, incorrectTest)
            
            elif 'triggers' in folder:
                if not fileName.endswith('-meta.xml'):
                    apiName = fileName.split('.')[0]
                    if '_' in apiName or not apiName.split('.')[0].endswith('Trigger') or not apiName[0].istitle():
                        incorrectTRG.append(apiName)

            elif 'layouts' in folder:
                pathSrc = os.path.join(pathToSrc, folder, fileName)
                apiName = fileName.split('.')[0]
                reportName = apiName
                checkDescription(pathSrc, reportName, apiName, incorrectDescription)
                    
    data = {
        'Incorrect LWC': incorrectLWC,
        'Incorrect Approval Proccess': incorrectAPR,
        'Incorrect Pages': incorrectVFP,
        'Incorrect Objects' : incorrectOBJ,
        'Incorrect description in component' : incorrectDescription,
        'Incorrect Fields' : incorrectFLD,
        'Incorrect Validation Rules' : incorrectVLR,
        'Incorrect Record Type' : incorrectRTP,
        'Incorrect Classes' : incorrectCLS,
        'Incorrect Tests' : incorrectTest,
        'Incorrect Triggers' : incorrectTRG
    }

    generate_html(data)


def main ():
    try:
        args = parseArgs()                                     
        
        if not os.path.isdir(args.pathToSrc):
            print('[WARNING] Path to src does not exist')
        
        print( 'Checking nomenclature' )
        nomenclatureValidator(args.pathToSrc)
        
    except:
        print ('no se ha podido realizar el estudio de la nomenclatura')



if  __name__ == '__main__':
    main()

