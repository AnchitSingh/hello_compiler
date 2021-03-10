#!/usr/bin/env python3
import ply.lex as lex
import sys
import re

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
    'NOT_EQUAL',
    'GRT',
    'LST',
    'GEQ',
    'LEQ',

    'PLUS',
    'MINUS',
    'MULT',
    'DIVIDE',
    'MODULO',

    'LOGICAL_AND',
    'LOGICAL_OR',
    'LOGICAL_NOT',
    'BITWISE_AND',
    'BITWISE_OR',
    'BITWISE_NOT',
    'BITWISE_XOR',
    'L_SHIFT',
    'R_SHIFT',

    'INCREMENT',
    'DECREMENT',

    'ASSIGN',
    'PLUSEQ',
    'MINUSEQ',
    'MULTEQ',
    'DIVEQ',
    'MODEQ',
    'BITWISE_OREQ',
    'BITWISE_ANDEQ',
    'BITWISE_XOREQ',
    'L_SHIFTEQ',
    'R_SHIFTEQ',

    'STMT_TERMINATOR',
    'COMMA',
    'DOT',
    'QUESTION',
    'COLON',
    'ARROW',
    'HASH',
    'ELLIPSIS',

    'L_PAREN',
    'R_PAREN',
    'BLOCK_OPENER',
    'BLOCK_CLOSER',
    'L_SQBR',
    'R_SQBR',

    'INT_CONSTANT',
    'FLOAT_CONSTANT',
    'ID',
    'STRING'
]+list(reserved.values())

t_EQUALS          = r'=='
t_NOT_EQUAL       = r'!='
t_GRT             = r'>'
t_LST             = r'<'
t_GEQ             = r'>='
t_LEQ             = r'<='

t_PLUS            = r'\+'
t_MINUS           = r'-'
t_MULT            = r'\*'
t_DIVIDE          = r'\/'
t_MODULO          = r'%'

t_LOGICAL_AND     = r'&&'
t_LOGICAL_OR      = r'\|\|'
t_LOGICAL_NOT     = r'!'
t_BITWISE_AND     = r'&'
t_BITWISE_OR      = r'\|'
t_BITWISE_NOT     = r'~'
t_BITWISE_XOR     = r'\^'
t_L_SHIFT         = r'<<'
t_R_SHIFT         = r'>>'

t_INCREMENT       = r'\+\+'
t_DECREMENT       = r'--'

t_ASSIGN          = r'='
t_PLUSEQ          = r'\+='
t_MINUSEQ         = r'-='
t_MULTEQ          = r'\*='
t_DIVEQ           = r'\/='
t_MODEQ           = r'%='
t_BITWISE_OREQ    = r'\|='
t_BITWISE_ANDEQ   = r'&='
t_BITWISE_XOREQ   = r'\^='
t_L_SHIFTEQ       = r'<<='
t_R_SHIFTEQ       = r'>>='

t_STMT_TERMINATOR = r';'
t_COMMA           = r','
t_DOT             = r'\.'
t_QUESTION        = r'\?'
t_COLON           = r':'
t_ARROW           = r'->'
t_HASH			  = r'\#'
t_ELLIPSIS        = r'\.\.\.'

t_L_PAREN         = r'\('
t_R_PAREN         = r'\)'
t_BLOCK_OPENER    = r'{|<%'
t_BLOCK_CLOSER    = r'}|>%'
t_L_SQBR          = r'\[|<:'
t_R_SQBR          = r'\]|>:'

t_STRING          = r'[a-zA-Z_]?\"(\\.|[^\\"])*\"'

t_ignore = ' \t'


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')    # Check for reserved words
    return t


def t_FLOAT_CONSTANT(t):
    r'((\d*\.\d+)|(\d+\.\d*))([Ee][+-]?\d+)?|(\d+[Ee][+-]?\d+)'
    t.value = float(t.value)
    return t


def t_INT_CONSTANT(t):
    r'(0[xX][a-fA-F0-9]+)|0(\d+)|(\d+)|\'(\\.|[^\\\'])\''
    hex = ['0x', '0X']
    if any(x in t.value for x in hex):
        t.value = int(t.value, 16)
    elif(t.value[0] == '0'):
        t.value = int(t.value, 8)
    elif(t.value[0] == '\''):
        t.value = ord(t.value[1])
    else:
        t.value = int(t.value)
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1


def t_INLINE_COMMENT(t):
    r'\/\/.*'
    pass


def t_BLOCK_COMMENT(t):
    r'\/\*[\s\S]*?\*\/'
    t.lexer.lineno += re.findall(r'.*', t.value).count('') - 1
    pass


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex.lex(debug = 0)


def main():
    if(len(sys.argv) == 1 or sys.argv[1] == "-h"):
        print("""Command Usage:
            ./clexer -f code.c -o tokens
    where code.c is the input c file and tokens is the output file with all tokens scanned.""")
        exit()

    if(sys.argv[1] != "-f"):
        print("Error: input the c file using -f option, use -h for more help.")
        exit(-1)
    elif(len(sys.argv) == 2):
        print("Error: pass the c code file as input using -f.")
        exit(-1)
    else:
        c_code = open(sys.argv[2], "r").read()

    lexer.input(c_code)
    template = "{:<20}{:<15}{:<10}{:<10}"
    tokens = []
    tokens.append(template.format("Token", "Lexeme", "Line#", "Column#"))
    for tok in lexer:
        tokens.append(template.format(tok.type, tok.value,
                                      tok.lineno, find_column(c_code, tok)))

    if(len(sys.argv) == 3 or sys.argv[3] != "-o"):
        for tok in tokens:
            print(tok)
    elif(len(sys.argv) == 4):
        print("Error: please pass name of output as argument when using -o option.")
        exit(-1)
    else:
        f = open(sys.argv[4], "w+")
        for tok in tokens:
            f.write(tok + "\n")
        f.close()


if '__main__' == __name__:
    main()
