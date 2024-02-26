import argparse

def parseArgs():

    parser = argparse.ArgumentParser()

    parser.add_argument( '-p', '--pathToSrc', required=True, help='Path to metadata' )
    parser.add_argument( '-d', '--pathToDescribe', required=False, help='Path to describe' )
    parser.add_argument( '-l', '--prefixList', nargs='+', required=False, help='All possible project prefixes separated by spaces' )
    args = parser.parse_args()

    return args