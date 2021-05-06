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
labels = {}
tmpId = 0

globalScopeTable = SymbolTable()
scopeTables.append(globalScopeTable)
offsets = [0]
offsetPId = [None]
currentOffset = 0

error_line_offset = 0


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
            if(res):
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
        return 8
    elif type_ in size.keys():
        return size[type_]
    else:
        struct_info, scp = checkEntry(type_, 0)
        if struct_info ==  False:
            print(" Error :: struct " + type_ + " is not defined")
            exit(-1)
        return struct_info["size"]

#--------------------------FUNCTIONS FOR 3AC-----------------------------------#


def getNewLabel(s="label"):
    labels[s] = labels[s]+1 if s in labels.keys() else 0
    label = s + "#" + str(labels[s])
    return label


def getNewTmp(type_, offset=None, size=None, base="rbp"):
    global tmpId
    tmp = "tmp_" + str(tmpId)
    tmpId = tmpId + 1

    if offset == None:
        addToOffset(getSize(type_))
        offset = getOffset()

    data = {"type":  type_, "class": "tmp", "size": size,
            "offset": offset, "base": str(base)}
    pushEntry(tmp, data)

    return tmp


def quad(op, a, statement=None):
    global currentScopeId

    arg = [str(a[i]) if i < len(a) else "" for i in range(3)]
    if statement == None:
        statement = str(op) + " " + arg[0] + " " + arg[1] + " " + arg[2]
    return " $ ".join([statement]+[op] + arg + [str(currentScopeId)])


class NODE:
    def __init__(self):
        self.data = {}
        self.code = []
        self.place = None

    def __str__(self):
        return (str(self.data) + str(self.place))


# fix this
def type_cast(type1, type2, place1, place2):
    prec = {"char": 1, "int": 2, "float": 3}
    if(type1 == type2):
        return {"place": place1, "code": [], "type": type1}
    if(prec[type1] > prec[type2]):
        tmp = getNewTmp(type1)
        return {"place": tmp, "code": [quad(type2+"_to_"+type1, [tmp, place2, ''], tmp + " = " + type2+"_to_"+type1+"("+place2+")")], "type": type1}
    else:
        tmp = getNewTmp(type2)
        return {"place": tmp, "code": [quad(type1+"_to_"+type2, [tmp, place1, ''], tmp + " = " + type1+"_to_"+type2+"("+place1+")")], "type": type2}


def isCompatible(type1, type2):
    if(type1 == type2):
        return True
    elif(type1 == "void" or type2 == "void"):
        return False
    if(type1[-1] == '*' or type2[-1] == '*'):
        return False
    return True


def report_error(msg, line):
    global error_line_offset
    if line == "break" or line == "continue":
        print("Error : " + msg + ", Check your " + line + "s")
        exit(-1)
    print("Error at line : " + str(line - error_line_offset) + " :: " + msg)
    exit(-1)


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
            report_error(
                "break should be inside for/do-while/while/switch-case !!", "break")
        elif re.fullmatch('[ ]*continue', i) != None:
            report_error(
                "continue should be inside for/do-while/while !!", "continue")

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


def p_primary_expression(p):
    '''primary_expression : ID
                          | INT_CONSTANT
                          | FLOAT_CONSTANT
                          | STRING
                          | L_PAREN expression R_PAREN'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 2 and i == 1):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        if isinstance(p[1].data, int):
            p[0].data = {"type": "int", "class": "basic",
                         "value": p[1].data, "name": None}

            p[0].place = getNewTmp(p[0].data["type"])
            p[0].code = [quad("=", [p[0].place, str(
                p[0].data["value"]), ""], p[0].place + " = " + str(p[0].data["value"]))]
        elif isinstance(p[1].data, float):
            p[0].data = {"type": "float", "class": "basic",
                         "value": p[1].data, "name": None}

            p[0].place = getNewTmp(p[0].data["type"])
            p[0].code = [quad("=", [p[0].place, str(
                p[0].data["value"]), ""], p[0].place + " = " + str(p[0].data["value"]))]
        elif isinstance(p[1].data, str) and p[1].data[0] == '"':
            p[0].data = {"type": "char*", "class": "basic",
                         "value": p[1].data, "name": None}

            p[0].place = getNewTmp(p[0].data["type"])
            p[0].code = [quad("=", [p[0].place, str(
                p[0].data["value"]), ""], p[0].place + " = " + str(p[0].data["value"]))]
        else:
            res, scp = checkEntry(p[1].data)
            if(res == False):
                print("Error at line : " + str(p.lineno(1)) + " :: " +
                      p[1].data + " | Identifier is not declared")
                exit()
            p[0].data = res.copy()

            p[0].place = p[1].data + "@" + str(scp)
            p[0].code = [""]
    else:
        p[0].parse = p[2].parse
        p[0].data = setData(p, 2)

        p[0].place = p[2].place
        p[0].code = p[2].code.copy()


# distinguish static array from pointer

def p_postfix_expression(p):
    '''postfix_expression : primary_expression
                          | postfix_expression L_SQBR expression R_SQBR
                          | postfix_expression L_PAREN R_PAREN
                          | postfix_expression L_PAREN argument_expression_list R_PAREN
                          | postfix_expression DOT ID
                          | postfix_expression ARROW ID
                          | postfix_expression INCREMENT
                          | postfix_expression DECREMENT'''
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

    elif(len(p) == 3):
        p[0].parse = [p[1].parse, p[2].parse]
        allowed_type = ["char", "int", "float"]
        if p[1].data["type"] not in allowed_type or p[1].data["type"][-1] != '*':
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  p[1].data["name"] + " | Type not compatible with increment/decrement operation")
            exit()
        p[0].data["type"] = p[1].data["type"]
        p[0].data["class"] = "basic"

        p[0].place = p[1].place
        p[0].code = p[1].code + [quad("=", [p[0].place, p[1].place], p[0].place + " = " + p[1].place)] + [
            quad(p[2].parse, [p[1].place], p[1].place + p[2].parse)]

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
    elif(p[2].parse == '.' or p[2].parse == '->'):
        p[0].parse = add_to_tree([p[0], p[1], p[3]], p[2].parse)
        if p[1].data["class"] != "struct":
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  p[1].data["name"] + " | Identifier used is not a struct class")
            exit()
        if(p[2].parse == '.'):
            res, scp = checkEntry(p[1].data["type"], 0)
            res_, scp_ = checkEntry(p[3].parse, res["members_scope"])
            if(res_ == False):
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      p[3].parse + " | Identifier used is not in struct member list")
                exit()
            p[0].data = res_.copy()

            res__, scp__ = checkEntry(p[1].place)
            tmpvar = getNewTmp("int*")
            (base, op) = (
                "rbp", "-") if str(res__["base"]) == "rbp" else ("0", "+")
            p[0].place = getNewTmp(res_["type"], tmpvar, res_["size"], base)
            p[0].code = p[1].code + 
                [quad(op, [tmpvar, res__["offset"], res__["size"] - res_["offset"]])]
            p[0].data["offset"] = tmpvar
            p[0].data["base"] = base
        else:
            if(p[1].data["type"][-1] != '*'):
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      p[1].data["name"] + " | Identifier used is not a struct pointer")
                exit()
            res, scp = checkEntry(p[1].data["type"][:-1], 0)
            res_, scp_ = checkEntry(p[3].parse, res["members_scope"])
            if(res_ == False):
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      p[3].parse + " | Identifier used is not in struct member list")
                exit()
            p[0].data = res_.copy()

            tmpvar = getNewTmp("int*")
            p[0].place = getNewTmp(res_["type"], tmpvar, res_["size"], "0")
            p[0].code = p[1].code + 
                [quad("+", [tmpvar, p[1].place, res["size"] - res_["offset"]])]
            p[0].data["offset"] = tmpvar
            p[0].data["base"] = "0"
    elif(p[3].parse == ')'):
        p[0].parse = add_to_tree([p[0]], p[1].parse + "()")
        res, scp = checkEntry(p[1].data["name"], 0)
        if(res == False):
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  p[1].data["name"] + " | Function is not declared")
            exit()
        p[1].data = res
        p[0].data["type"] = p[1].data["ret_type"]
    elif(p[4].parse == ')'):
        p[0].parse = add_to_tree([p[0], p[3]], p[1].parse + "()")
        res, scp = checkEntry(p[1].data["name"], 0)
        if(res == False):
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  p[1].data["name"] + " | Function is not declared")
            exit()
        p[1].data = res
        input_list = p[1].data["input_type"].split(',')[1:]
        arg_list = p[3].data
        if(len(input_list) != len(arg_list)):
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  p[1].data["name"] + " | Insufficient function arguments")
            exit()
        for i in range(len(input_list)):
            if((arg_list[i]["class"] == "struct" and input_list[i] == arg_list[i]["type"])
               or ((input_list[i][-1] == '*') ^ (arg_list[i]["type"][-1] == '*'))
               or (input_list[i][-1] == '*' and arg_list[i]["type"][-1] == '*' and input_list[i] != arg_list[i]["type"])):
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      p[1].data["name"] + " | Type mismatch in function arguments")
                exit()
        p[0].data["type"] = p[1].data["ret_type"]


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


def p_unary_expression(p):
    '''unary_expression : postfix_expression
                        | INCREMENT unary_expression
                        | DECREMENT unary_expression
                        | unary_operator cast_expression
                        | SIZEOF unary_expression
                        | SIZEOF L_PAREN type_name R_PAREN'''
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

    elif(p[2].parse == '('):
        p[0].parse = add_to_tree([p[0], p[3]], "sizeof")
        p[0].data["type"] = "int"
        p[0].data["class"] = "basic"

        p[0].place = getNewTmp("int")
        p[0].code = p[3].code+[quad("=", [p[0].place, str(getSize(
            p[3].data["type"])), ""], p[0].place+"= "+str(getSize(p[3].data["type"])))]
    elif(p[1].parse == 'sizeof'):
        p[0].parse = add_to_tree([p[0], p[2]], "sizeof")
        p[0].data["type"] = "int"
        p[0].data["class"] = "basic"

        res, scp = checkEntry(p[2].place)
        p[0].place = getNewTmp("int")
        p[0].code = p[2].code + 
            [quad("=", [p[0].place, str(res["size"]), ""],
                  p[0].place+"= "+str(res["size"]))]
    else:
        p[0].parse = add_to_tree([p[0], p[2]], p[1].parse)
        p[0].data = setData(p, 2)
        if(p[1].data == '&'):
            p[0].data["type"] = p[2].data["type"] + '*'

            p[0].place = getNewTmp(p[0].data["type"])
            p[0].code = p[2].code + 
                [quad("lea", [p[0].place, p[2].place],
                      p[0].place + " = & " + p[2].place)]
        elif(p[1].data == '*'):
            if p[2].data["type"][-1] != '*':
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      p[2].data["name"] + " | Error dereferencing non pointer variable")
                exit()
            p[0].data["type"] = p[2].data["type"][:-1]

            p[0].place = getNewTmp(
                p[0].data["type"], p[2].place, size=getSize(p[0].data["type"]), base="0")
            p[0].code = p[2].code.copy()
        elif(p[1].data == '!'):
            p[0].data["type"] = "int"
            p[0].data["class"] = "basic"

            p[0].place = getNewTmp(p[0].data["type"])
            p[0].code = p[2].code + [quad(p[1].data, [p[0].place, p[2].place, ""],
                                          p[0].place + " = " + p[1].data + " " + p[2].place)]
        elif(p[1].data in ['+', '-', '~']):
            if p[2].data["class"] != 'basic':
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      p[2].data["name"] + " | Type not compatible with unary operator")
                exit()
            p[0].data["type"] = p[2].data["type"]

            if(p[1].data == '~'):
                p[0].place = getNewTmp(p[0].data["type"])
                p[0].code = p[2].code + [quad(p[1].data, [p[0].place, p[2].place, ""],
                                              p[0].place + " = " + p[1].data + " " + p[2].place)]
            elif(p[1].data == '+'):
                p[0].code = p[2].code.copy()
                p[0].place = p[2].place
            else:
                p[0].place = getNewTmp(p[2].data["type"])
                p[0].code = p[2].code + 
                    [quad("*", [p[0].place, "-1", p[2].place],
                          p[0].place + " = " + " -1 * " + p[2].place)]
        else:
            allowed_type = ["char", "int", "float"]
            if p[2].data["type"] not in allowed_type or p[2].data["type"][-1] != '*':
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      p[2].data["name"] + " | Type not compatible with unary operation")
                exit()
            p[0].data["type"] = p[2].data["type"]

            p[0].place = p[2].place
            p[0].code = p[2].code + 
                [quad(p[1].parse, [p[2].place], p[2].place + p[1].parse)]


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
        if(p[2].data["type"][-1] == '*') ^ (p[4].data["type"][-1] == '*'):
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  p[2].data["type"] + " | Type cast not allowed for pointer and non-pointer")
            exit()
        p[0].data = setData(p, 4)
        p[0].data["type"] = p[2].data["type"]

        p[0].place = getNewTmp(p[0].data["type"])
        p[0].code = p[4].code + p[2].code + [quad(p[4].data["type"]+"_to_"+p[2].data["type"], [p[0].place, p[4].place, ""],
                                    p[0].place+"=" + p[4].data["type"]+"_to_"+p[2].data["type"]+"("+p[4].place+")")]


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
        if(p[2].data == '%'):
            allowed_type = ["char", "int"]
            if p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      "Type not compatible with modulo operation")
                exit()
        else:
            allowed_type = ["char", "int", "float"]
            if p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      "Type not compatible with multiply or divide operation")
                exit()
        # p[0].data["type"] = type_cast(p[1].data["type"], p[3].data["type"])["type"]
        p[0].data["class"] = "basic"

        x = type_cast(p[1].data["type"], p[3].data["type"],
                      p[1].place, p[3].place)
        p[0].data["type"] = x["type"]
        p[0].place = getNewTmp(x["type"])
        tmp_code = [quad(p[2].data, [ p[0].place , p[1].place, p[3].place ])]
        p[0].code = p[1].code+p[3].code+x["code"]+tmp_code


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
            allowed_type = ["char", "int"]
            if(p[3].data["type"] not in allowed_type):
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      "Type incompatible for pointer with minus or plus operation")
                exit()
            p[0].data["type"] = p[1].data["type"]

            tmp = getNewTmp(p[3].data["type"])
            tmp_code = [ quad("*", [ tmp , p[3].place , str(getSize(p[1].data["type"][:-1] ) )] ) ]
            p[0].place = getNewTmp(p[1].data["type"])
            p[0].code = p[1].code + p[3].code + tmp_code + [ quad( p[2].data, [ p[0].place ,p[1].place ,tmp] ) ]
        
        elif(p[3].data["type"][-1] == '*'):
            allowed_type = ["char", "int"]
            if(p[1].data["type"] not in allowed_type):
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      "Type incompatible for pointer with minus or plus operation")
                exit()
            if(p[2].data == '-'):
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      "Integer minus pointer is not compatible expression")
                exit()
            p[0].data["type"] = p[3].data["type"]

            tmp = getNewTmp(p[1].data["type"])
            tmp_code = [ quad("*", [ tmp , p[1].place , str(getSize(p[3].data["type"][:-1] ) )] ) ]
            p[0].place = getNewTmp(p[3].data["type"])
            p[0].code = p[1].code + p[3].code + tmp_code + [ quad( p[2].data, [ p[0].place ,p[3].place ,tmp] ) ]

        else:
            allowed_type = ["char", "int", "float"]
            if p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      "Type not compatible with plus or minus operation")
                exit()
            # p[0].data["type"] = type_cast(p[1].data["type"], p[3].data["type"])["type"]
            p[0].data["class"] = "basic"

            x = type_cast(p[1].data["type"], p[3].data["type"],
                          p[1].place, p[3].place)
            p[0].data["type"] = x["type"]
            p[0].place = getNewTmp(x["type"])
            tmp_code = [quad(p[2].data, [ p[0].place , p[1].place, p[3].place ])]
            p[0].code = p[1].code+p[3].code+x["code"]+tmp_code


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
        allowed_type = ["char", "int"]
        if p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with bitwise shift operation")
            exit()
        p[0].data["type"] = p[1].data["type"]

        p[0].place = getNewTmp(p[1].data["type"])
        p[0].code = p[1].code + p[3].code + [ quad(p[2].data, [
                                                  p[0].place, p[1].place, p[3].place]) ]


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
        allowed_type = ["char", "int", "float"]
        if p[1].data["type"][-1] == '*' and p[3].data["type"][-1] == '*':
            pass
        elif p[1].data["type"][-1] == '*' and p[3].data["type"] not in ["char", "int"]:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with relational operation " + p[1].data["type"] + ", " + p[3].data["type"])
            exit()
        elif p[3].data["type"][-1] == '*' and p[1].data["type"] not in ["char", "int"]:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with relational operation " + p[1].data["type"] + ", " + p[3].data["type"])
            exit()
        elif p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with relational operation " + p[1].data["type"] + ", " + p[3].data["type"])
            exit()
        p[0].data["type"] = "int"
        p[0].data["class"] = "basic"

        p[0].place = getNewTmp("int")
        tmp_code = [quad(p[2].data, [p[0].place, p[1].place, p[3].place])]
        p[0].code = p[1].code+p[3].code+tmp_code


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
        allowed_type = ["char", "int", "float"]
        if p[1].data["type"][-1] == '*' and p[3].data["type"][-1] == '*':
            pass
        elif p[1].data["type"][-1] == '*' and p[3].data["type"] not in ["char", "int"]:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with relational operation " + p[1].data["type"] + ", " + p[3].data["type"])
            exit()
        elif p[3].data["type"][-1] == '*' and p[1].data["type"] not in ["char", "int"]:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with relational operation " + p[1].data["type"] + ", " + p[3].data["type"])
            exit()
        elif p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with relational operation " + p[1].data["type"] + ", " + p[3].data["type"])
            exit()
        p[0].data["type"] = "int"
        p[0].data["class"] = "basic"

        p[0].place = getNewTmp("int")
        tmp_code = [quad(p[2].data, [p[0].place, p[1].place, p[3].place])]
        p[0].code = p[1].code+p[3].code+tmp_code


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
        allowed_type = ["char", "int"]
        if p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with bitwise and operation " + p[1].data["type"] + ", " + p[3].data["type"])
            exit()
        # p[0].data["type"] = type_cast(p[1].data["type"], p[3].data["type"])["type"]
        p[0].data["class"] = "basic"

        x = type_cast(p[1].data["type"], p[3].data["type"],
                          p[1].place, p[3].place)
        p[0].data["type"] = x["type"]
        p[0].place = getNewTmp(x["type"])
        tmp_code = [quad(p[2].data, [ p[0].place , p[1].place, p[3].place ])]
        p[0].code = p[1].code+p[3].code+x["code"]+tmp_code


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
        allowed_type = ["char", "int"]
        if p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with bitwise xor operation " + p[1].data["type"] + ", " + p[3].data["type"])
            exit()
        # p[0].data["type"] = type_cast(p[1].data["type"], p[3].data["type"])["type"]
        p[0].data["class"] = "basic"

        x = type_cast(p[1].data["type"], p[3].data["type"],
                          p[1].place, p[3].place)
        p[0].data["type"] = x["type"]
        p[0].place = getNewTmp(x["type"])
        tmp_code = [quad(p[2].data, [ p[0].place , p[1].place, p[3].place ])]
        p[0].code = p[1].code+p[3].code+x["code"]+tmp_code


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
        allowed_type = ["char", "int"]
        if p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with bitwise or operation " + p[1].data["type"] + ", " + p[3].data["type"])
            exit()
        # p[0].data["type"] = type_cast(p[1].data["type"], p[3].data["type"])["type"]
        p[0].data["class"] = "basic"

        x = type_cast(p[1].data["type"], p[3].data["type"],
                          p[1].place, p[3].place)
        p[0].data["type"] = x["type"]
        p[0].place = getNewTmp(x["type"])
        tmp_code = [quad(p[2].data, [ p[0].place , p[1].place, p[3].place ])]
        p[0].code = p[1].code+p[3].code+x["code"]+tmp_code


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
        allowed_type = ["char", "int", "float"]
        if p[1].data["type"][-1] == '*' or p[3].data["type"][-1] == '*':
            p[0].data["type"] = "int"
            p[0].data["class"] = "basic"
            return
        elif p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with logical and operation " + p[1].data["type"] + ", " + p[3].data["type"])
            exit()
        p[0].data["type"] = "int"
        p[0].data["class"] = "basic"

        p[0].place = getNewTmp("int")
        tmp_code = [quad(p[2].data, [p[0].place, p[1].place, p[3].place])]
        p[0].code = p[1].code+p[3].code+tmp_code


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
        allowed_type = ["char", "int", "float"]
        if p[1].data["type"][-1] == '*' or p[3].data["type"][-1] == '*':
            p[0].data["type"] = "int"
            p[0].data["class"] = "basic"
            return
        elif p[1].data["type"] not in allowed_type or p[3].data["type"] not in allowed_type:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with logical or operation " + p[1].data["type"] + ", " + p[3].data["type"])
            exit()
        p[0].data["type"] = "int"
        p[0].data["class"] = "basic"

        p[0].place = getNewTmp("int")
        tmp_code = [quad(p[2].data, [p[0].place, p[1].place, p[3].place])]
        p[0].code = p[1].code+p[3].code+tmp_code


def p_conditional_expression(p):
    '''conditional_expression : logical_or_expression
                              | logical_or_expression QUESTION expression COLON conditional_expression'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(len(p) == 4 and (i == 2 or i == 4)):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 2):
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)

        p[0].place = p[1].place
        p[0].code = p[1].code.copy()

    else:
        p[0].parse = add_to_tree(
            [p[0], p[1], p[3], p[5]], p[2].parse + p[4].parse)
        if p[1].data["type"] in ["void", "void*"] or p[1].data["class"] in ["struct", "union"]:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with ternary operation")
            exit()
        if p[3].data["type"] != p[5].data["type"]:
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type mismatch with ternary operation")
            exit()
        # p[0].data["type"] = type_cast(
        #     p[3].data["type"], p[5].data["type"])["type"]
        p[0].data["class"] = "basic"

        #handle float
        if p[1].data["type"] == "int":
            x = {"place": p[1].place, "code": [], "type": "int"}
        else:
            tmp = getNewTmp("int")
            x = {"place": tmp, "code": [quad(p[1].data["type"] + "_to_"+ "int", [tmp, p[1].place, ''], tmp + " = " + p[1].data["type"] +"_to_"+ "int" +"("+ p[1].place +")")], "type": "int"}
        p[0].data["type"] = p[3].data["type"]
        p[0].place = getNewTmp(p[0].data["type"])
        p[0].else_ = getNewLabel("else_part")
        p[0].after = getNewLabel("after")
        tmp_code = [quad("ifz", [p[1].place,  p[0].else_, ""], "ifz " + p[1].place + " goto->" + p[0].else_)] + p[3].code + [quad("goto", [p[0].after, "", ""], "goto->" + p[0].after)]
        p[0].code = p[1].code + x["code"] + tmp_code + [quad("label", [p[0].else_, "", ""], p[0].else_ + ":")] +  p[5].code + [quad("label", [p[0].after, "", ""], p[0].after + ":")]


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
        if p[1].data["class"] in ["struct", "union"] or p[3].data["class"] in ["struct", "union"] or p[1].data["type"][-1] == '*' and p[3].data["type"] == "float" or p[3].data["type"][-1] == '*' and p[1].data["type"] == "float" or p[1].data["type"] == "void" or p[3].data["type"] == "void":
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  "Type not compatible with assignment operation")
            exit()
        # p[0].data["type"] = type_cast(
        #     p[1].data["type"], p[3].data["type"])["type"]
        p[0].data["class"] = "basic"

        if p[2].data == "=":
            tmp_code = [quad(p[2].data, [p[1].place, p[3].place])]
        else:
            if p[2].data[0] in ["*", "/", "%", "+", "-", "&", "|", "^"]:
                x = type_cast(p[1].data["type"], p[3].data["type"],
                      p[1].place, p[3].place)
                p[0].data["type"] = x["type"]
                tmp_entry = getNewTmp(x["type"])
                tmp_code = x["code"] + [quad(p[2].data[:-1], [ tmp_entry , p[1].place, p[3].place ])]
            else:
                tmp_entry = getNewTmp(p[1].data["type"])
                tmp_code = [ quad(p[2].data[:-1], [ tmp_entry, p[1].place, p[3].place]) ]
            
            tmp_code = tmp_code + [quad(p[2].data[-1], [p[1].place, tmp_entry])]
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
                   | declaration_specifiers init_declarator_list STMT_TERMINATOR'''
    global currentScopeId
    
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    p[0].data = {}
    if(len(p) == 4):
        p[0].parse = []
        for t in p[2].parse:
            if(t[0] == '='):
                p[0].parse.append(t)

        for decl in p[2].data:
            data = setData(p, 1)
            if(data["type"] == "void" or data["type"][:-1] == "void"):
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                      data["name"] + " | Can not declare void type variable")
                exit()
            if("init_type" in decl.keys()):
                if not isCompatible(decl["init_type"], data["type"]) or (data["type"][-1] == '*' and not isCompatible(decl["init_type"], data["type"][:-1])):
                    print("Error at line : " + str(p.lineno(0)) +
                          " :: " + "Incompatible type initialisation")
                    exit()
            data["name"] = decl["name"]
            data["meta"] = decl["meta"]

            if len(data["meta"]) != 0:
                data["is_array"] = 1
                data["element_type"] = data["type"][:-1]
                data["index"] = 1
                data["to_add"] = "0"

                arr_size = 1
                for n in data["meta"]:
                    arr_size = arr_size * n

                data["size"] = getSize(data["element_type"]) * arr_size
                addToOffset(data["size"])
                data["offset"] = getOffset() - data["size"] if currentScopeId == 0 else getOffset() 
                data["base"] = "0" if currentScopeId == 0 else "rbp"
                
                res = pushEntry(decl["name"], data)
                if(res == False):
                    addToOffset(-data["size"])
                    print("Error at line : " + str(p.lineno(0)) + " :: " +
                        decl["name"] + " | Redeclaration of variable")
                    exit()
            else:
                if(decl["type"] != ""):
                    data["type"] = data["type"] + decl["type"]
                if(data["class"] == "struct" or data["class"] == "union"):
                    res, scp = checkEntry(data["type"], 0)
                    if(res != False):
                        data["size"] = res["size"]
                else:
                    data["size"] = getSize(data["type"])
                addToOffset(data["size"])
                data["offset"] = getOffset() - data["size"] if currentScopeId == 0 else getOffset()
                data["base"] = "0" if currentScopeId == 0 else "rbp"
                res = pushEntry(decl["name"], data)
                if(res == False):
                    print("Error at line : " + str(p.lineno(0)) + " :: " +
                        decl["name"] + " | Redeclaration of variable")
                    exit()

                if "init_type" in decl.keys():
                    tmp_code = [ quad("=",[ decl["name"]+"@"+str(currentScopeId) , decl["place"] ] ) ]
                    p[0].code = p[0].code + code
    else:
        p[0].parse = p[1].parse
        p[0].code = p[1].code.copy()


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
                      | SHORT
                      | INT
                      | LONG
                      | FLOAT
                      | DOUBLE
                      | SIGNED
                      | UNSIGNED'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
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
    '''struct_or_union_specifier : struct_or_union ID BLOCK_OPENER push_scope struct_declaration_list pop_scope BLOCK_CLOSER
                                 | struct_or_union ID'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 2):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 8):
        # t = add_to_tree([None, p[4]], "members_list")
        # p[0].parse = add_to_tree([p[0], p[2], t], p[1].parse)
        p[0].data = {"type": p[2].data, "class": p[1].data}
        p[0].data["members_scope"] = p[5].scope
        p[0].data["size"] = getOffset()
        res, scp = pushEntry(p[2].data, p[0].data)
        if(res == False):
            print("Error at line : " + str(p.lineno(0)) +
                  " :: " + "Redefinition of struct variable")
            exit()

        for code in p[4].code:
            if(len(code)) > 0:
                code[0] = p[0].data["type"] + ":" + code[0]
            p[0].code = p[0].code + code
        popOffset()
    elif(len(p) == 5):
        # t = add_to_tree([None, p[3]], "members_list")
        # p[0].parse = add_to_tree([p[0], t], p[1].parse)
        pass
    else:
        p[0].parse = [p[1].parse, p[2].parse]
        res, scp = checkEntry(p[2].data, 0)
        if(res == False):
            print("Error at line : " + str(p.lineno(0)) +
                  " :: " + "Struct identifier is not defined")
            exit()
        p[0].data = res
    # if(len(p) == 3):
    #     p[0].parse = [p[1].parse, p[2].parse]


def p_struct_or_union(p):
    '''struct_or_union : STRUCT
                       | UNION'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
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
        # p[0].parse = [p[1].parse]
        p[0].data = [setData(p, 1)]

        p[0].code = [ p[1].code.copy() ]
    else:
        # p[0].parse = p[1].parse
        # p[0].parse.append(p[2].parse)
        p[0].data = setData(p, 1)
        p[0].data.append(setData(p, 2))

        p[0].code = [ p[1].code.copy() ] + p[2].code
    p[0].scope = currentScopeId


def p_struct_declaration(p):
    '''struct_declaration : specifier_qualifier_list struct_declarator_list STMT_TERMINATOR'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    # p[0].parse = [p[1].parse, p[2].parse]
    for decl in p[2].data:
        data = setData(p, 1)
        if(data["type"] == "void" or data["type"][:-1] == "void"):
            print("Error at line : " + str(p.lineno(0)) + " :: " +
                  data["name"] + " | Can not declare void type variable")
            exit()
        if(decl["type"] != ""):
            data["type"] = data["type"] + decl["type"]
        data["name"] = decl["name"]
        data["meta"] = decl["meta"]

        if len(data["meta"]) != 0:
            data["is_array"] = 1
            data["element_type"] = data["type"][:-1]
            data["index"] = 1
            data["to_add"] = "0"

            arr_size = 1
            for n in data["meta"]:
                arr_size = arr_size * n

            data["size"] = getSize(data["element_type"]) * arr_size
            addToOffset(data["size"])
            data["offset"] = getOffset()
            data["base"] = "rbp"
                
            res = pushEntry(decl["name"], data)
            if(res == False):
                addToOffset(-data["size"])
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                    decl["name"] + " | Redeclaration of variable")
                exit()
        else:   
            data["size"] = getSize(data["type"])
            addToOffset(data["size"])
            data["offset"] = getOffset()
            data["base"] = "rbp"
            res = pushEntry(decl["name"], data)
            if(res == False):
                print("Error at line : " + str(p.lineno(0)) + " :: " +
                    decl["name"] + " | Redeclaration of variable")
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


def p_struct_declarator_list(p):
    '''struct_declarator_list : struct_declarator
                              | struct_declarator_list COMMA struct_declarator'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    if(len(p) == 2):
        # p[0].parse = [p[1].parse]
        p[0].data = [setData(p, 1)]
    else:
        # p[0].parse = p[1].parse
        # p[0].parse.append(p[3].parse)
        p[0].data = setData(p, 1)
        p[0].data.append(setData(p, 3))


def p_struct_declarator(p):
    '''struct_declarator : declarator'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    # p[0].parse = list(toParse(p[1:]))
    if(len(p) == 2):
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
                         | direct_declarator L_SQBR R_SQBR
                         | direct_declarator L_PAREN f_push_scope parameter_type_list R_PAREN
                         | direct_declarator L_PAREN f_push_scope R_PAREN'''
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
        p[0].data = {"name": setData(p, 1), "type": "", "meta": []}
    elif(p[2].parse == '('):
        p[0].parse = [[p[0].parse], p[1].parse + "()"]
        function_name = p[1].data["name"]
        p[0].data = {
            "name": function_name,
            "ret_type": None,
            "input_type": None,
            "func_scope": currentScopeId,
            "func_offset": getOffset()
        }
        if(p[3] == ')'):
            # p[0].parse = [[p[0].parse], p[1].parse + "()"]
            pass
        else:
            # t = add_to_tree([None, p[3]], "parameters")
            # p[0].parse = [[p[0].parse, t], p[1].parse + "()"]
            input_type = ""
            for arg in p[4].data:
                input_type = input_type + ',' + arg["type"]
            p[0].data["input_type"] = input_type
        parent = getParentScope(currentScopeId)
        res, scp = checkEntry(function_name, parent)
        if(res == False):
            pushEntry(function_name, {
                      "type": "function", "class": "function", **(p[0].data)}, scope=parent)
        else:
            print("Error at line : " + str(p.lineno(0)) +
                  " :: " + "Redeclaration of function name")
            exit()
        
    else:
        p[0].parse = p[1].parse
        p[0].data = setData(p, 1)
        if(p[1].data["type"] == "void"):
            print("Error at line : " + str(p.lineno(0)) +
                  " :: " + "Can not declare void type array")
            exit()
        p[0].data["type"] = p[1].data["type"] + '*'
        p[0].data["meta"] = p[1].data["meta"] + [p[3].data] if len(p) == 5 else [1]


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
    # elif(len(p) == 3 and (p[2].parse == 'const' or p[2].parse == 'volatile')):
    #     p[0].parse = [p[1].parse, p[2].parse]
    # elif(len(p) == 3):
    #     p[0].parse = p[2].parse
    #     p[0].parse.insert(0, p[1].parse)
    # else:
    #     p[0].parse = p[3].parse
    #     p[0].parse.insert(0, p[2].parse)
    #     p[0].parse.insert(0, p[1].parse)


def p_parameter_type_list(p):
    '''parameter_type_list : parameter_list
                           | parameter_list COMMA ELLIPSIS'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    p[0].parse = p[1].parse
    p[0].data = setData(p, 1)


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
    if(data["type"] == "void"):
        print("Error at line : " + str(p.lineno(0)) + " :: " +
              "Can not declare void type variable in parameter")
        exit()
    if(decl["type"] == '*'):
        data["type"] = data["type"] + '*'
    data["name"] = decl["name"]
    data["meta"] = decl["meta"]
    res = pushEntry(decl["name"], data)
    if(res == False):
        print("Error at line : " + str(p.lineno(0)) +
              " :: " + "Redeclaration of variable")
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
        p[0].data["type"] += p[2].data["type"]
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
    # else:
    #     p[0].parse = '{' + str(p[2].parse)[1:-1] + '}'
    #     p[0].data = {}
    #     init_type = p[2].data[0]["type"]
    #     for init in p[2].data:
    #         if not isCompatible(init["type"], init_type):
    #             print("Error at line : " + str(p.lineno(0)) +
    #                   " :: " + "Incompatible type initialisation")
    #             exit()
    #         # init_type = type_cast(init_type, init["type"])["type"]
    #     p[0].data["type"] = init_type


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
                 | push_scope compound_statement pop_scope
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
    else:
        p[0].parse = p[2].parse
        p[0].data = setData(p, 2)
        p[0].place = p[2].place
        p[0].code = p[2].code.copy()


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
        p[0].parse = add_to_tree(
            [p[0], p[4]], p[1].parse + ' ' + str(p[2].parse))
        p[0].data = setData(p, 4)
        p[0].code = {
            "class": "case",
            "type": "int",
            "value": p[2].parse,
            "statement": p[4].code,
            "label": label
        }
    elif(p[1] == 'default'):
        p[0].parse = add_to_tree([p[0], p[3]], p[1].parse)
        p[0].data = setData(p, 3)
        p[0].code = {
            "class": "default",
            "type": None,
            "value": None,
            "statement": p[3].code,
            "label": label
        }
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
    if(len(p) == 3):
        p[0].place = getNewTmp("int")
    elif(len(p) == 4):
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
        if "ret_type" in p[1].data.keys():
            if "ret_type" in p[2].data.keys() and p[1].data["ret_type"] != p[2].data["ret_type"]:
                print("Error at line : " + str(p.lineno(0)) +
                      " :: " + "Return type mismatch")
                exit()
            else:
                p[0].data["ret_type"] = p[1].data["ret_type"]
        elif "ret_type" in p[2].data.keys():
            p[0].data["ret_type"] = p[2].data["ret_type"]

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
    '''selection_statement : IF L_PAREN expression R_PAREN statement'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i in [1, 2, 4, 6]):
                p_.data = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[3]], "condition")
    t2 = add_to_tree([None, p[5]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2], p[1].parse)
    p[0].data = setData(p, 5)
    p[0].after = getNewLabel("if_after")
    p[0].code = p[3].code + [quad("ifz", [p[3].place, p[0].after, p[3].place, p[0].after, ""], "ifz " +
                                  p[3].place + " goto->" + p[0].after)] + p[5].code + [quad("label", [p[0].after], p[0].after + " : ")]


def p_selection_statement_1(p):
    '''selection_statement : IF L_PAREN expression R_PAREN statement ELSE statement'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i in [1, 2, 4, 6]):
                p_.data = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[3]], "condition")
    t2 = add_to_tree([None, p[5]], "body")
    t3 = add_to_tree([None, p[7]], "else-body")
    p[0].parse = add_to_tree([p[0], t1, t2, t3], p[1].parse + p[6].parse)
    p[0].data = {}
    if "ret_type" in p[5].data.keys():
        if "ret_type" in p[7].data.keys() and p[5].data["ret_type"] == p[7].data["ret_type"]:
            print("Error at line : " + str(p.lineno(0)) +
                  " :: " + "Return type mismatch")
            exit()
        else:
            p[0].data["ret_type"] = p[5].data["ret_type"]
    elif "ret_type" in p[7].data.keys():
        p[0].data["ret_type"] = p[7].data["ret_type"]

    p[0].if_ = getNewLabel("if_part")
    p[0].else_ = getNewLabel("else_part")
    p[0].after = getNewLabel("if_after")

    tmp_code = [quad("ifz", [p[3].place,  p[0].else_, ""], "ifz " + p[3].place + " goto->" +
                     p[0].else_)] + p[5].code + [quad("goto", [p[0].after, "", ""], "goto->" + p[0].after)]
    p[0].code = p[3].code + [quad("label", [p[0].if_, "", ""], p[0].if_ + ":")] + ["    " + i for i in tmp_code] + [quad("label", [
        p[0].else_, "", ""], p[0].else_ + ":")] + ["    " + i for i in p[7].code] + [quad("label", [p[0].after, "", ""], p[0].after + ":")]


def p_selection_statement_2(p):
    '''selection_statement : SWITCH L_PAREN expression R_PAREN statement'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i in [1, 2, 4, 6]):
                p_.data = p[i]
            p[i] = p_

    t1 = add_to_tree([None, p[3]], "condition")
    t2 = add_to_tree([None, p[5]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2], p[1].parse)
    allowed_type = ["char", "int"]
    if p[3].data["type"] not in allowed_type:
        print("Error at line : " + str(p.lineno(0)) + " :: " +
              "Type not compatible with switch condition")
        exit()
    if len(set([c["value"] for c in p[5].code])) != len(p[5].code):
        print("Error at line : " + str(p.lineno(0)) + " :: " +
              "Same value is used more than one time in cases")
        exit()
    p[0].data = setData(p, 5)

    p[0].case = getNewLabel("switch_case")
    p[0].next = getNewLabel("switch_body")
    p[0].after = getNewLabel("switch_after")
    caselist = []
    nextlist = []
    test = p[3].place
    default_label = p[0].after
    for idx, val in enumerate([c["value"] for c in p[5].code]):
        if val == None:
            default_label = p[5].code[idx]["label"]
            continue
        tmp1 = getNewTmp("int")
        tmp2 = getNewTmp("int")
        caselist = caselist + [quad("=", [tmp1, str(val), ""], tmp1+" = "+str(val))] + [quad("-", [tmp2, test, tmp1], tmp2 +
                                                                                             " = "+test+" - "+tmp1), quad("ifz", [tmp2, p[5].code[idx]["label"], ""], "ifz "+tmp2+" goto->"+p[5].code[idx]["label"])]
    caselist = caselist + 
        [quad("goto", [default_label], "goto->" + default_label)]
    for idx, code in enumerate(p[5].code):
        tmp_code = code["statement"]
        tmp_code = [quad("goto", [p[0].after], "goto->"+p[0].after)
                    if re.fullmatch('[ ]*break', i) else i for i in tmp_code]
        nextlist = nextlist + [quad("label", [code["label"], "", ""], code["label"] + ":")] + [
            "    " + i for i in tmp_code]
    p[0].code = p[3].code + [quad("label", [p[0].case, "", ""], p[0].case + ":")] + ["    " + i for i in caselist] + [quad("label", [
        p[0].next, "", ""], p[0].next + ":")] + ["    " + i for i in nextlist] + [quad("label", [p[0].after, "", ""], p[0].after + ":")]


def p_iteration_statement_0(p):
    '''iteration_statement : WHILE L_PAREN expression R_PAREN statement'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1 or p[i] in ["while", '(', ')', ';']):
                p_.data = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[3]], "condition")
    t2 = add_to_tree([None, p[5]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2], p[1].parse)
    p[0].data = setData(p, 5)

    p[0].begin = getNewLabel("while_body")
    p[0].after = getNewLabel("while_after")
    tmp_code = p[3].code + [quad("ifz", [p[3].place, p[0].after], "ifz " + p[3].place +
                                 " goto->" + p[0].after)] + p[5].code + [quad("goto", [p[0].begin], "goto->" + p[0].begin)]
    tmp_code = [quad("goto", [p[0].after], "goto->"+p[0].after)
                if re.fullmatch('[ ]*break', i) else i for i in tmp_code]
    tmp_code = [quad("goto", [p[0].begin], "goto->"+p[0].begin)
                if re.fullmatch('[ ]*continue', i) else i for i in tmp_code]
    p[0].code = [quad("label", [p[0].begin, "", ""], p[0].begin + " : ")] + [
        "    " + i for i in tmp_code] + [quad("label", [p[0].after], p[0].after + " : ")]


def p_iteration_statement_1(p):
    '''iteration_statement : DO statement WHILE L_PAREN expression R_PAREN STMT_TERMINATOR'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1 or p[i] in ["while", '(', ')', ';']):
                p_.data = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[5]], "condition")
    t2 = add_to_tree([None, p[2]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2], p[1].parse + '-' + p[3].parse)
    p[0].data = setData(p, 2)

    p[0].begin = getNewLabel("do_body")
    p[0].after = getNewLabel("do_after")
    tmp_code = p[2].code + p[5].code + [quad(
        "ifnz", [p[5].place, p[0].begin, ""], "ifnz " + p[5].place + " goto->" + p[0].begin)]
    tmp_code = [quad("goto", [p[0].after], "goto->"+p[0].after)
                if re.fullmatch('[ ]*break', i) else i for i in tmp_code]
    tmp_code = [quad("goto", [p[0].begin], "goto->"+p[0].begin)
                if re.fullmatch('[ ]*continue', i) else i for i in tmp_code]
    p[0].code = [quad("label", [p[0].begin, "", ""], p[0].begin + " : ")] + [
        "    " + i for i in tmp_code] + [quad("label", [p[0].after], p[0].after + " : ")]


def p_iteration_statement_2(p):
    '''iteration_statement : FOR L_PAREN expression_statement expression_statement R_PAREN statement'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1 or p[i] in ["while", '(', ')', ';']):
                p_.data = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[3]], "initialisation")
    t2 = add_to_tree([None, p[4]], "stop condition")
    t3 = add_to_tree([None, p[6]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2, t3], p[1].parse)
    p[0].data = setData(p, 6)

    p[0].test = getNewLabel("for_test")
    p[0].body = p[0].test
    p[0].after = getNewLabel("for_after")
    tmp_code = p[4].code + [quad("ifz", [p[4].place, p[0].after], "ifz " + p[4].place +
                                 " goto->" + p[0].after)] + p[6].code + [quad("goto", [p[0].test], "goto->" + p[0].test)]
    tmp_code = [quad("goto", [p[0].after], "goto->"+p[0].after)
                if re.fullmatch('[ ]*break', i) else i for i in tmp_code]
    tmp_code = [quad("goto", [p[0].body], "goto->"+p[0].body)
                if re.fullmatch('[ ]*continue', i) else i for i in tmp_code]
    p[0].code = p[3].code + [quad("label", [p[0].test, "", ""], p[0].test + " : ")] + [
        "    " + i for i in tmp_code] + [quad("label", [p[0].after], p[0].after + " : ")]


def p_iteration_statement_3(p):
    '''iteration_statement : FOR L_PAREN expression_statement expression_statement expression R_PAREN statement'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1 or p[i] in ["while", '(', ')', ';']):
                p_.data = p[i]
            p[i] = p_
    t1 = add_to_tree([None, p[3]], "initialisation")
    t2 = add_to_tree([None, p[4]], "stop condition")
    t3 = add_to_tree([None, p[5]], "update")
    t4 = add_to_tree([None, p[7]], "body")
    p[0].parse = add_to_tree([p[0], t1, t2, t3, t4], p[1].parse)
    p[0].data = setData(p, 7)

    p[0].test = getNewLabel("for_test")
    p[0].body = getNewLabel("for_body")
    p[0].after = getNewLabel("for_after")
    tmp_code = p[4].code + [quad("ifz", [p[4].place, p[0].after], "ifz " + p[4].place + " goto->" +
                                 p[0].after)] + p[7].code + p[5].code + [quad("goto", [p[0].test], "goto->" + p[0].test)]
    tmp_code = [quad("goto", [p[0].after], "goto->"+p[0].after)
                if re.fullmatch('[ ]*break', i) else i for i in tmp_code]
    tmp_code = [quad("goto", [p[0].body], "goto->"+p[0].body)
                if re.fullmatch('[ ]*continue', i) else i for i in tmp_code]
    p[0].code = p[3].code + [quad("label", [p[0].test, "", ""], p[0].test + " : ")] + ["    " + i for i in tmp_code[:len(
        p[4].code + [quad("ifz", [p[4].place, p[0].after], "ifz " + p[4].place + " goto->" + p[0].after)] + p[7].code)]]
    p[0].code = p[0].code + [quad("label", [p[0].body], p[0].body + " : ")] + ["    " + i for i in tmp_code[len(
        p[4].code + [quad("ifz", [p[4].place, p[0].after], "ifz " + p[4].place + " goto->" + p[0].after)] + p[7].code):]]
    p[0].code = p[0].code + [quad("label", [p[0].after], p[0].after + " : ")]


def p_jump_statement(p):
    '''jump_statement : CONTINUE STMT_TERMINATOR
                      | BREAK STMT_TERMINATOR
                      | RETURN STMT_TERMINATOR
                      | RETURN expression STMT_TERMINATOR'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            if(i == 1 or p[i] == ';'):
                p_.data = p[i]
            p[i] = p_
    if(len(p) == 3):
        p[0].parse = add_to_tree([p[0]], p[1].parse)
        if(p[1].data == "return"):
            p[0].data["ret_type"] = "void"
            p[0].code = p[2].code+[quad("return", [], "return ")]
        else:
            p[0].code = [p[1].data]
    else:
        p[0].parse = add_to_tree([p[0], p[2]], p[1].parse)
        p[0].data["ret_type"] = p[2].data["type"]
        p[0].code = p[2].code + 
            [quad("return", [p[2].place, "", ""], "return "+p[2].place)]


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
        p[0].code = p[1].code.copy()+p[2].code.copy()


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
    '''function_definition : declaration_specifiers declarator compound_statement pop_scope'''
    for i in range(len(p)):
        if not isinstance(p[i], NODE):
            p_ = NODE()
            p_.parse = p[i]
            p[i] = p_
    # t1 = add_to_tree([None] + p[-1:], "body")
    t1 = list(toParse(p[-1:]))[0]
    # t2 = add_to_tree([None, p[1]], "return type")
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

    if(p[1].data["type"] != "void" and ((not isinstance(p[3].data, list) and "ret_type" not in p[3].data.keys()) or isinstance(p[3].data, list))):
        print("Error at line : " + str(p.lineno(0)) + " :: " +
              "Return type is not void, must include a return statement")
        exit()
    if not isCompatible(p[1].data["type"], p[3].data["ret_type"]):
        print("Error at line : " + str(p.lineno(0)) +
              " :: " + "Return type mismatch")
        exit()
    funcData, scp = checkEntry(p[2].data["name"], 0)
    funcData["ret_type"] = p[1].data["type"]
    funcData["func_offset"] = getOffset()
    updateEntry(p[2].data["name"], funcData)
    popOffset()


# Error rule for syntax errors
def p_error(p):
    print("Syntax Error: line " + str(p.lineno) + ":" +
          filename.split('/')[-1], "near", p.value)
    exit()


def p_empty(p):
    'empty :'
    print("i m here")


def p_push_scope(p):
    'push_scope :'
    pushScope()


def p_f_push_scope(p):
    'f_push_scope :'
    global currentScopeId
    global scopeTables
    if(currentScopeId):
        print("Error at line : " + str(p.lineno(0)) + " :: " +
              "Function can only be declared in global scope")
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
    pickle.dump(scopeTableList,f2)


if '__main__' == __name__:
    main()
