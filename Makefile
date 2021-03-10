all:
		rm -rf bin
		mkdir bin
		cp src/lexer.py bin/lexer
		cp src/parser.py bin/parser
		chmod u+x bin/lexer
		chmod u+x bin/parser

clean:
		rm -rf bin
		rm -rf lexer-output
		rm -rf parser-output
		rm -rf AST
