#!/bin/bash
QUERY_OUTPUT="./securityChecker/resources/query_output/"
USERNAME=$1
PATH_TO_SRC=$2
OUTPUT=$3
PMD=$4
echo "ARG USN: $USERNAME"
echo "ARG SRC: $PATH_TO_SRC"
echo "ARG OUT: $OUTPUT"
echo "ARG PMD: $PMD"
if [ -z "$1" ]
  then
    echo "ARGUMENT 1 - Username missing"
    exit 1
fi
if [ -z "$2" ]
  then
    echo "ARGUMENT 2 - Path to SRC missing"
    exit 1
fi
if [ -z "$3" ]
  then
    echo "ARGUMENT 3 - outputReport missing"
    exit 1
fi
if [ -z "$4" ]
  then
    echo "ARGUMENT 3 - outputReport missing"
    exit 1
fi

echo "---- Running Security Checker ----"
echo "[x] Running SFDX query"
echo "[x] output will be stored in $QUERY_OUTPUT"
sfdx data export tree --json -d $QUERY_OUTPUT -u $USERNAME --query "SELECT Assignee.Name, PermissionSet.Name FROM PermissionSetAssignment ORDER BY PermissionSet.Name" > /dev/null
# sfdx force:data:soql:query -u $USERNAME -q "SELECT Assignee.Name, PermissionSet.Name FROM PermissionSetAssignment ORDER BY PermissionSet.Name" --json>$QUERYOUTPUT
echo "[x] Running SecurityScanner"

python3 securityScanner.py -p $PATH_TO_SRC -r $OUTPUT -pmd $PMD
STATUS=$?
[ $STATUS -eq 0 ] && echo "[X]SecurityScanner command was successful" || echo "[X]SecurityScanner failed"