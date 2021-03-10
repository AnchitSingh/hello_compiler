#!/bin/sh
make clean
make
mkdir lexer-output

for t in test/*.c; do
    table=$(echo $t | cut -d '/' -f2- | sed 's/\.[^.]*$//')
    ./bin/lexer -f $t -o lexer-output/$table.out
done
