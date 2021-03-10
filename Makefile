all:
		rm -rf bin
		mkdir bin
		cp src/clexer.py bin/clexer
		cp src/cparser.py bin/cparser
		chmod u+x bin/clexer
		chmod u+x bin/cparser

clean:
		rm -rf bin
		rm -rf lexer-output
		rm -rf parser-output
		rm -rf AST
