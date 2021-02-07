all:
		rm -rf bin
		mkdir bin
		cp src/clexer.py bin/clexer
		chmod u+x bin/clexer

clean:
		rm -rf bin
		rm -rf lexer-output
