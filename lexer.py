import ply.lex as lex
import sys

reserved = {
    'auto' : 'AUTO',
    'break' : 'BREAK',
    'case' : 'CASE',
    'char' : 'CHAR',
    'const' : 'CONST',
    'continue' : 'CONTINUE',
    'default' : 'DEFAULT',
    'do' : 'DO',
    'double' : 'DOUBLE',
    'else' : 'ELSE',
    'enum' : 'ENUM',
    'extern' : 'EXTERN',
    'float' : 'FLOAT',
    'for' : 'FOR',
    'goto' : 'GOTO',
    'if' : 'IF',
    'int' : 'INT',
    'long' : 'LONG',
    'register' : 'REGISTER',
    'return' : 'RETURN',
    'short' : 'SHORT',
    'signed' : 'SIGNED',
    'sizeof' : 'SIZEOF',
    'static' : 'STATIC',
    'struct' : 'STRUCT',
    'switch' : 'SWITCH',
    'typedef' : 'TYPEDEF',
    'union' : 'UNION',
    'unsigned' : 'UNSIGNED',
    'void' : 'VOID',
    'volatile' : 'VOLATILE',
    'while' : 'WHILE',
    '_Packed' : '_PACKED',
}

tokens = [
    'EQUALS',
    'ASSIGN',
    'GRT',
    'LST',
    'GEQ',
    'LEQ',
    'PLUS',
    'MINUS',
    'MULT',
    'DIVIDE',
    'LOGICAL_AND',
    'LOGICAL_OR',
    'LOGICAL_NOT',
    'NOT_EQUAL',
    'BITWISE_AND',
    'BITWISE_OR',
    'BITWISE_NOT',
    'BITWISE_XOR',
    'MODULO',
    'INCREMENT',
    'DECREMENT',
    'DOT',
    'PLUSEQ',
    'MINUSEQ',
    'MULTEQ',
    'DIVEQ',
    'MODEQ',
    'STMT_TERMINATOR',
    'COMMA',
    'L_PAREN',
    'R_PAREN',
    'BLOCK_OPENER',
    'BLOCK_CLOSER',
    'L_SQBR',
    'R_SQBR',
    'INT_CONSTANT',
    'FLOAT_CONSTANT',
    'ID',
    'STRING',
    'HASH'
]+list(reserved.values())

t_EQUALS          = r'=='
t_ASSIGN          = r'='
t_GRT             = r'>'
t_LST             = r'<'
t_GEQ             = r'>='
t_LEQ             = r'<='
t_PLUS            = r'\+'
t_MINUS           = r'-'
t_MULT            = r'\*'
t_DIVIDE          = r'\/'
t_LOGICAL_AND     = r'&&'
t_LOGICAL_OR      = r'\|\|'
t_LOGICAL_NOT     = r'!'
t_NOT_EQUAL       = r'!='
t_BITWISE_AND     = r'&'
t_BITWISE_OR      = r'\|'
t_BITWISE_NOT     = r'~'
t_BITWISE_XOR     = r'\^'
t_MODULO          = r'%'
t_INCREMENT       = r'\+\+'
t_DECREMENT       = r'--'
t_DOT             = r'\.'
t_PLUSEQ          = r'\+='
t_MINUSEQ         = r'-='
t_MULTEQ          = r'\*='
t_DIVEQ           = r'\/='
t_MODEQ           = r'%='
t_STMT_TERMINATOR = r';'
t_COMMA           = r','
t_L_PAREN         = r'\('
t_R_PAREN         = r'\)'
t_BLOCK_OPENER    = r'\{'
t_BLOCK_CLOSER    = r'\}'
t_L_SQBR          = r'\['
t_R_SQBR          = r'\]'
t_STRING          = r'"(?:[^\\\n"]|\\.)*"'
t_HASH			  = r'\#'
t_ignore = ' \t'

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value,'ID')    # Check for reserved words
    return t



def t_FLOAT_CONSTANT(t):
    r'-?\d*\.\d+'
    t.value = float(t.value)
    return t

def t_INT_CONSTANT(t):
    r'-?(\d+)'
    t.value = int(t.value)
    return t

def t_INLINE_COMMENT(t):
    r'\/\/.*'
    pass

def t_BLOCK_COMMENT(t):
    r'\/\*[\s\S]*?\*\/'
    pass



def t_newline(t):
    r'\n'
    t.lexer.lineno += len(t.value)


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


def main():
    c_code=open(sys.argv[1],"r").read()
    lexer = lex.lex()
    lexer.input(c_code)
    for tok in lexer:
        print(tok)


if '__main__' == __name__:
    main()
