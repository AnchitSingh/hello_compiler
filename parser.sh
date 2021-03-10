#!/bin/sh
make clean
make
mkdir parser-output
mkdir AST

for t in test/*.c; do
    table=$(echo $t | cut -d '/' -f2- | sed 's/\.[^.]*$//')
    ./bin/parser -f $t -o parser-output/graph$table.dot
    dot -Tps parser-output/graph$table.dot -o AST/graph$table.ps
done
