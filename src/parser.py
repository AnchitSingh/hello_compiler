import sys
import os
import re
import pickle

from ply import yacc
from lexer import tokens, lexer


node_id = 0


def flatten(l):
    for el in l:
        if type(el) is list and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def toParse(p):
    for ep in p:
        if isinstance(ep, NODE):
            yield ep.parse
        else:
            yield ep


def add_to_tree(p, node_label=None):
    global node_id
    global f

    p = list(toParse(p))
    p = list(flatten(p))

    if(node_label == None):
        node_label = (sys._getframe(1).f_code.co_name)[2:]
    node_id = node_id + 1
    parent_id = node_id
    # create a non-terminal node for current node
    f.write(
        "\n\t" + str(node_id) + " [label = \"" + node_label + "\"]")
    # add children
    for i in range(1, len(p)):
        if(p[i] is not None):
            if(type(p[i]) is not tuple):
                node_id = node_id + 1
                # create a terminal node if child is not node already
                f.write("\n\t" + str(node_id) +
                        " [label = \"" + str(p[i]).replace('"', "") + "\"]")
                p[i] = (p[i], node_id)

            # add edge from current node to child node
            f.write(
                "\n\t" + str(parent_id) + " -> " + str(p[i][1]))

    if len(p) > 2:
        f.write(
            "\n{\nrank = same;\n")
        for i in range(1, len(p) - 1):
            if p[i] is not None:
                f.write(
                    str(p[i][1]) + " -> ")
        if(p[-1:][0] is not None):
            f.write(str(p[-1:][0][1]))
        f.write(
            " [style = invis];\nrankdir = LR;\n}")

    return (node_label, parent_id)


class SymbolTable:
    def __init__(self, parent=None):
        self.table = {}
        self.parent = parent

    def lookUp(self, name):
        return (name in self.table)

    def insert(self, name, value):
        if (not self.lookUp(name)):
            (self.table)[name] = value
            return True
        else:
            return False

    def update(self, name, value):
        (self.table)[name] = value
        return True

    def getDetail(self, name):
        if(self.lookUp(name)):
            return self.table[name]
        else:
            return None


filename = None

scopeTables = []
currentScopeId = 0
globalScopeTable = SymbolTable()
scopeTables.append(globalScopeTable)

offsets = [0]
offsetPId = [None]
currentOffset = 0

tmpId = 0
gblCount = 0
labelId = {}

structs = []


def pushScope():
    global scopeTables
    global currentScopeId
    newScope = SymbolTable(parent=currentScopeId)
    scopeTables.append(newScope)
    currentScopeId = len(scopeTables) - 1


def popScope():
    global scopeTables
    global currentScopeId
    currentScopeId = scopeTables[currentScopeId].parent


def getParentScope(scopeId):
    global scopeTables
    if(scopeId < len(scopeTables)):
        return scopeTables[scopeId].parent
    else:
        return False


def pushEntry(identifier, data, scope=None):
    global scopeTables
    global currentScopeId
    global gblCount

    if isinstance(identifier, dict) and currentScopeId == 0 and "size" in identifier.keys() and "offset" in identifier.keys() and "base" in identifier.keys():
        identifier["offset"] = "gbl@" + str(gblCount)
        gblCount = gblCount + 1

    if isinstance(identifier, dict) and "base" in identifier.keys():
        identifier["base"] = str(identifier["base"])

    if scope is None:
        scope = currentScopeId

    if checkEntry(identifier, scope)[0]:
        return False
    else:
        scopeTables[scope].insert(identifier, data)
        return True


def updateEntry(identifier, data, scope=None):
    global scopeTables
    global currentScopeId

    if scope is None:
        scope = currentScopeId

    scopeTables[scope].update(identifier, data)


def checkEntry(identifier, scope=None):
    global scopeTables
    global currentScopeId

    if scope is None:
        scope = currentScopeId
        while(scope is not None):
            res, scp = checkEntry(identifier, scope)
            if res is not False:
                return (res, scp)
            scope = scopeTables[scope].parent
        return (False, scope)

    symtab = scopeTables[scope]
    if symtab.lookUp(identifier):
        return (symtab.getDetail(identifier), scope)
    return (False, scope)


def getOffset():
    global offsets
    global currentOffset
    return offsets[currentOffset]


def addToOffset(val):
    global offsets
    global currentOffset

    offsets[currentOffset] = offsets[currentOffset] + val


def pushOffset():
    global offsets
    global currentOffset
    global offsetPId
    newOffset = 0
    offsets.append(newOffset)
    offsetPId.append(currentOffset)
    currentOffset = len(offsets) - 1


def popOffset():
    global offsets
    global currentOffset
    global offsetPId
    currentOffset = offsetPId[currentOffset]


def setData(p, x):
    if isinstance(p[x].data, str) or isinstance(p[x].data, int) or isinstance(p[x].data, float):
        return p[x].data
    else:
        return p[x].data.copy()


def getSize(type_):
    size = {"void": 0, "char": 1, "int": 4, "float": 4}
    if(type_[-1] == '*'):
        return 4
    elif type_ in size.keys():
        return size[type_]
    else:
        struct_info, scp = checkEntry(type_, 0)
        if struct_info ==  False:
            print(" Error :: " + type_ + " | Struct is not defined")
            exit()
        return struct_info["size"]

#--------------------------FUNCTIONS FOR 3AC-----------------------------------#

def getNewLabel(lb="label"):
    labelId[lb] = labelId[lb] + 1 if lb in labelId.keys() else 0
    label = lb + "#" + str(labelId[lb])
    return label


def getNewTmp(type_, offset=None, size=None, base="rbp"):
    global tmpId
    tmp = "tmp@" + str(tmpId)
    tmpId = tmpId + 1

    if offset == None:
        addToOffset(getSize(type_))
        offset = getOffset()

    data = {"type": type_, "class": "tmp", "size": size, "offset": offset, "base": str(base)}
    pushEntry(tmp, data)

    return tmp


def quadGen(op, arg_, code=None):
    global currentScopeId

    arg = [ str(arg_[i]) if i < len(arg_) else "" for i in range(3) ]
    if code == None:
        code = str(op) + " " + arg[0] + " " + arg[1] + " " + arg[2]
    return " $ ".join([code]+[op] + arg + [str(currentScopeId)])


class NODE:
    def __init__(self):
        self.data = {}
        self.code = []
        self.place = None

    def __str__(self):
        return (str(self.data) + str(self.place))


start = 'program'


def p_program(p):
    '''program : translation_unit'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    p[0].parse = add_to_tree(p)
    for i in range(len(p)):
        p[0].code = p[0].code + p[i].code.copy()
    for i in p[0].code:
        if re.fullmatch('[ ]*break', i) != None:
            print("Error :: " + "break should be inside for/do-while/while/switch-case")
            exit()
        elif re.fullmatch('[ ]*continue', i) != None:
            print("Error :: " + "continue should be inside for/do-while/while")
            exit()

    global filename
    cfile = open("3AC.code", 'w')
    cod = []
    for i in p[0].code:
        if re.fullmatch('[ ]*', i) == None:
            cod.append(i)

    cfile.write("// Code For " + filename + "\n")
    x = 1
    for i in cod:
        cfile.write('{0:3}'.format(x) + "::" + i.split('$')[0] + "\n")
        x = x + 1
    x = 1
    for i in cod:
        cfile.write('{0:3}'.format(x) + "::" + i + "\n")
        x = x + 1

    bin3ac = open("3AC.obj", "wb")
    pickle.dump(cod, bin3ac)


def p_primary_expression_0(p):
    '''primary_expression : INT_CONSTANT
                          | CHAR_CONSTANT
                          | FLOAT_CONSTANT
                          | STRING'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1):
                p_.data = p[i]
            p[i] = p_
    
    p[0].parse = p[1].parse
    p[0].data = {"type": None, "class": "basic", "value": p[1].data, "name": None}
    if isinstance(p[1].data, int):
        p[0].data["type"] = "int"

    elif isinstance(p[1].data, str) and p[1].data[0] == '\'':
        p[0].data["type"] = "char"

    elif isinstance(p[1].data, float):
        p[0].data["type"] = "float"

    elif isinstance(p[1].data, str) and p[1].data[0] == '"':
        p[0].data["type"] = "char*"

    p[0].place = getNewTmp(p[0].data["type"])
    p[0].code = [ quadGen( "=", [ p[0].place, str(p[0].data["value"]) ], p[0].place + " = " + str(p[0].data["value"]) ) ]


def p_primary_expression_1(p):
    '''primary_expression : ID'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1):
                p_.data = p[i]
            p[i] = p_
    
    p[0].parse = p[1].parse
    
    res, scp = checkEntry(p[1].data)
    if(res == False):
        print("Error at line : " + str(p.lineno(1)) + " :: " + p[1].data + " | Identifier is not declared")
        exit()
    p[0].data = res.copy()

    p[0].place = p[1].data + "@" + str(scp)


def p_primary_expression_2(p):
    '''primary_expression : L_PAREN expression R_PAREN'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    
    p[0].parse = p[2].parse
    p[0].data = setData(p, 2)

    p[0].place = p[2].place
    p[0].code = p[2].code.copy()


# distinguish static array from pointer

def p_postfix_expression_0(p):
    '''postfix_expression : primary_expression
                          | postfix_expression L_SQBR expression R_SQBR'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()

    elif(p[2].parse == '['):
        p[0].parse = add_to_tree([p[0], p[1], p[3]], "[]")
        allowed_type = ["char", "int"]
        if p[3].data["type"] not in allowed_type:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  p[1].data["name"] + " | Array index is not integer")
            exit()
        if p[1].data["type"][-1] != '*':
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  p[1].data["name"] + " | Type is not an array or pointer")
            exit()
        p[0].data["type"] = p[1].data["type"][:-1]
        p[0].data["class"] = "basic"


def p_postfix_expression_1(p):
    '''postfix_expression : postfix_expression DOT ID
                          | postfix_expression ARROW ID
                          | postfix_expression INCREMENT
                          | postfix_expression DECREMENT'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    
    if(len(p) == 3):
        p[0].parse = [p[1].parse, p[2].parse]
        
        if p[1].data["type"] not in ["char", "int", "float"] and p[1].data["type"][-1] != '*':
            print("Error at line : " + str(p.lineno(1)) + " :: " + p[1].data["name"] + " | Type not compatible with increment/decrement operation")
            exit()
        p[0].data["type"] = p[1].data["type"]

        p[0].place = getNewTmp(p[0].data["type"])
        p[0].code = p[1].code + [ quadGen( "=", [ p[0].place, p[1].place ], p[0].place + " = " + p[1].place ) ] + [ quadGen( p[2].parse, [ p[1].place ], p[1].place + p[2].parse ) ]

    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        
        if p[1].data["class"] not in ["struct", "union"]:
            print("Error at line : " + str(p.lineno(1)) + " :: " + p[1].data["name"] + " | Identifier used is not a struct/union class")
            exit()
        if(p[2].parse == "->" and p[1].data["type"][-1] != '*'):
            print("Error at line : " + str(p.lineno(1)) + " :: " + p[1].data["name"] + " | Identifier used is not a struct pointer")
            exit()
        
        res, scp = checkEntry(p[1].data["type"][:-1] if p[1].data["type"][-1] == '*' else p[1].data["type"], 0)
        res_, scp_ = checkEntry(p[3].parse, res["members_scope"])
        if(res_ == False):
            print("Error at line : " + str(p.lineno(3)) + " :: " + p[3].parse + " | Identifier used is not in struct member list of " + p[1].data["name"])
            exit()
        p[0].data = res_.copy()
        
        tmp_var = getNewTmp("void*")
        if p[2].parse == '.' and str(p[1].data["base"]) == "rbp":
            base = "rbp"
            op = "-"
        else:
            base = "0"
            op = "+"
        p[0].data["offset"] = tmp_var
        p[0].data["base"] = base
        
        p[0].place = getNewTmp(res_["type"], tmp_var, res_["size"], base)
        p[0].code = p[1].code + [ quadGen( op, [ tmp_var, p[1].data["offset"], p[1].data["size"] - res_["offset"] ] ) ]


def p_postfix_expression_2(p):
    '''postfix_expression : postfix_expression L_PAREN R_PAREN
                          | postfix_expression L_PAREN argument_expression_list R_PAREN'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    
    p[0].parse = add_to_tree([p[0]] if len(p) == 4 else [p[0], p[3]], p[1].parse + "()")
    if p[1].data["class"] != "function":
        print("Error at line : " + str(p.lineno(2)) + " :: " + p[1].data["name"] + " | Identifier is not a function type")
        exit()
    if(p[1].data["definition"] == False):
        print("Error at line : " + str(p.lineno(2)) + " :: " + p[1].data["name"] + " | Function is not defined only declared")
        exit()
    p[0].data["type"] = p[1].data["ret_type"]

    input_list = p[1].data["input_type"].split(',')
    arg_list = p[3].data if len(p) == 5 else [ ]
    if(len(input_list) != len(arg_list)):
        print("Error at line : " + str(p.lineno(2)) + " :: " + p[1].data["name"] + " | Number of function arguments does not match")
        exit()
    
    tmp_code = [ ]
    if(len(p) == 5):
        for i in range(len(input_list)):
            if(input_list[i] != arg_list[i]["type"]):
                print("Error at line : " + str(p.lineno(2)) + " :: " + p[1].data["name"] + " | Type mismatch in function arguments")
                exit()
        tmp_code = tmp_code + p[3].code
        for arg in p[3].place:
            tmp_code.append( quadGen( "pushParam", [ arg ], "PushParam " + arg ) )

    p[0].place = getNewTmp(p[0].data["type"])
    p[0].code = p[1].code + tmp_code + [ quadGen( "Fcall", [ p[0].place, p[1].data["label"] ], p[0].place + " = " + "Fcall " + p[1].data["name"] ) ] + [ quadGen( "removeParams", [ str(p[1].data["parameter_space"]) ], "RemoveParams " + str(p[1].data["parameter_space"]) ) ]


def p_argument_expression_list(p):
    '''argument_expression_list : assignment_expression
                                | argument_expression_list COMMA assignment_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = [p[1].parse]
        p[0].data = [setData(p, 1)]

        p[0].place = [p[1].place]
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = p[1].parse
        p[0].parse.append(p[3].parse)
        p[0].data = p[1].data
        p[0].data.append(setData(p, 3))

        p[0].place = [p[3].place] + p[1].place
        p[0].code = p[1].code + p[3].code


def p_unary_expression_0(p):
    '''unary_expression : postfix_expression
                        | INCREMENT unary_expression
                        | DECREMENT unary_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        if p[2].data["type"] not in ["char", "int", "float"] and p[2].data["type"][-1] != '*':
            print("Error at line : " + str(p.lineno(2)) + " :: " + p[2].data["name"] + " | Type not compatible with unary increment/decrement operation")
            exit()
        p[0].data["type"] = p[2].data["type"]

        p[0].place = p[2].place
        p[0].code = p[2].code + [ quadGen( p[1].parse, [ p[2].place ], p[2].place + p[1].parse ) ]


def p_unary_expression_1(p):
    '''unary_expression : unary_operator cast_expression
                        | SIZEOF unary_expression
                        | SIZEOF L_PAREN type_name R_PAREN'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_

    if(p[1].parse == "sizeof"):
        p[0].parse = add_to_tree([p[0], p[2] if len(p) == 3 else p[3]], "sizeof")
        p[0].data["type"] = "int"

        p[0].place = getNewTmp("int")
        if len(p) == 3:
            res, scp = checkEntry(p[2].place)
            p[0].code = p[2].code + [ quadGen( "=", [ p[0].place, str(res["size"]) ], p[0].place + " = " + str(res["size"]) ) ]
        else:
            p[0].code = p[3].code + [ quadGen( "=", [ p[0].place, str(getSize(p[3].data["type"])) ], p[0].place + " = " + str(getSize(p[3].data["type"])) ) ]
    else:
        p[0].parse = add_to_tree([p[0], p[2]], p[1].parse)
        p[0].data = setData(p, 2)
        
        if(p[1].data == '&'):
            p[0].data["type"] = p[2].data["type"] + '*'

            p[0].place = getNewTmp(p[0].data["type"])
            p[0].code = p[2].code + [ quadGen( "lea", [ p[0].place, p[2].place ], p[0].place + " = & " + p[2].place ) ]
        elif(p[1].data == '*'):
            if p[2].data["type"][-1] != '*':
                print("Error at line : " + str(p.lineno(2)) + " :: " + p[2].data["name"] + " | Error dereferencing non-pointer variable")
                exit()
            p[0].data["type"] = p[2].data["type"][:-1]

            p[0].place = getNewTmp(p[0].data["type"], p[2].place, getSize(p[0].data["type"]), "0")
            p[0].code = p[2].code.copy()
        elif(p[1].data == '!'):
            p[0].data["type"] = "int"

            p[0].place = getNewTmp("int")
            p[0].code = p[2].code + [ quadGen( p[1].data, [ p[0].place, p[2].place ], p[0].place + " = " + p[1].data + " " + p[2].place ) ]
        else:
            if p[2].data["type"] not in ["char", "int", "float"]:
                print("Error at line : " + str(p.lineno(2)) + " :: " + p[2].data["name"] + " | Type not compatible with unary operator")
                exit()
            p[0].data["type"] = p[2].data["type"]

            if(p[1].data == '~'):
                p[0].place = getNewTmp(p[0].data["type"])
                p[0].code = p[2].code + [ quadGen( p[1].data, [ p[0].place, p[2].place ], p[0].place + " = " + p[1].data + " " + p[2].place ) ]
            elif(p[1].data == '+'):
                p[0].place = p[2].place
                p[0].code = p[2].code.copy()
            else:
                p[0].place = getNewTmp(p[0].data["type"])
                p[0].code = p[2].code + [ quadGen( "*", [ p[0].place, "-1", p[2].place ], p[0].place + " = " + " -1 * " + p[2].place ) ]


def p_unary_operator(p):
    '''unary_operator : BITWISE_AND
                      | MULT
                      | PLUS
                      | MINUS
                      | BITWISE_NOT
                      | LOGICAL_NOT'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1):
                p_.data = p[i]
            p[i] = p_
    p[0].parse = p[1].parse
    p[0].data = p[1].data


def p_cast_expression(p):
    '''cast_expression : unary_expression
                       | L_PAREN type_name R_PAREN cast_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = add_to_tree([p[0], p[2], p[4]])
        if(p[2].data["type"] not in ["char", "int", "float"] or p[4].data["type"] not in ["char", "int", "float"]):
            print("Error at line : " + str(p.lineno(4)) + " :: " + p[2].data["type"] + ", " + p[4].data["type"] + " | Type cast not allowed for given data type")
            exit()
        p[0].data = setData(p, 4)
        p[0].data["type"] = p[2].data["type"]

        p[0].place = getNewTmp(p[0].data["type"])
        p[0].code = p[4].code + p[2].code + [ quadGen( p[4].data["type"] + "_to_" + p[2].data["type"], [ p[0].place, p[4].place ], p[0].place + " = " + p[4].data["type"] + "_to_" + p[2].data["type"] + "( " + p[4].place + " )" ) ]


def p_multiplicative_expression(p):
    '''multiplicative_expression : cast_expression
                                 | multiplicative_expression MULT cast_expression
                                 | multiplicative_expression DIVIDE cast_expression
                                 | multiplicative_expression MODULO cast_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()

    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)

        if(p[1].data["type"] != p[3].data["type"]):
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type mismatch in two operands of multiple/divide/modulo operation")
            exit()

        if(p[2].data == '%'):
            if p[1].data["type"] != "int" or p[3].data["type"] != "int":
                print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with modulo operation")
                exit()
        else:
            if p[1].data["type"] not in ["char", "int", "float"] or p[3].data["type"] not in ["char", "int", "float"]:
                print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with multiply/divide operation")
                exit()
        p[0].data["type"] = p[1].data["type"]

        p[0].place = getNewTmp(p[0].data["type"])
        p[0].code = p[1].code + p[3].code + [ quadGen( p[2].data, [ p[0].place, p[1].place, p[3].place ] ) ]


def p_additive_expression(p):
    '''additive_expression : multiplicative_expression
                           | additive_expression PLUS multiplicative_expression
                           | additive_expression MINUS multiplicative_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        if(p[1].data["type"][-1] == '*'):
            if(p[3].data["type"] != "int"):
                print("Error at line : " + str(p.lineno(1)) + " :: " + "Type incompatible for pointer with add/subtract operation")
                exit()
            p[0].data["type"] = p[1].data["type"]

            tmp = getNewTmp(p[3].data["type"])
            tmp_code = [ quadGen( "*", [ tmp, p[3].place, str(getSize(p[1].data["type"][:-1])) ] ) ]
            p[0].place = getNewTmp(p[1].data["type"])
            p[0].code = p[1].code + p[3].code + tmp_code + [ quadGen( p[2].data, [ p[0].place, p[1].place, tmp ] ) ]
        else:
            if(p[1].data["type"] != p[3].data["type"]):
                print("Error at line : " + str(p.lineno(1)) + " :: " + "Type mismatch in two operands of add/subtract operation")
                exit()

            if p[1].data["type"] not in ["char", "int", "float"] or p[3].data["type"] not in ["char", "int", "float"]:
                print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with add/subtract operation")
                exit()

            p[0].data["type"] = p[1].data["type"]
            p[0].place = getNewTmp(p[0].data["type"])
            p[0].code = p[1].code + p[3].code + [ quadGen( p[2].data, [ p[0].place, p[1].place, p[3].place ] ) ]


def p_shift_expression(p):
    '''shift_expression : additive_expression
                        | shift_expression L_SHIFT additive_expression
                        | shift_expression R_SHIFT additive_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        if p[1].data["type"] not in ["char", "int", "float"] or p[3].data["type"] != "int":
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with bitwise shift operation")
            exit()
        p[0].data["type"] = p[1].data["type"]

        p[0].place = getNewTmp(p[0].data["type"])
        p[0].code = p[1].code + p[3].code + [ quadGen( p[2].data, [ p[0].place, p[1].place, p[3].place ] ) ]


def p_relational_expression(p):
    '''relational_expression : shift_expression
                             | relational_expression LST shift_expression
                             | relational_expression GRT shift_expression
                             | relational_expression LEQ shift_expression
                             | relational_expression GEQ shift_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        if(p[1].data["type"] != p[3].data["type"]):
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type mismatch in two operands of relational operation")
            exit()
        if p[1].data["type"] not in ["char", "int", "float"] or p[3].data["type"] not in ["char", "int", "float"]:
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with relational operation")
            exit()
        p[0].data["type"] = "int"

        p[0].place = getNewTmp("int")
        p[0].code = p[1].code + p[3].code + [ quadGen( p[2].data, [ p[0].place, p[1].place, p[3].place ] ) ]


def p_equality_expression(p):
    '''equality_expression : relational_expression
                           | equality_expression EQUALS relational_expression
                           | equality_expression NOT_EQUAL relational_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()

    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        if(p[1].data["type"] != p[3].data["type"]):
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type mismatch in two operands of equality operation")
            exit()
        if p[1].data["type"] not in ["char", "int", "float"] or p[3].data["type"] not in ["char", "int", "float"]:
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with equality operation")
            exit()
        p[0].data["type"] = "int"

        p[0].place = getNewTmp("int")
        p[0].code = p[1].code + p[3].code + [ quadGen( p[2].data, [ p[0].place, p[1].place, p[3].place ] ) ]


def p_and_expression(p):
    '''and_expression : equality_expression
                      | and_expression BITWISE_AND equality_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()

    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        if(p[1].data["type"] != p[3].data["type"]):
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type mismatch in two operands of bitwise and operation")
            exit()
        if p[1].data["type"] not in ["char", "int"] or p[3].data["type"] not in ["char", "int"]:
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with bitwise and operation")
            exit()
        p[0].data["type"] = p[1].data["type"]

        p[0].place = getNewTmp(p[0].data["type"])
        p[0].code = p[1].code + p[3].code + [ quadGen( p[2].data, [ p[0].place, p[1].place, p[3].place ] ) ]


def p_exclusive_or_expression(p):
    '''exclusive_or_expression : and_expression
                               | exclusive_or_expression BITWISE_XOR and_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        if(p[1].data["type"] != p[3].data["type"]):
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type mismatch in two operands of bitwise xor operation")
            exit()
        if p[1].data["type"] not in ["char", "int"] or p[3].data["type"] not in ["char", "int"]:
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with bitwise xor operation")
            exit()
        p[0].data["type"] = p[1].data["type"]

        p[0].place = getNewTmp(p[0].data["type"])
        p[0].code = p[1].code + p[3].code + [ quadGen( p[2].data, [ p[0].place, p[1].place, p[3].place ] ) ]


def p_inclusive_or_expression(p):
    '''inclusive_or_expression : exclusive_or_expression
                               | inclusive_or_expression BITWISE_OR exclusive_or_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        if(p[1].data["type"] != p[3].data["type"]):
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type mismatch in two operands of bitwise or operation")
            exit()
        if p[1].data["type"] not in ["char", "int"] or p[3].data["type"] not in ["char", "int"]:
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with bitwise or operation")
            exit()
        p[0].data["type"] = p[1].data["type"]

        p[0].place = getNewTmp(p[0].data["type"])
        p[0].code = p[1].code + p[3].code + [ quadGen( p[2].data, [ p[0].place, p[1].place, p[3].place ] ) ]


def p_logical_and_expression(p):
    '''logical_and_expression : inclusive_or_expression
                              | logical_and_expression LOGICAL_AND inclusive_or_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        if(p[1].data["type"] != p[3].data["type"]):
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type mismatch in two operands of logical and operation")
            exit()
        if p[1].data["type"] not in ["char", "int", "float"] or p[3].data["type"] not in ["char", "int", "float"]:
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with logical and operation")
            exit()
        p[0].data["type"] = "int"

        p[0].place = getNewTmp("int")
        p[0].code = p[1].code + p[3].code + [ quadGen( p[2].data, [ p[0].place, p[1].place, p[3].place ] ) ]


def p_logical_or_expression(p):
    '''logical_or_expression : logical_and_expression
                             | logical_or_expression LOGICAL_OR logical_and_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()

    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        if(p[1].data["type"] != p[3].data["type"]):
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type mismatch in two operands of logical or operation")
            exit()
        if p[1].data["type"] not in ["char", "int", "float"] or p[3].data["type"] not in ["char", "int", "float"]:
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with logical or operation")
            exit()
        p[0].data["type"] = "int"

        p[0].place = getNewTmp("int")
        p[0].code = p[1].code + p[3].code + [ quadGen( p[2].data, [ p[0].place, p[1].place, p[3].place ] ) ]


def p_conditional_expression(p):
    '''conditional_expression : logical_or_expression
                              | logical_or_expression QUESTION expression COLON conditional_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3], p[5]], p[2].parse + p[4].parse)
        if p[1].data["type"] not in ["char", "int", "float"]:
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with ternary operation")
            exit()
        if p[3].data["type"] != p[5].data["type"]:
            print("Error at line : " + str(p.lineno(3)) + " :: " + "Type mismatch with ternary operation")
            exit()

        tmp_code = [ ]
        if p[1].data["type"] != "int":
            tmp_var = getNewTmp("int")
            tmp_code = tmp_code + [ quadGen( p[1].data["type"] + "_to_int", [ tmp_var, p[1].place ], tmp_var + " = " + p[1].data["type"] + "_to_int" + "( " + p[1].place + " )" ) ]
        p[0].data["type"] = p[3].data["type"]
        p[0].place = getNewTmp(p[0].data["type"])
        p[0].else_ = getNewLabel("else_part")
        p[0].after = getNewLabel("after")
        p[0].code = p[1].code + tmp_code + [ quadGen( "ifz", [ p[1].place, p[0].else_ ], "ifz " + p[1].place + " goto->" + p[0].else_ ) ] + p[3].code + [ quadGen( "goto", [ p[0].after ], "goto->" + p[0].after ) ] + [ quadGen( "label", [ p[0].else_ ], p[0].else_ + ":" ) ] +  p[5].code + [ quadGen( "label", [ p[0].after ], p[0].after + ":" ) ]


# type checking handling

def p_assignment_expression(p):
    '''assignment_expression : conditional_expression
                             | unary_expression assignment_operator assignment_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        if(p[1].data["type"] != p[3].data["type"]):
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type mismatch in two operands of assignment operation")
            exit()
        if p[1].data["type"] not in ["char", "int", "float", "char*", "int*", "float*"] or p[3].data["type"] not in ["char", "int", "float", "char*", "int*", "float*"]:
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Type not compatible with assignment operation")
            exit()
        p[0].data["type"] = p[1].data["type"]
        
        tmp_code = [ ]
        if(len(p[2].data) != 1):
            tmp_var = getNewTmp(p[1].data["type"])
            tmp_code = tmp_code + [ quadGen( p[2].data[:-1], [ tmp_var, p[1].place, p[3].place ] ) ]
        
        tmp_code = tmp_code + [ quadGen( p[2].data[-1], [ p[1].place, p[3].place if len(p[2].data) == 1 else tmp_var ], p[1].place + " = " + p[3].place if len(p[2].data) == 1 else tmp_var ) ]
        p[0].code = p[3].code + p[1].code + tmp_code


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
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1):
                p_.data = p[i]
            p[i] = p_
    p[0].parse = p[1].parse
    p[0].data = setData(p, 1)


# come back later

def p_expression(p):
    '''expression : assignment_expression
                  | expression COMMA assignment_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = [p[1].parse]
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = p[1].parse
        p[0].parse.append(p[3].parse)

        p[0].place = p[1].place
        p[0].code = p[1].code + p[3].code


def p_constant_expression(p):
    '''constant_expression : conditional_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    p[0].parse = p[1].parse
    p[0].data = setData(p, 1)

    p[0].place = p[1].place
    p[0].code = p[1].code.copy()


def p_declaration(p):
    '''declaration : declaration_specifiers STMT_TERMINATOR
                   | declaration_specifiers init_declarator_list STMT_TERMINATOR
                   | declaration_specifiers declarator L_PAREN func_push_scope parameter_type_list R_PAREN pop_scope STMT_TERMINATOR'''
    global currentScopeId
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    
    if len(p) == 3:
        p[0].parse = p[1].parse
    elif(len(p) == 4):
        p[0].parse = []
        for t in p[2].parse:
            if(t[0] == '='):
                p[0].parse.append(t)
        
        p[0].code = p[2].code.copy()
        for decl in p[2].data:
            data = setData(p, 1)
            data["type"] = data["type"] + decl["type"]
            if(data["type"] == "void" or data["type"][:-1] == "void"):
                print("Error at line : " + str(p.lineno(1)) + " :: " + data["name"] + " | Can not declare void type variable")
                exit()
            if("init_type" in decl.keys()):
                if decl["init_type"] != data["type"]:
                    print("Error at line : " + str(p.lineno(1)) + " :: " + "Incompatible type initialisation")
                    exit()
            
            data["name"] = decl["name"]
            if "meta" in decl.keys():
                data["meta"] = decl["meta"]

            if len(data["meta"]) != 0:
                data["is_array"] = 1
                data["element_type"] = data["type"][:-1]
                data["index"] = 1
                data["to_add"] = "0"

                arr_size = 1
                for dim in data["meta"]:
                    arr_size = arr_size * dim

                data["size"] = getSize(data["element_type"]) * arr_size
                addToOffset(data["size"])
                if currentScopeId == 0:
                    data["offset"] = getOffset() - data["size"]  
                    data["base"] = "0"
                else:
                    data["offset"] = getOffset()
                    data["base"] = "rbp"
                
                res = pushEntry(decl["name"], data)
                if(res == False):
                    addToOffset(-data["size"])
                    print("Error at line : " + str(p.lineno(0)) + " :: " + decl["name"] + " | Redeclaration of variable")
                    exit()
            else:
                data["size"] = getSize(data["type"])
                addToOffset(data["size"])
                if currentScopeId == 0:
                    data["offset"] = getOffset() - data["size"]  
                    data["base"] = "0"
                else:
                    data["offset"] = getOffset()
                    data["base"] = "rbp"
                
                res = pushEntry(decl["name"], data)
                if(res == False):
                    print("Error at line : " + str(p.lineno(0)) + " :: " +
                        decl["name"] + " | Redeclaration of variable")
                    exit()

                if "init_type" in decl.keys():
                    p[0].code = p[0].code + [ quadGen( "=", [ decl["name"] + "@" + str(currentScopeId), decl["place"] ] ) ]
    else:
        popOffset()


def p_declaration_specifiers(p):
    '''declaration_specifiers : type_specifier
                              | type_specifier declaration_specifiers'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = [p[1].parse]
        p[0].data = setData(p, 1)
    else:
        p[0].parse = p[2].parse
        p[0].parse.insert(0, p[1].parse)

        print("Error at line : " + str(p.lineno(1)) + " :: " + "Did not handle decl specifier with multiple type specifiers")
        exit()


def p_init_declarator_list(p):
    '''init_declarator_list : init_declarator
                            | init_declarator_list COMMA init_declarator'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = [p[1].parse]
        p[0].data = [setData(p, 1)]

        p[0].code = p[1].code.copy()
    else:
        p[0].parse = p[1].parse
        p[0].parse.append(p[3].parse)
        p[0].data = setData(p, 1)
        p[0].data.append(setData(p, 3))

        p[0].code = p[1].code + p[3].code


def p_init_declarator(p):
    '''init_declarator : declarator
                       | declarator ASSIGN initializer'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    p[0].data = setData(p, 1)
    if(len(p) == 2):
        p[0].parse = p[1].parse
    else:
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        p[0].data["init_type"] = p[3].data["type"]

        p[0].data["place"] = p[3].place
        p[0].code = p[3].code.copy()


def p_type_specifier_0(p):
    '''type_specifier : VOID
                      | CHAR
                      | INT
                      | FLOAT'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1):
                p_.data = p[i]
            p[i] = p_
    p[0].parse = p[1].parse
    p[0].data = {"type": p[1].data, "class": "basic"}


def p_type_specifier_1(p):
    '''type_specifier : struct_or_union_specifier'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    p[0].parse = p[1].parse
    p[0].data = setData(p, 1)


def p_struct_or_union_specifier(p):
    '''struct_or_union_specifier : struct_or_union ID BLOCK_OPENER struct_push_scope struct_declaration_list pop_scope BLOCK_CLOSER
                                 | struct_or_union ID'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 8):
        p[0].data = {"type": p[2].data, "class": p[1].data}
        p[0].data["members_scope"] = p[5].scope
        p[0].data["size"] = getOffset()
        res = pushEntry(p[2].data, p[0].data)
        if(res == False):
            print("Error at line : " + str(p.lineno(2)) + " :: " + p[2].data + " | Redefinition of struct variable")
            exit()

        popOffset()
    else:
        p[0].parse = [p[1].parse, p[2].parse]
        
        res, scp = checkEntry(p[2].data, 0)
        if(res == False):
            if(p[2].data not in structs):
                print("Error at line : " + str(p.lineno(2)) + " :: " + p[2].data + " | Struct identifier is not defined")
                exit()
            else:
                res = {"type": p[2].data, "class": p[1].data}
        p[0].data = res


def p_struct_or_union(p):
    '''struct_or_union : STRUCT
                       | UNION'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1):
                p_.data = p[i]
            p[i] = p_
    p[0].parse = p[1].parse
    p[0].data = setData(p, 1)


def p_struct_declaration_list(p):
    '''struct_declaration_list : struct_declaration
                               | struct_declaration_list struct_declaration'''
    global currentScopeId
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].data = [setData(p, 1)]
    else:
        p[0].data = setData(p, 1)
        p[0].data.append(setData(p, 2))
    
    p[0].scope = currentScopeId


def p_struct_declaration(p):
    '''struct_declaration : specifier_qualifier_list struct_declarator_list STMT_TERMINATOR'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    for decl in p[2].data:
        data = setData(p, 1)
        data["type"] = data["type"] + decl["type"]
        if(data["type"] == "void" or data["type"][:-1] == "void"):
            print("Error at line : " + str(p.lineno(1)) + " :: " + data["name"] + " | Can not declare void type variable")
            exit()
        
        data["name"] = decl["name"]
        if("meta" in decl.keys()):
            data["meta"] = decl["meta"]

        if len(data["meta"]) != 0:
            data["is_array"] = 1
            data["element_type"] = data["type"][:-1]
            data["index"] = 1
            data["to_add"] = "0"

            arr_size = 1
            for dim in data["meta"]:
                arr_size = arr_size * dim

            data["size"] = getSize(data["element_type"]) * arr_size
            addToOffset(data["size"])
            data["offset"] = getOffset()
            data["base"] = "rbp"
                
            res = pushEntry(decl["name"], data)
            if(res == False):
                addToOffset(-data["size"])
                print("Error at line : " + str(p.lineno(2)) + " :: " + decl["name"] + " | Redeclaration of variable")
                exit()
        else:
            if(data["class"] in ["struct", "union"] and data["type"] == structs[-1]):
                print("Error at line : " + str(p.lineno(1)) + " :: " + data["type"] + " | Can not declare recursive struct")
                exit()
            data["size"] = getSize(data["type"])
            addToOffset(data["size"])
            data["offset"] = getOffset()
            data["base"] = "rbp"
            res = pushEntry(decl["name"], data)
            if(res == False):
                print("Error at line : " + str(p.lineno(2)) + " :: " + decl["name"] + " | Redeclaration of variable")
                exit()


def p_specifier_qualifier_list(p):
    '''specifier_qualifier_list : type_specifier specifier_qualifier_list
                                | type_specifier'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = [p[1].parse]
        p[0].data = setData(p, 1)
    else:
        p[0].parse = p[2].parse
        p[0].parse.insert(0, p[1].parse)

        print("Error at line : " + str(p.lineno(1)) + " :: " + "Did not handle specifier qualifier list with multiple type specifiers")
        exit()


def p_struct_declarator_list(p):
    '''struct_declarator_list : struct_declarator
                              | struct_declarator_list COMMA struct_declarator'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].data = [setData(p, 1)]
    else:
        p[0].data = setData(p, 1)
        p[0].data.append(setData(p, 3))


def p_struct_declarator(p):
    '''struct_declarator : declarator'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    p[0].data = setData(p, 1)


def p_declarator(p):
    '''declarator : pointer direct_declarator
                  | direct_declarator'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)
    else:
        p[0].parse = [p[1].parse, p[2].parse]
        p[0].data = setData(p, 2)
        p[0].data["type"] = p[2].data["type"] + p[1].data


def p_direct_decalarator(p):
    '''direct_declarator : ID
                         | L_PAREN declarator R_PAREN
                         | direct_declarator L_SQBR INT_CONSTANT R_SQBR
                         | direct_declarator L_SQBR R_SQBR'''
    global currentScopeId
    
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 2 and i == 1):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse

        res, scp = checkEntry(p[1].data, currentScopeId)
        if(res is not False):
            print("Error at line : " + str(p.lineno(1)) + " :: " + p[1].data + " | Identifier is already declared in same scope")
            exit()
        p[0].data = {"name": setData(p, 1), "type": "", "meta": []}

        p[0].place = p[1].data + "@" + str(scp)
    elif(p[2].parse == '['):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)
        p[0].data["type"] = p[1].data["type"] + '*'
        p[0].data["meta"] = p[1].data["meta"] + [p[3].parse] if len(p) == 5 else [1]
    else:
        p[0].parse = p[2].parse
        p[0].data = setData(p, 2)

        p[0].place = p[2].place
        p[0].code = p[2].code


def p_pointer(p):
    '''pointer : MULT
               | MULT pointer'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = [p[1].parse]
        p[0].data = setData(p, 1)
    else:
        p[0].parse = p[2].parse
        p[0].parse.insert(0, p[1].parse)
        p[0].data = p[1].data + p[2].data

        print("Error at line : " + str(p.lineno(1)) + " :: " + "Did not handle multiple pointer")
        exit()


def p_parameter_type_list(p):
    '''parameter_type_list : parameter_list
                           | '''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse

    f_name = p[-3].data["name"]
    ret_type = p[-4].data["type"] + p[-3].data["type"]
    offset = - 8
    input_type = ""
    
    if len(p) == 2:
        for arg in p[1].data:
            if(input_type == ""):
                input_type = arg["type"]
            else:
                input_type = input_type + ',' + arg["type"]
            
            if "is_array" in arg.keys():
                arg["base"] = "0"
                arg["offset"] = getNewTmp("int", offset, 4)
                offset = offset - 4
                updateEntry(arg["name"], arg)
            else:
                arg["offset"] = offset
                arg["base"] = "rbp"
                offset = offset - arg["size"]
                updateEntry(arg["name"], arg)
    parent = getParentScope(currentScopeId)
    res, scp = checkEntry(f_name, parent)
    if res is False:
        label = "main" if f_name == "main" else getNewLabel("func")
    else:
        label = res["label"]

    p[0].data = {
        "name" : f_name, "type" : "function", "class" : "function", "ret_type" : ret_type, "input_type" : input_type,
        "label" : label, "func_scope" : currentScopeId, "definition": False, "stack_space" : getOffset(),
        "parameter_space": (-offset - 8), "saved_register_space" : 40 , "return_offset" : 4, "rbp_offset" : 0,
    }

    scopeTables[currentScopeId].type_ = "function"

    if res is False:
        pushEntry(f_name, p[0].data, parent)
    else:
        # this function name is seen but may be overloaded
        print("Error at line : " + str(p.lineno(1)) + " :: " + f_name + " | Function may be overloaded")
        exit()


def p_parameter_list(p):
    '''parameter_list : parameter_declaration
                      | parameter_list COMMA parameter_declaration'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = [p[1].parse]
        p[0].data = [setData(p, 1)]
    else:
        p[0].parse = p[1].parse
        p[0].parse.append(p[3].parse)
        p[0].data = setData(p, 1)
        p[0].data.append(setData(p, 3))


def p_parameter_declaration(p):
    '''parameter_declaration : declaration_specifiers declarator'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    p[0].parse = list(toParse(p[1:]))
    decl = setData(p, 2)
    data = setData(p, 1)
    if(data["type"] in ["void", "void*"]):
            print("Error at line : " + str(p.lineno(1)) + " :: " + "Can not declare void type variable in parameter")
            exit()

    data["type"] = data["type"] + decl["type"]
    data["name"] = decl["name"]
    if("meta" in decl.keys()):
        data["meta"] = decl["meta"]
    
    if len(data["meta"]) != 0:
        data["is_array"] = 1
        data["element_type"] = data["type"][:-1]
        data["index"] = 1
        data["to_add"] = "0"

        arr_size = 1
        for dim in data["meta"]:
            arr_size = arr_size * dim

        data["size"] = getSize(data["element_type"]) * arr_size
        addToOffset(data["size"])
        data["offset"] = getOffset()
        
        res = pushEntry(decl["name"], data)
        if(res == False):
            addToOffset(-data["size"])
            print("Error at line : " + str(p.lineno(2)) + " :: " + decl["name"] + " | Redeclaration of variable")
            exit()
    else:
        data["size"] = getSize(data["type"])
        res = pushEntry(decl["name"], data)
        if(res == False):
            print("Error at line : " + str(p.lineno(2)) + " :: " + "Redeclaration of variable")
            exit()
    p[0].data = data


def p_type_name(p):
    '''type_name : specifier_qualifier_list
                 | specifier_qualifier_list pointer'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    p[0].parse = add_to_tree(p)
    p[0].data = setData(p, 1)
    if(len(p) == 3):
        p[0].data["type"] = p[1].data["type"] + p[2].data
        if("meta" in p[2].data.keys()):
            p[0].data["meta"] = p[2].data["meta"]
    else:
        p[0].data["meta"] = []


def p_initializer(p):
    '''initializer : assignment_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()


def p_initializer_list(p):
    '''initializer_list : initializer
                        | initializer_list COMMA initializer'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = [p[1].parse]
        p[0].data = [setData(p, 1)]

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = p[1].parse
        p[0].parse.append(p[3].parse)
        p[0].data = setData(p, 1)
        p[0].data.append(setData(p, 3))

        p[0].place = p[1].place
        p[0].code = p[1].code + p[3].code


def p_statement(p):
    '''statement : labeled_statement
                 | compound_statement
                 | expression_statement
                 | selection_statement
                 | iteration_statement
                 | jump_statement'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)
        
        p[0].place = p[1].place
        p[0].code = p[1].code.copy()


def p_labeled_statement(p):
    '''labeled_statement : CASE INT_CONSTANT COLON statement
                         | DEFAULT COLON statement'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    label = getNewLabel()
    if(len(p) == 5):
        p[0].parse = add_to_tree([p[0], p[4]], p[1].parse + ' ' + str(p[2].parse))
        p[0].data = setData(p, 4)
        
        p[0].code = {"class": "case", "type": "int", "value": p[2].parse, "statement": p[4].code, "label": label, "lineno": p.lineno(1)}
    elif(p[1].parse == 'default'):
        p[0].parse = add_to_tree([p[0], p[3]], p[1].parse)
        p[0].data = setData(p, 3)
        
        p[0].code = {"class": "default", "type": None, "value": None, "statement": p[3].code, "label": label, "lineno": p.lineno(1)}
    # else:
    #     p[0].parse = add_to_tree(p)
    #     p[0].data = setData(p, 3)


def p_compound_statement(p):
    '''compound_statement : BLOCK_OPENER BLOCK_CLOSER
                          | BLOCK_OPENER statement_list BLOCK_CLOSER
                          | BLOCK_OPENER declaration_list BLOCK_CLOSER
                          | BLOCK_OPENER declaration_list statement_list BLOCK_CLOSER'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 4):
        p[0].parse = [p[2].parse]
        p[0].data = setData(p, 2)
        
        p[0].place = p[2].place
        p[0].code = p[2].code.copy()
    elif(len(p) == 5):
        p[0].parse = [p[2].parse, p[3].parse]
        p[0].data = setData(p, 3)
        
        p[0].place = p[3].place
        p[0].code = p[2].code + p[3].code


def p_declaration_list(p):
    '''declaration_list : declaration
                        | declaration_list declaration'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = [p[1].parse]
        p[0].data = [setData(p, 1)]
        
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = p[1].parse
        p[0].parse.append(p[2].parse)
        p[0].data = setData(p, 1)
        p[0].data.append(setData(p, 2))
        
        p[0].code = p[1].code + p[2].code


def p_statement_list(p):
    '''statement_list : statement
                      | statement_list statement'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = [p[1].parse]
        p[0].data = setData(p, 1)
        
        p[0].place = p[1].place
        if isinstance(p[1].code, dict):
            p[0].code = [p[1].code.copy()]
        else:
            p[0].code = p[1].code.copy()
    else:
        p[0].parse = p[1].parse
        p[0].parse.append(p[2].parse)
        p[0].data = {}
        if "retType" in p[1].data.keys():
            if "retType" in p[2].data.keys() and p[1].data["retType"] != p[2].data["retType"]:
                print("Error at line : " + str(p.lineno(2)) + " :: " + "Return type mismatch")
                exit()
            else:
                p[0].data["retType"] = p[1].data["retType"]
        elif "retType" in p[2].data.keys():
            p[0].data["retType"] = p[2].data["retType"]

        p[0].place = p[2].place
        if isinstance(p[2].code, dict):
            p[0].code = p[1].code + [p[2].code.copy()]
        else:
            p[0].code = p[1].code + p[2].code


def p_expression_statement(p):
    '''expression_statement : STMT_TERMINATOR
                            | expression STMT_TERMINATOR'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(p[i] == ';'):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 3):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)
        
        p[0].place = p[1].place
        p[0].code = p[1].code.copy()


def p_selection_statement_0(p):
    '''selection_statement : IF push_scope L_PAREN expression R_PAREN statement pop_scope'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i in [1, 3, 5]):
                p_.data = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[4]], "condition")
    t2 = add_to_tree([None, p[6]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2], p[1].parse)
    p[0].data = setData(p, 6)
    
    p[0].after = getNewLabel("if_after")
    p[0].code = p[4].code + [ quadGen( "ifz", [ p[4].place, p[0].after ], "ifz " + p[4].place + " goto->" + p[0].after ) ] + p[6].code + [ quadGen( "label", [ p[0].after ], p[0].after + " : " ) ]


def p_selection_statement_1(p):
    '''selection_statement : IF push_scope L_PAREN expression R_PAREN statement pop_scope ELSE push_scope statement pop_scope'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i in [1, 3, 5, 8]):
                p_.data = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[4]], "condition")
    t2 = add_to_tree([None, p[6]], "body")
    t3 = add_to_tree([None, p[10]], "else-body")
    p[0].parse = add_to_tree([p[0], t1, t2, t3], p[1].parse + p[8].parse)
    p[0].data = {}
    if "retType" in p[6].data.keys():
        if "retType" in p[10].data.keys() and p[6].data["retType"] != p[10].data["retType"]:
            print("Error at line : " + str(p.lineno(10)) + " :: " + "Return type mismatch")
            exit()
        else:
            p[0].data["retType"] = p[6].data["retType"]
    elif "retType" in p[10].data.keys():
        p[0].data["retType"] = p[10].data["retType"]

    p[0].if_ = getNewLabel("if_part")
    p[0].else_ = getNewLabel("else_part")
    p[0].after = getNewLabel("if_after")
    tmp_code = [ quadGen( "ifz", [ p[4].place,  p[0].else_ ], "ifz " + p[4].place + " goto->" + p[0].else_ ) ] + p[6].code + [ quadGen( "goto", [ p[0].after ], "goto->" + p[0].after ) ]
    p[0].code = p[4].code + [ quadGen( "label", [ p[0].if_ ], p[0].if_ + ":" ) ] + [ "    " + i for i in tmp_code ] + [ quadGen( "label", [ p[0].else_ ], p[0].else_ + ":" ) ] + [ "    " + i for i in p[10].code ] + [ quadGen( "label", [ p[0].after ], p[0].after + ":" ) ]


def p_selection_statement_2(p):
    '''selection_statement : SWITCH push_scope L_PAREN expression R_PAREN statement pop_scope'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    
    t1 = add_to_tree([None, p[4]], "condition")
    t2 = add_to_tree([None, p[6]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2], p[1].parse)
    if p[4].data["type"] != "int":
        print("Error at line : " + str(p.lineno(3)) + " :: " + "Type not compatible with switch condition")
        exit()
    cases = set()
    for c in p[6].code:
        if c["value"] in cases:
            print("Error at line : " + str(c["lineno"]) + " :: " + "Same value is used more than one time in cases")
            exit()
        else:
            cases.add(c["value"])
    p[0].data = setData(p, 6)

    p[0].case = getNewLabel("switch_case")
    p[0].next = getNewLabel("switch_body")
    p[0].after = getNewLabel("switch_after")
    caselist = []
    nextlist = []
    test = p[4].place
    default_label = p[0].after
    for idx, val in enumerate([c["value"] for c in p[6].code]):
        if val == None:
            default_label = p[6].code[idx]["label"]
            continue
        tmp1 = getNewTmp("int")
        tmp2 = getNewTmp("int")
        caselist = caselist + [ quadGen( "=", [ tmp1, str(val)], tmp1 + " = " + str(val) ) ] + [ quadGen( "-", [ tmp2, test, tmp1 ] ), quadGen( "ifz", [ tmp2, p[6].code[idx]["label"] ], "ifz " + tmp2 + " goto->" + p[6].code[idx]["label"] ) ]
    caselist = caselist + [ quadGen( "goto", [ default_label ], "goto->" + default_label ) ]
    for idx, code in enumerate(p[6].code):
        tmp_code = [ quadGen( "goto", [ p[0].after ], "goto->" + p[0].after ) if re.fullmatch('[ ]*break', i) else i for i in code["statement"] ]
        nextlist = nextlist + [ quadGen( "label", [ code["label"] ], code["label"] + ":" ) ] + [ "    " + i for i in tmp_code ]
    p[0].code = p[4].code + [ quadGen( "label", [ p[0].case ], p[0].case + ":" ) ] + [ "    " + i for i in caselist ] + [ quadGen( "label", [ p[0].next ], p[0].next + ":" ) ] + [ "    " + i for i in nextlist ] + [ quadGen( "label", [ p[0].after ], p[0].after + ":" ) ]


def p_iteration_statement_0(p):
    '''iteration_statement : WHILE push_scope L_PAREN expression R_PAREN statement pop_scope'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[4]], "condition")
    t2 = add_to_tree([None, p[6]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2], p[1].parse)
    p[0].data = setData(p, 6)

    p[0].begin = getNewLabel("while_body")
    p[0].after = getNewLabel("while_after")
    tmp_code = p[4].code + [ quadGen( "ifz", [ p[4].place, p[0].after ], "ifz " + p[4].place + " goto->" + p[0].after ) ] + p[6].code + [ quadGen( "goto", [ p[0].begin ], "goto->" + p[0].begin ) ]
    tmp_code = [ quadGen( "goto", [ p[0].after ], "goto->" + p[0].after ) if re.fullmatch('[ ]*break', i) else i for i in tmp_code ]
    tmp_code = [ quadGen( "goto", [ p[0].begin ], "goto->" + p[0].begin ) if re.fullmatch('[ ]*continue', i) else i for i in tmp_code ]
    p[0].code = [ quadGen( "label", [ p[0].begin ], p[0].begin + ":" ) ] + [ "    " + i for i in tmp_code ] + [ quadGen( "label", [ p[0].after ], p[0].after + ":" ) ]


def p_iteration_statement_1(p):
    '''iteration_statement : DO push_scope statement WHILE L_PAREN expression R_PAREN pop_scope STMT_TERMINATOR'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[6]], "condition")
    t2 = add_to_tree([None, p[3]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2], p[1].parse + '-' + p[4].parse)
    p[0].data = setData(p, 3)

    p[0].begin = getNewLabel("do_body")
    p[0].after = getNewLabel("do_after")
    tmp_code = p[3].code + p[6].code + [ quadGen( "ifnz", [ p[6].place, p[0].begin ], "ifnz " + p[6].place + " goto->" + p[0].begin ) ]
    tmp_code = [ quadGen( "goto", [ p[0].after ], "goto->" + p[0].after ) if re.fullmatch('[ ]*break', i) else i for i in tmp_code ]
    tmp_code = [ quadGen( "goto", [ p[0].begin ], "goto->" + p[0].begin ) if re.fullmatch('[ ]*continue', i) else i for i in tmp_code ]
    p[0].code = [ quadGen( "label", [ p[0].begin ], p[0].begin + ":" ) ] + [ "    " + i for i in tmp_code ] + [ quadGen( "label", [ p[0].after ], p[0].after + ":" ) ]


def p_iteration_statement_2(p):
    '''iteration_statement : FOR push_scope L_PAREN expression_statement expression_statement R_PAREN statement pop_scope'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[4]], "initialisation")
    t2 = add_to_tree([None, p[5]], "stop condition")
    t3 = add_to_tree([None, p[7]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2, t3], p[1].parse)
    p[0].data = setData(p, 7)

    p[0].test = getNewLabel("for_test")
    p[0].body = p[0].test
    p[0].after = getNewLabel("for_after")
    tmp_code = p[5].code + [ quadGen( "ifz", [ p[5].place, p[0].after ], "ifz " + p[5].place + " goto->" + p[0].after ) ] + p[7].code + [ quadGen( "goto", [ p[0].test ], "goto->" + p[0].test ) ]
    tmp_code = [ quadGen( "goto", [ p[0].after ], "goto->" + p[0].after ) if re.fullmatch('[ ]*break', i) else i for i in tmp_code ]
    tmp_code = [ quadGen( "goto", [ p[0].body ], "goto->" + p[0].body ) if re.fullmatch('[ ]*continue', i) else i for i in tmp_code ]
    p[0].code = p[4].code + [ quadGen( "label", [ p[0].test ], p[0].test + ":" ) ] + [ "    " + i for i in tmp_code ] + [ quadGen( "label", [ p[0].after ], p[0].after + ":" ) ]


def p_iteration_statement_3(p):
    '''iteration_statement : FOR push_scope L_PAREN expression_statement expression_statement expression R_PAREN statement pop_scope'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[4]], "initialisation")
    t2 = add_to_tree([None, p[5]], "stop condition")
    t3 = add_to_tree([None, p[6]], "update")
    t4 = add_to_tree([None, p[8]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2, t3, t4], p[1].parse)
    p[0].data = setData(p, 8)

    p[0].test = getNewLabel("for_test")
    p[0].body = getNewLabel("for_body")
    p[0].after = getNewLabel("for_after")
    tmpCode = [ quadGen( "ifz", [ p[5].place, p[0].after ], "ifz " + p[5].place + " goto->" + p[0].after ) ] + p[8].code
    tmp_code = p[5].code + tmpCode + p[6].code + [ quadGen( "goto", [ p[0].test ], "goto->" + p[0].test ) ]
    tmp_code = [ quadGen( "goto", [ p[0].after ], "goto->" + p[0].after ) if re.fullmatch('[ ]*break', i) else i for i in tmp_code ]
    tmp_code = [ quadGen( "goto", [ p[0].body ], "goto->" + p[0].body ) if re.fullmatch('[ ]*continue', i) else i for i in tmp_code ]
    p[0].code = p[4].code + [ quadGen( "label", [ p[0].test], p[0].test + ":" ) ] + [ "    " + i for i in tmp_code[:len( p[5].code + tmpCode )] ]
    p[0].code = p[0].code + [ quadGen( "label", [ p[0].body ], p[0].body + ":" ) ] + [ "    " + i for i in tmp_code[len( p[4].code + tmpCode ):] ]
    p[0].code = p[0].code + [ quadGen( "label", [ p[0].after ], p[0].after + ":" ) ]


def p_jump_statement(p):
    '''jump_statement : CONTINUE STMT_TERMINATOR
                      | BREAK STMT_TERMINATOR
                      | RETURN STMT_TERMINATOR
                      | RETURN expression STMT_TERMINATOR'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 3):
        p[0].parse = add_to_tree([p[0]], p[1].parse)
        if(p[1].data == "return"):
            p[0].data["retType"] = "void"
            p[0].code = [ quadGen( "return", [ ], "return" ) ]
        else:
            p[0].code = [ p[1].data ]
    else:
        p[0].parse = add_to_tree([p[0], p[2]], p[1].parse)
        p[0].data["retType"] = p[2].data["type"]
        
        p[0].code = p[2].code + [ quadGen( "return", [ p[2].place ], "return " + p[2].place ) ]


def p_translation_unit(p):
    '''translation_unit : external_declaration
                        | translation_unit external_declaration'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = [p[1].parse]
        
        p[0].code = p[1].code.copy()
    else:
        p[0].parse = p[1].parse
        p[0].parse.append(p[2].parse)
        
        p[0].code = p[1].code + p[2].code


def p_external_declaration(p):
    '''external_declaration : function_definition
                            | declaration'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    p[0].parse = p[1].parse
    
    p[0].code = p[1].code.copy()


def p_function_definition(p):
    '''function_definition : declaration_specifiers declarator L_PAREN func_push_scope parameter_type_list R_PAREN compound_statement pop_scope'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    t1 = list(toParse(p[-1:]))[0]
    p[2].parse = list(flatten(p[2].parse))
    f_name = str(p[2].parse[-1:][0])
    for x in p[2].parse:
        if(x == '*'):
            f_name = '*' + f_name
        else:
            break
    if(p[2].parse[-2:-1][0] is None):
        p[0].parse = add_to_tree([p[0], t1], f_name)
    else:
        p[0].parse = add_to_tree([p[0], p[2].parse[-2:-1], t1], f_name)
    
    ret_type = p[1].data["type"] + p[2].data["type"]
    
    if(p[7].data == {} or "retType" not in p[7].data.keys()):
        p[7].data["retType"] = "void"
    if(ret_type != p[7].data["retType"]):
        print("Error at line : " + str(p.lineno(3)) + " :: " + "Return type mismatch expected " + ret_type + ", but returns " + p[7].data["retType"])
        exit()
    
    res, scp = checkEntry(p[2].data["name"], 0)
    res["definition"] = True
    res["stack_space"] = getOffset()
    updateEntry(p[2].data["name"], res)
    popOffset()

    p[0].code = [ quadGen( "label", [ res["label"] ], res["name"] + "|" + res["input_type"] + ":" ), quadGen( "BeginFunc", [ str(res["stack_space"]) ], "    BeginFunc " + str(res["stack_space"]) ) ] + p[5].code + [ "    " + i for i in p[7].code ]


# Error rule for syntax errors
def p_error(p):
    print("Syntax Error: line " + str(p.lineno) + ":" + filename.split('/')[-1], "near", p.value)
    exit()


def p_push_scope(p):
    'push_scope :'
    pushScope()


def p_struct_push_scope(p):
    'struct_push_scope :'
    structs.append(p[-2])
    pushScope()
    pushOffset()


def p_func_push_scope(p):
    'func_push_scope :'
    global currentScopeId
    global scopeTables
    if(currentScopeId):
        print("Error at line : " + str(p.lineno(0)) + " :: " + "Function can only be declared in global scope")
        exit()
    pushScope()
    pushOffset()


def p_pop_scope(p):
    'pop_scope :'
    popScope()


def main():
    if(len(sys.argv) == 1 or sys.argv[1] == "-h"):
        print("""Command Usage:
            python3 parser.py code.c
        where code.c is the input c file""")
        exit()

    parser = yacc.yacc()
    parser.error = 0

    global f
    global filename

    f = open("graph.dot", "w+")
    f.write("digraph ast {")

    filename = sys.argv[1]
    c_code = open(filename, 'r').read()
    p = parser.parse(c_code, lexer=lexer)
    f.write("\n}\n")

    f1 = open("symTab.dump", "w")
    for i in range(len(scopeTables)):
        f1.write("SCOPE " + str(i) + " : START \n")
        for key in scopeTables[i].table.keys():
            f1.write("    " + str(key) + " :: ")
            data = scopeTables[i].table[key]
            if isinstance(data, dict):
                for attrib in data.keys():
                    f1.write("{ " + str(attrib) + " : " +
                             str(data[attrib]) + " } , ")
            f1.write("\n")
        f1.write("END" + "\n\n")

    f1.write("\n")
    f1.write("SCOPE ID : PARENT ID\n")
    for i in range(len(scopeTables)):
        f1.write("\t" + str(i) + "\t\t" + str(scopeTables[i].parent) + "\n")

    f2 = open("symTab.obj", "wb")
    pickle.dump(scopeTables,f2)


if '__main__' == __name__:
    main()
