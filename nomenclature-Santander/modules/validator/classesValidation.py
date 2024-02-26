

def checkClass(classPath, apiName, validEndingsClasses, incorrectCLS, incorrectTest):
    
    try:
        
        with open(classPath, 'r', encoding='UTF8') as file:
            # Read the file content
            content = file.read()
            # Check if '@isTest' or '@IsTest' is in the content
            if '@isTest' in content or '@IsTest' in content:
                # If the file name does not end with 'Test', add it to the incorrectTest list
                if not apiName.split('.')[0].endswith('Test') or '_' in apiName or not apiName[0].istitle():
                    incorrectTest.append(apiName)
            else:
                # If the file name does not end with any of the valid endings, add it to the incorrectCls list
                if not any(apiName.split('.')[0].endswith(ending) for ending in validEndingsClasses) or '_' in apiName or not apiName[0].istitle():
                    incorrectCLS.append(apiName)
        
        return incorrectTest, incorrectCLS
        
    except:
        print(f'Error while read new file {apiName}')
