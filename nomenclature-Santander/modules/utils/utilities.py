import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader



def checkDescription(pathSrc,reportName, apiName, withoutDescription):
    try:
        
        tree = ET.parse(pathSrc)
        root = tree.getroot()
        description = root.find('{http://soap.sforce.com/2006/04/metadata}description')
        if description is None:
            withoutDescription.append(apiName)
                    
        else:
            description_text = description.text  # Obtenemos el texto del tag 'description'
            if description_text is  None:
                withoutDescription.append(reportName)
        
        return withoutDescription
        
    except:
        print(f'Error while read new file {apiName}')


def checkNomenclatureGeneral(fileName, apiName, incorrectName):
    # Check extension (name.extension-meta.xml or name.extension)
    #fileName = deleteExtension(fileName)
    #apiName = deleteExtension(apiName)

    if '_' in apiName or not apiName[0].istitle():
        incorrectName.append(fileName)
        
    return incorrectName


def deleteExtension(fileName):
    if fileName.endswith('-meta.xml'):
        fileName = fileName.replace('-meta.xml', '')

    fileNameEnding = '.' + fileName.split('.')[-1]
    fileName = fileName.replace(fileNameEnding, '')

    return fileName

def generate_html(data):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    output = template.render(data=data)
    with open('output.html', 'w') as f:
        f.write(output)

