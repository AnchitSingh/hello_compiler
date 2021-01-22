import ply.lex as lex

tokens = (
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
    'L_SHIFT',
    'R_SHIFT',
    'LSHIFTEQ',
    'RSHIFTEQ',
    'COLON',
    'QUESTION',
    'AUTO',
    'BREAK',
    'CASE',
    'CHAR',
    'CONST',
    'CONTINUE',
    'DEFAULT',
    'DO',
    'DOUBLE',
    'ELSE',
    'ENUM',
    'EXTERN',
    'FLOAT',
    'FOR',
    'GOTO',
    'IF',
    'INT',
    'LONG',
    'REGISTER',
    'RETURN',
    'SHORT',
    'SIGNED',
    'SIZEOF',
    'STATIC',
    'STRUCT',
    'SWITCH',
    'TYPEDEF',
    'UNION',
    'UNSIGNED',
    'VOID',
    'VOLATILE',
    'WHILE',
    'ELLIPSIS',
    'RIGHT_ASSIGN',
    'LEFT_ASSIGN',
    'ADD_ASSIGN',
    'SUB_ASSIGN',
    'MUL_ASSIGN',
    'DIV_ASSIGN',
    'MOD_ASSIGN',
    'AND_ASSIGN',
    'XOR_ASSIGN',
    'OR_ASSIGN',
    'RIGHT_OP',
    'LEFT_OP',
    'INC_OP',
    'DEC_OP',
    'PTR_OP',
    'AND_OP',
    'OR_OP',
    'LE_OP',
    'GE_OP',
    'EQ_OP',
    'NE_OP',
    'STMT_TERMINATOR',
    'COMMA',
    'L_PAREN',
    'R_PAREN',
    'BLOCK_OPENER',
    'BLOCK_CLOSER',
    'L_SQBR',
    'R_SQBR',
    'IDENTIFIER',
    'INT_CONSTANT',
    'FLOAT_CONSTANT',
    'CHAR_CONSTANT',
    'STR_CONSTANT',
    'INLINE_COMMENT',
    'BLOCK_COMMENT',
    'LAMBDA_TOKEN',
    'BREAK',
    'BYTE',
    'CASE',
    'CATCH',
    'CLASS',
    'CONST',
    'CONTINUE',
    'DEFAULT',
    'DO',
    'ELSE',
    'ENUM',
    'EXTENDS',
    'FINAL',
    'FINALLY',
    'FOR',
    'IF',
    'IMPLEMENTS',
    'IMPORT',
    'INSTANCEOF',
    'INTERFACE',
    'NEW',
    'PACKAGE',
    'RETURN',
    'STATIC',
    'SUPER',
    'SWITCH',
    'THIS',
    'THROW',
    'THROWS',
    'TRY',
    'WHILE',
    'NULL',
    'LAMBDA' 
)
 
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_ignore  = ' \t'

def t_INLINE_COMMENT(t):
    r'\/\*(.*)(\n+.*)*\*\/'
    pass

def t_BLOCK_COMMENT(t):
    r'\/\/.*'
    pass



def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)    
    return t

def t_newline(t):
    r'\n'
    t.lexer.lineno += len(t.value)


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()