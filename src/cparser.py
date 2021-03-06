#!/usr/bin/env python3

import sys
import os
import ply.yacc as yacc
from clexer import tokens
from clexer import lexer


index = 0


def flatten(l):
    for el in l:
        if type(el) is list and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def add_to_tree(p, node_label=None):
    global index
    global f

    p = list(flatten(p))

    if(node_label == None):
        node_label = (sys._getframe(1).f_code.co_name)[2:]
    index = index + 1
    parent_id = index
    # create a non-terminal node for current node
    f.write(
        "\n\t" + str(index) + " [label = \"" + node_label + "\"]")
    # add children
    for i in range(1, len(p)):
        if(type(p[i]) is not tuple):
            index = index + 1
            # create a terminal node if child is not node already
            f.write("\n\t" + str(index) +
                    " [label = \"" + str(p[i]).replace('"', "") + "\"]")
            p[i] = (p[i], index)

        # add edge from current node to child node
        f.write(
            "\n\t" + str(parent_id) + " -> " + str(p[i][1]))

    return (node_label, parent_id)


start = 'translation_unit'


def p_primary_expression(p):
    '''primary_expression : ID
                          | INT_CONSTANT
                          | FLOAT_CONSTANT
                          | STRING
                          | L_PAREN expression R_PAREN'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[2]])


def p_postfix_expression(p):
    '''postfix_expression : primary_expression
                          | postfix_expression L_SQBR expression R_SQBR
                          | postfix_expression L_PAREN R_PAREN
                          | postfix_expression L_PAREN argument_expression_list R_PAREN
                          | postfix_expression DOT ID
                          | postfix_expression ARROW ID
                          | postfix_expression INCREMENT
                          | postfix_expression DECREMENT'''
    if(len(p) == 2):
        p[0] = p[1]
    elif(len(p) == 3):
        p[0] = add_to_tree(p)
    elif(p[2] == '['):
        p[0] = add_to_tree([p[0], p[1], p[3]], "[]")
    elif(p[2] == '.' or p[2] == '->'):
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])
    elif(p[3] == ')'):
        p[0] = add_to_tree([p[0]], p[1] + "()")
    elif(p[4] == ')'):
        p[0] = add_to_tree([p[0], p[3]], p[1] + "()")


def p_argument_expression_list(p):
    '''argument_expression_list : assignment_expression
                                | argument_expression_list COMMA assignment_expression'''
    if(len(p) == 2):
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[3])


def p_unary_expression(p):
    '''unary_expression : postfix_expression
                        | INCREMENT unary_expression
                        | DECREMENT unary_expression
                        | unary_operator cast_expression
                        | SIZEOF unary_expression
                        | SIZEOF L_PAREN type_name R_PAREN'''
    if(len(p) == 2):
        p[0] = p[1]
    elif(p[2] == '('):
        p[0] = add_to_tree([p[0], p[3]], "sizeof")
    elif(p[1] == 'sizeof'):
        p[0] = add_to_tree([p[0], p[2]], "sizeof")
    else:
        p[0] = add_to_tree([p[0], p[2]], p[1])


def p_unary_operator(p):
    '''unary_operator : BITWISE_AND
                      | MULT
                      | PLUS
                      | MINUS
                      | BITWISE_NOT
                      | LOGICAL_NOT'''
    p[0] = p[1]


def p_cast_expression(p):
    '''cast_expression : unary_expression
                       | L_PAREN type_name R_PAREN cast_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[2], p[4]])


def p_multiplicative_expression(p):
    '''multiplicative_expression : cast_expression
                                 | multiplicative_expression MULT cast_expression
                                 | multiplicative_expression DIVIDE cast_expression
                                 | multiplicative_expression MODULO cast_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_additive_expression(p):
    '''additive_expression : multiplicative_expression
                           | additive_expression PLUS multiplicative_expression
                           | additive_expression MINUS multiplicative_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_shift_expression(p):
    '''shift_expression : additive_expression
                        | shift_expression L_SHIFT additive_expression
                        | shift_expression R_SHIFT additive_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_relational_expression(p):
    '''relational_expression : shift_expression
                             | relational_expression LST shift_expression
                             | relational_expression GRT shift_expression
                             | relational_expression LEQ shift_expression
                             | relational_expression GEQ shift_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_equality_expression(p):
    '''equality_expression : relational_expression
                           | equality_expression EQUALS relational_expression
                           | equality_expression NOT_EQUAL relational_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_and_expression(p):
    '''and_expression : equality_expression
                      | and_expression BITWISE_AND equality_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_exclusive_or_expression(p):
    '''exclusive_or_expression : and_expression
                               | exclusive_or_expression BITWISE_XOR and_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_inclusive_or_expression(p):
    '''inclusive_or_expression : exclusive_or_expression
                               | inclusive_or_expression BITWISE_OR exclusive_or_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_logical_and_expression(p):
    '''logical_and_expression : inclusive_or_expression
                              | logical_and_expression LOGICAL_AND inclusive_or_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_logical_or_expression(p):
    '''logical_or_expression : logical_and_expression
                             | logical_or_expression LOGICAL_OR logical_and_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_conditional_expression(p):
    '''conditional_expression : logical_or_expression
                              | logical_or_expression QUESTION expression COLON conditional_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        t1 = add_to_tree([None, p[1]], "condition")
        t2 = add_to_tree([None, p[3]], "true")
        t3 = add_to_tree([None, p[5]], "false")
        p[0] = add_to_tree([p[0], t1, t2, t3], p[2] + p[4])


def p_assignment_expression(p):
    '''assignment_expression : conditional_expression
                             | unary_expression assignment_operator assignment_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_assignment_operator(p):
    '''assignment_operator : ASSIGN
                           | MULTEQ
                           | DIVEQ
                           | MODEQ
                           | PLUSEQ
                           | MINUSEQ
                           | L_SHIFTEQ
                           | R_SHIFTEQ
                           | BITWISE_ANDEQ
                           | BITWISE_XOREQ
                           | BITWISE_OREQ'''
    p[0] = p[1]


def p_expression(p):
    '''expression : assignment_expression
                  | expression COMMA assignment_expression'''
    if(len(p) == 2):
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[3])


def p_constant_expression(p):
    '''constant_expression : conditional_expression'''
    p[0] = p[1]


def p_declaration(p):
    '''declaration : declaration_specifiers STMT_TERMINATOR
                   | declaration_specifiers init_declarator_list STMT_TERMINATOR'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_declaration_specifiers(p):
    '''declaration_specifiers : storage_class_specifier
                              | storage_class_specifier declaration_specifiers
                              | type_specifier
                              | type_specifier declaration_specifiers
                              | type_qualifier
                              | type_qualifier declaration_specifiers'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_init_declarator_list(p):
    '''init_declarator_list : init_declarator
                            | init_declarator_list COMMA init_declarator'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_init_declarator(p):
    '''init_declarator : declarator
                       | declarator ASSIGN initializer'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_storage_class_specifier(p):
    '''storage_class_specifier : TYPEDEF
                               | EXTERN
                               | STATIC
                               | AUTO
                               | REGISTER'''
    p[0] = p[1]


def p_type_specifier(p):
    '''type_specifier : VOID
                      | CHAR
                      | SHORT
                      | INT
                      | LONG
                      | FLOAT
                      | DOUBLE
                      | SIGNED
                      | UNSIGNED
                      | struct_or_union_specifier
                      | enum_specifier'''
    p[0] = p[1]


def p_struct_or_union_specifier(p):
    '''struct_or_union_specifier : struct_or_union ID BLOCK_OPENER struct_declaration_list BLOCK_CLOSER
                                 | struct_or_union BLOCK_OPENER struct_declaration_list BLOCK_CLOSER
                                 | struct_or_union ID'''
    if(len(p) == 6):
        t = add_to_tree([None, p[4]], "members_list")
        p[0] = add_to_tree([p[0], p[2], t], p[1])
    elif(len(p) == 5):
        t = add_to_tree([None, p[3]], "members_list")
        p[0] = add_to_tree([p[0], t], p[1])
    else:
        p[0] = add_to_tree([p[0], p[2]], p[1])


def p_struct_or_union(p):
    '''struct_or_union : STRUCT
                       | UNION'''
    p[0] = p[1]


def p_struct_declaration_list(p):
    '''struct_declaration_list : struct_declaration
                               | struct_declaration_list struct_declaration'''
    if(len(p) == 2):
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[2])


def p_struct_declaration(p):
    '''struct_declaration : specifier_qualifier_list struct_declarator_list STMT_TERMINATOR'''
    p[0] = add_to_tree([p[0], p[1], p[2]])


def p_specifier_qualifier_list(p):
    '''specifier_qualifier_list : type_specifier specifier_qualifier_list
                                | type_specifier
                                | type_qualifier specifier_qualifier_list
                                | type_qualifier'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_struct_declarator_list(p):
    '''struct_declarator_list : struct_declarator
                              | struct_declarator_list COMMA struct_declarator'''
    if(len(p) == 2):
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[3])


def p_struct_declarator(p):
    '''struct_declarator : declarator
                         | COLON constant_expression
                         | declarator COLON constant_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_enum_specifier(p):
    '''enum_specifier : ENUM BLOCK_OPENER enumerator_list BLOCK_CLOSER
                      | ENUM ID BLOCK_OPENER enumerator_list BLOCK_CLOSER
                      | ENUM ID'''
    if(len(p) == 5):
        t = add_to_tree([None, p[3]], "members_list")
        p[0] = add_to_tree([p[0], t], p[1])
    elif(len(p) == 6):
        t = add_to_tree([None, p[4]], "members_list")
        p[0] = add_to_tree([p[0], p[2], t], p[1])
    else:
        p[0] = add_to_tree([p[0], p[2]], p[1])


def p_enumerator_list(p):
    '''enumerator_list : enumerator
                       | enumerator_list COMMA enumerator'''
    if(len(p) == 2):
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[3])


def p_enumerator(p):
    '''enumerator : ID
                  | ID ASSIGN constant_expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree([p[0], p[1], p[3]], p[2])


def p_type_qualifier(p):
    '''type_qualifier : CONST
                      | VOLATILE'''
    p[0] = p[1]


def p_declarator(p):
    '''declarator : pointer direct_declarator
                  | direct_declarator'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_direct_decalarator(p):
    '''direct_declarator : ID
                         | L_PAREN declarator R_PAREN
                         | direct_declarator L_SQBR constant_expression R_SQBR
                         | direct_declarator L_SQBR R_SQBR
                         | direct_declarator L_PAREN parameter_type_list R_PAREN
                         | direct_declarator L_PAREN identifier_list R_PAREN
                         | direct_declarator L_PAREN R_PAREN'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_pointer(p):
    '''pointer : MULT
               | MULT type_qualifier_list
               | MULT pointer
               | MULT type_qualifier_list pointer'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_type_qualifier_list(p):
    '''type_qualifier_list : type_qualifier
                           | type_qualifier_list type_qualifier'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_parameter_type_list(p):
    '''parameter_type_list : parameter_list
                           | parameter_list COMMA ELLIPSIS'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_parameter_list(p):
    '''parameter_list : parameter_declaration
                      | parameter_list COMMA parameter_declaration'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_parameter_declaration(p):
    '''parameter_declaration : declaration_specifiers declarator
                             | declaration_specifiers abstract_declarator
                             | declaration_specifiers'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_identifier_list(p):
    '''identifier_list : ID
                       | identifier_list COMMA ID'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_type_name(p):
    '''type_name : specifier_qualifier_list
                 | specifier_qualifier_list abstract_declarator'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_abstract_declarator(p):
    '''abstract_declarator : pointer
                           | direct_abstract_declarator
                           | pointer direct_abstract_declarator'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_direct_abstract_declarator(p):
    '''direct_abstract_declarator : L_PAREN abstract_declarator R_PAREN
                                  | L_SQBR R_SQBR
                                  | L_SQBR constant_expression R_SQBR
                                  | direct_abstract_declarator L_SQBR R_SQBR
                                  | direct_abstract_declarator L_SQBR constant_expression R_SQBR
                                  | L_PAREN R_PAREN
                                  | L_PAREN parameter_type_list R_PAREN
                                  | direct_abstract_declarator L_PAREN R_PAREN
                                  | direct_abstract_declarator L_PAREN parameter_type_list R_PAREN'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_initializer(p):
    '''initializer : assignment_expression
                   | BLOCK_OPENER initializer_list BLOCK_CLOSER
                   | BLOCK_OPENER initializer_list COMMA BLOCK_CLOSER'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_initializer_list(p):
    '''initializer_list : initializer
                        | initializer_list COMMA initializer'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_statement(p):
    '''statement : labeled_statement
                 | compound_statement
                 | expression_statement
                 | selection_statement
                 | iteration_statement
                 | jump_statement'''
    p[0] = p[1]


def p_labeled_statement(p):
    '''labeled_statement : ID COLON statement
                         | CASE constant_expression COLON statement
                         | DEFAULT COLON statement'''
    if(len(p) == 5):
        p[0] = add_to_tree([p[0], p[4]], p[1] + ' ' + str(p[2]))
    elif(p[1] == 'default'):
        p[0] = add_to_tree([p[0], p[3]], p[1])
    else:
        p[0] = add_to_tree(p)


def p_compound_statement(p):
    '''compound_statement : BLOCK_OPENER BLOCK_CLOSER
                          | BLOCK_OPENER statement_list BLOCK_CLOSER
                          | BLOCK_OPENER declaration_list BLOCK_CLOSER
                          | BLOCK_OPENER declaration_list statement_list BLOCK_CLOSER'''
    if(len(p) == 4):
        p[0] = add_to_tree([p[0], p[2]])
    elif(len(p) == 5):
        p[0] = add_to_tree([p[0], p[2], p[3]])


def p_declaration_list(p):
    '''declaration_list : declaration
                        | declaration_list declaration'''
    if(len(p) == 2):
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[2])


def p_statement_list(p):
    '''statement_list : statement
                      | statement_list statement'''
    if(len(p) == 2):
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[2])


def p_expression_statement(p):
    '''expression_statement : STMT_TERMINATOR
                            | expression STMT_TERMINATOR'''
    if(len(p) == 3):
        p[0] = p[1]


def p_selection_statement(p):
    '''selection_statement : IF L_PAREN expression R_PAREN statement
                           | IF L_PAREN expression R_PAREN statement ELSE statement
                           | SWITCH L_PAREN expression R_PAREN statement'''
    if(len(p) == 6):
        t1 = add_to_tree([None, p[3]], "condition")
        t2 = add_to_tree([None, p[5]], "body")
        p[0] = add_to_tree([p[0], t1, t2], p[1])
    else:
        t1 = add_to_tree([None, p[3]], "condition")
        t2 = add_to_tree([None, p[5]], "body")
        t3 = add_to_tree([None, p[7]], "else-body")
        p[0] = add_to_tree([p[0], t1, t2, t3], p[1] + p[6])


def p_iteration_statement(p):
    '''iteration_statement : WHILE L_PAREN expression R_PAREN statement
                           | DO statement WHILE L_PAREN expression R_PAREN STMT_TERMINATOR
                           | FOR L_PAREN expression_statement expression_statement R_PAREN statement
                           | FOR L_PAREN expression_statement expression_statement expression R_PAREN statement'''
    if(len(p) == 6):
        t1 = add_to_tree([None, p[3]], "condition")
        t2 = add_to_tree([None, p[5]], "body")
        p[0] = add_to_tree([p[0], t1, t2], p[1])
    elif(len(p) == 8 and p[1] == 'do'):
        t1 = add_to_tree([None, p[5]], "condition")
        t2 = add_to_tree([None, p[2]], "body")
        p[0] = add_to_tree([p[0], t1, t2], p[1] + '-' + p[3])
    elif(len(p) == 7):
        t1 = add_to_tree([None, p[3]], "initialisation")
        t2 = add_to_tree([None, p[4]], "stop condition")
        t3 = add_to_tree([None, p[6]], "body")
        p[0] = add_to_tree([p[0], t1, t2, t3], p[1])
    else:
        t1 = add_to_tree([None, p[3]], "initialisation")
        t2 = add_to_tree([None, p[4]], "stop condition")
        t2 = add_to_tree([None, p[5]], "update")
        t4 = add_to_tree([None, p[7]], "body")
        p[0] = add_to_tree([p[0], t1, t2, t3, t4], p[1])


def p_jump_statement(p):
    '''jump_statement : GOTO ID STMT_TERMINATOR
                      | CONTINUE STMT_TERMINATOR
                      | BREAK STMT_TERMINATOR
                      | RETURN STMT_TERMINATOR
                      | RETURN expression STMT_TERMINATOR'''
    if(len(p) == 3):
        p[0] = add_to_tree([p[0]], p[1])
    else:
        p[0] = add_to_tree([p[0], p[2]], p[1])


def p_translation_unit(p):
    '''translation_unit : external_declaration
                        | translation_unit external_declaration'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


def p_external_declaration(p):
    '''external_declaration : function_definition
                            | declaration'''
    p[0] = p[1]


def p_function_definition(p):
    '''function_definition : declaration_specifiers declarator declaration_list compound_statement
                           | declaration_specifiers declarator compound_statement
                           | declarator declaration_list compound_statement
                           | declarator compound_statement'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = add_to_tree(p)


# Error rule for syntax errors
def p_error(p):
    print(p)
    print("Syntax error in input!")


def p_empty(p):
    'empty :'
    pass


def main():
    if(len(sys.argv) == 1 or sys.argv[1] == "-h"):
        print("""Command Usage:
            python3 cparser.py -f code.c -o myAST.dot
        where code.c is the input c file and myAST.dot is the output file with AST tree specifications.""")
        exit()

    parser = yacc.yacc()
    parser.error = 0

    global f
    if(len(sys.argv) == 5 and sys.argv[3] == "-o"):
        f = open(sys.argv[4], "w+")
    else:
        f = open("graph.dot", "w+")
    f.write("digraph ast {")

    if(sys.argv[1] == "-f" and len(sys.argv) == 3):
        c_code = open(sys.argv[2], 'r').read()
        p = parser.parse(c_code, lexer=lexer)
    else:
        while True:
            try:
                s = input('$ > ')
            except EOFError:
                break
            if not s:
                continue
            p = parser.parse(s)
    f.write("\n}\n")


if '__main__' == __name__:
    main()
