import ply.lex as lex

class HelloLexer():
    
    def __init__(self):
        pass

def t_COMMENT(t):
     r'\/\*(.*)(\n+.*)*\*\/'
     pass