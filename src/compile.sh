#!/bin/bash

if [[ "$#" != "1" ]];
then
    echo "Give c code file args $#"
    exit -1
fi

python3 parser.py $1
if [[ "$?" == "0" ]];then
    python3 codegen.py
else
    exit -1
fi

if [[ "$?" == "0" ]];then
    gcc asmfile.s ../lib/printstr.s -m32 -no-pie -o exec.out
else
    exit -1
fi
