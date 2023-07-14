import argparse

def parseArgs():

	parser = argparse.ArgumentParser()
	
	parser.add_argument( '-p', '--pathToSrc', required=True, help='Path to metadata' )
	parser.add_argument( '-r', '--reportPath', required=True, help='Path to save report' )
	parser.add_argument( '-pmd', '--pathToPmdReport', help='Path to PMD report' )
	args = parser.parse_args()

	return args