# hello_compiler
**SOURCE LANGUAGE**: *C*


**IMPLEMENTATION LANGUAGE**: *Python*


**TARGET LANGUAGE**: *x86*


Requirements:

-python3
-ply module (pip3 install ply)


### Milestone 1
Command to run lexer:

-python3 src/lexer.py -f test.c -o tokens.out


### Milestone 2
Command to run parser:

-python3 src/parser.py -f test.c -o AST.dot


Using executable:

1. make
2. ./bin/lexer -f test/test1.c -o tokens.out
3. ./bin/parser -f test/test1.c -o graph.dot


Alternate usage to run all test cases:

1. chmod u+x lexer.sh
2. chmod u+x parser.sh
3. ./lexer.sh
4. ./parser.sh
