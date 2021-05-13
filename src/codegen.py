import re
import pickle
import operator


f1 = open("symTab.obj", "rb")
scopeTables = pickle.load(f1)
f2 = open("3AC.obj", "rb")
code3ac = pickle.load(f2)


currentScopeId = 0
FileName = ""
lineno = 0
asmcode = []


def checkEntry(identifier, scopeId=None):
    global scopeTables
    global currentScopeId

    identifier = str(identifier)
    if identifier.split('@')[0] == "tmp":
        identifier = identifier
    else:
        identifier = identifier.split('@')[0]

    if(scopeId is not None):
        symbol_table = scopeTables[scopeId]
        if symbol_table.lookUp(identifier):
            return (symbol_table.getDetail(identifier), scopeId)
        return (False, scopeId)
    else:
        for scope in range(len(scopeTables)):
            symbol_table = scopeTables[scope]
            if symbol_table.lookUp(identifier):
                return (symbol_table.getDetail(identifier), scope)
        return (False, scopeId)


def loadAddr(reg, var):
    global asmcode
    var = str(var)
    if "@" in var:
        if var.split('@')[0] == "tmp":
            var_entry = checkEntry(var)[0]
        else:
            var_entry = checkEntry(
                var.split('@')[0], int(var.split('@')[1]))[0]

        offset = str(var_entry["offset"])
        base = var_entry["base"]
        if base == "0":
            loadVar(reg, offset)
        elif base == "rbp":
            if "@" in offset:
                # offset is variable
                asmcode.append("push %esi")
                loadVar("esi", offset)
                asmcode.append("neg %esi")
                asmcode.append("lea (%ebp, %esi, 1), %" + reg)
                asmcode.append("pop %esi")
            else:
                # offset is int/constant
                asmcode.append("lea " + str(-int(offset)) + "(%ebp), %" + reg)
        else:
            print("error in load Addr | base is not rbp or zero")
            exit(-1)
    else:
        print("error in load Addr | var is not a variable | " + var)
        exit(-1)


def loadVar(reg, var):
    global asmcode
    var = str(var)
    if "@" in var:
        if var.split('@')[0] == "tmp":
            var_entry = checkEntry(var)[0]
        elif var.split('@')[0] == "gbl":
            asmcode.append("mov $" + var + ", %" + reg)
            return
        else:
            var_entry = checkEntry(var.split('@')[0], int(var.split('@')[1]))[0]

        offset = str(var_entry["offset"])
        base = str(var_entry["base"])
        type_ = var_entry["type"]

        if "@" in offset:
            # offset is variable
            if base == "0":
                loadVar("esi", offset)
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    asmcode.append("mov (%esi), %" + reg)
                elif type_ == "char":
                    asmcode.append("movb (%esi), %" + reg[1] + "l")
                else:
                    print("error in load Var | struct error in load")
                    exit(-1)
            elif base == "rbp":
                loadVar("esi", offset)
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    asmcode.append("neg %esi")
                    asmcode.append("mov (%ebp , %esi, 1), %" + reg)
                elif type_ == "char":
                    asmcode.append("neg %esi")
                    asmcode.append("movb (%ebp , %esi, 1), %" + reg[1] + "l")
                else:
                    print("error in load Var | struct error in load")
                    exit(-1)
            else:
                print("error in load Var | wrong base in load")
                exit(-1)
        else:
            # offset is int/constant
            if base == "0":
                print("error in load Var | constant offset with base 0")
                exit(-1)
            elif base == "rbp":
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    asmcode.append("mov " + str(-int(offset)) + "(%ebp), %" + reg)
                elif type_ == "char":
                    asmcode.append("movb " + str(-int(offset)) + "(%ebp), %" + reg[1] + "l")
                else:
                    print("error in load Var | struct error in load")
                    exit(-1)
            else:
                print("error in load Var | wrong base in load")
                exit(-1)
    else:
        if var[0] == "'" and var[2] == "'" and len(var) == 3:
            asmcode.append("movb $" + str(ord(var[1])) + ", %" + reg[1] + "l")
        elif var.lstrip("-").isdigit():
            asmcode.append("mov $" + var + ", %" + reg)
        else:
            print("error in load Var | " + var)
            exit(-1)


def storeVar(reg, var):
    global asmcode
    var = str(var)
    if "@" in var:
        if var.split('@')[0] == "tmp":
            var_entry = checkEntry(var)[0]
        else:
            var_entry = checkEntry(var.split('@')[0], int(var.split('@')[1]))[0]

        offset = str(var_entry["offset"])
        base = str(var_entry["base"])
        type_ = var_entry["type"]

        if "@" in offset:
            # offset is variable
            if base == "0":
                loadVar("edi", offset)
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    asmcode.append("mov %" + reg + ", (%edi)")
                elif type_ == "char":
                    asmcode.append("movb %" + reg[1] + "l" + ", (%edi)")
                else:
                    print("error in store Var | struct error in store | " + var)
                    exit(-1)
            elif base == "rbp":
                loadVar("edi", offset)
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    asmcode.append("neg %edi")
                    asmcode.append("mov %" + reg + ", (%ebp, %edi, 1)")
                elif type_ == "char":
                    asmcode.append("neg %edi")
                    asmcode.append("movb %" + reg[1] + "l" + ", (%ebp, %edi, 1)")
                else:
                    print("error in store Var | struct error in store | " + var)
                    exit(-1)
            else:
                print("error in store Var | wrong base in store")
                exit(-1)
        else:
            # offset is int/constant
            if base == "0":
                print("error in store Var | constant offset with base 0")
                exit(-1)
            elif base == "rbp":
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    asmcode.append("mov %" + reg + ", " + str(-int(offset)) + "(%ebp)")
                elif type_ == "char":
                    asmcode.append("movb %" + reg[1] + "l" + ", " + str(-int(offset)) + "(%ebp)")
                else:
                    print("error in store Var | struct error in store | " + var)
                    exit(-1)
            else:
                print("error in store Var | wrong base in store")
                exit(-1)
    else:
        print("error in store Var")
        exit(-1)


def movVar(srcOffset, srcBase, destOffset, destBase, size):
    if size == 4:
        reg = "edx"
        mov = "mov"
    if size == 2:
        reg = "dx"
        mov = "movw"
    if size == 1:
        reg = "dl"
        mov = "movb"

    if srcBase == "0":
        asmcode.append(mov + " (%" + srcOffset + "), %" + reg)
    if srcBase == "rbp":
        asmcode.append("neg %" + srcOffset)
        asmcode.append(mov + " (%ebp, %" + srcOffset + ", 1), %" + reg)
        asmcode.append("neg %" + srcOffset)
    if destBase == "0":
        asmcode.append(mov + " %" + reg + ", (%" + destOffset + ")")
    if destBase == "rbp":
        asmcode.append("neg %" + destOffset)
        asmcode.append(mov + " %" + reg + ", (%ebp, %" + destOffset + ", 1)")
        asmcode.append("neg %" + destOffset)


def addToOffset(base_s, base_d, size):
    if base_s == "0":
        asmcode.append("add $" + str(size) + ", %eax")
    else:
        asmcode.append("sub $" + str(size) + ", %eax")
    if base_d == "0":
        asmcode.append("add $" + str(size) + ", %ebx")
    else:
        asmcode.append("sub $" + str(size) + ", %ebx")


def op_add(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("add %ebx, %eax")
    storeVar("eax", out)


def op_sub(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("sub %ebx, %eax")
    storeVar("eax", out)


def op_mult(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("imul %ebx, %eax")
    storeVar("eax", out)


def op_div(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("mov $0, %edx")
    asmcode.append("idiv %ebx")
    storeVar("eax", out)


def op_modulo(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("mov $0, %edx")
    asmcode.append("idiv %ebx")
    storeVar("edx", out)


def op_lshift(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("bl", inp2)
    asmcode.append("shl %bl, %eax")
    storeVar("eax", out)


def op_rshift(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("bl", inp2)
    asmcode.append("shr %bl, %eax")
    storeVar("eax", out)


def op_inc(instr):
    inp = instr[0]
    loadVar("eax", inp)
    asmcode.append("inc %eax")
    storeVar("eax", inp)


def op_dec(instr):
    inp = instr[0]
    loadVar("eax", inp)
    asmcode.append("dec %eax")
    storeVar("eax", inp)


def op_assign(instr):
    out, inp = instr
    if "@" in inp:
        if inp.split('@')[0] == "gbl":
            loadVar("eax", inp)
            storeVar("eax", out)
            return

        var_entry = checkEntry(inp)[0] if inp.split('@')[0] == "tmp" else checkEntry(inp.split('@')[0], int(inp.split('@')[1]))[0]
        type_ = var_entry["type"]
        if "*" in type_ or type_ in ["int", "char", "float"]:
            loadVar("eax", inp)
            storeVar("eax", out)
        else:
            var_entry_ = checkEntry(out)[0] if out.split('@')[0] == "tmp" else checkEntry(out.split('@')[0], int(out.split('@')[1]))[0]
            loadVar("eax", var_entry["offset"])
            loadVar("ebx", var_entry_["offset"])

            for i in range(0, var_entry["size"]):
                movVar("eax", var_entry["base"], "ebx", var_entry_["base"], 1)
                addToOffset(var_entry["base"], var_entry_["base"], 1)
    else:
        var_entry = checkEntry(out)[0] if out.split('@')[0] == "tmp" else checkEntry(out.split('@')[0], int(out.split('@')[1]))[0]
        type_ = var_entry["type"]
        if type_ == "char":
            if(inp == "''"):
                inp = "' '"
            asmcode.append("mov $" + str(ord(inp[1])) + ", %eax")
            storeVar("eax", out)
        else:
            asmcode.append("mov $" + inp + ", %eax")
            storeVar("eax", out)


def op_bitwise_and(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("and %ebx, %eax")
    storeVar("eax", out)


def op_bitwise_or(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("or %ebx, %eax")
    storeVar("eax", out)


def op_bitwise_xor(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("xor %ebx, %eax")
    storeVar("eax", out)


def op_bitwise_not(instr):
    out, inp = instr
    loadVar("eax", inp)
    asmcode.append("not %eax")
    storeVar("eax", out)


def op_logical_and(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("and %ebx, %eax")
    asmcode.append("cmp $0, %eax")
    asmcode.append("mov $0, %eax")
    asmcode.append("setne %al")
    storeVar("eax", out)


def op_logical_or(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("or %ebx, %eax")
    asmcode.append("cmp $0, %eax")
    asmcode.append("mov $0, %eax")
    asmcode.append("setne %al")
    storeVar("eax", out)


def op_logical_not(instr):
    out, inp = instr
    loadVar("eax", inp)
    asmcode.append("cmp $0, %eax")
    asmcode.append("mov $0, %eax")
    asmcode.append("sete %al")
    storeVar("eax", out)


def op_ifz(instr):
    var, label = instr
    loadVar("eax", var)
    asmcode.append("cmp $0, %eax")
    asmcode.append("je " + label)


def op_ifnz(instr):
    var, label = instr
    loadVar("eax", var)
    asmcode.append("cmp $0, %eax")
    asmcode.append("jne " + label)


def op_lea(instr):
    out, inp = instr
    loadAddr("eax", inp)
    storeVar("eax", out)


def op_comp_lt(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("cmp %ebx, %eax")
    asmcode.append("mov $0, %ecx")
    asmcode.append("setl %cl")
    storeVar("ecx", out)


def op_comp_gt(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("cmp %ebx, %eax")
    asmcode.append("mov $0, %ecx")
    asmcode.append("setg %cl")
    storeVar("ecx", out)


def op_comp_lte(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("cmp %ebx, %eax")
    asmcode.append("mov $0, %ecx")
    asmcode.append("setle %cl")
    storeVar("ecx", out)


def op_comp_gte(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("cmp %ebx, %eax")
    asmcode.append("mov $0, %ecx")
    asmcode.append("setge %cl")
    storeVar("ecx", out)


def op_comp_eq(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("cmp %ebx, %eax")
    asmcode.append("mov $0, %ecx")
    asmcode.append("sete %cl")
    storeVar("ecx", out)


def op_comp_neq(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("cmp %ebx, %eax")
    asmcode.append("mov $0, %ecx")
    asmcode.append("setne %cl")
    storeVar("ecx", out)


def op_label(instr):
    label = instr[0]
    asmcode.append(str(label) + ":")


def op_goto(instr):
    label = instr[0]
    asmcode.append("jmp " + label)


def op_pushparam(instr):
    inp = instr[0]
    var_entry = checkEntry(inp)[0] if inp.split('@')[0] == "tmp" else checkEntry(inp.split('@')[0], int(inp.split('@')[1]))[0]
    if var_entry["type"][-1] == "*":
        if("is_array" in var_entry.keys() and var_entry["is_array"] is True):
            loadAddr("eax", inp)
        else:
            loadVar("eax", inp)
        asmcode.append("push %eax")
    elif var_entry["type"] in ["char", "int", "float"]:
        loadVar("eax", inp)
        asmcode.append("push %eax")
    else:
        loadVar("eax", var_entry["offset"])
        asmcode.append("sub $" + str(var_entry["size"]) + ", %esp")
        asmcode.append("mov %esp, %ebx")

        for i in range(0, var_entry["size"]):
            movVar("eax", var_entry["base"], "ebx", "0", 1)
            addToOffset(var_entry["base"], "0", 1)


def op_removeparam(instr):
    size = instr[0]
    if not size.isdigit():
        print(" pop size should be int")
        exit(-1)
    asmcode.append("add $" + size + ", %esp")


def op_fcall(instr):
    if(len(instr) == 2):
        out, label = instr
        asmcode.append("call " + label)
        storeVar("eax", out)
    else:
        label = instr[0]
        asmcode.append("call " + label)


def op_beginfunc(instr):
    size = instr[0]
    if not size.isdigit():
        print(" expand size should be int")
        exit(-1)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp, %ebp")
    asmcode.append("sub $" + size + ", %esp")
    asmcode.append("push %ebx")
    asmcode.append("push %ecx")
    asmcode.append("push %edx")
    asmcode.append("push %esi")
    asmcode.append("push %edi")


def op_return(instr):
    if(len(instr) == 1):
        inp = instr[0]
        loadVar("eax", inp)
    else:
        asmcode.append("nop")
    asmcode.append("pop %ebx")
    asmcode.append("pop %ecx")
    asmcode.append("pop %edx")
    asmcode.append("pop %esi")
    asmcode.append("pop %edi")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")
    asmcode.append("ret")


def op_malloc(instr):
    out, size = instr
    loadVar("edi", size)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp, %ebp")
    asmcode.append("push %edi")
    asmcode.append("call malloc")
    asmcode.append("add $4, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")
    storeVar("eax", out)


def op_free(instr):
    inp = instr[0]
    loadVar("edi", inp)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp, %ebp")
    asmcode.append("push %edi")
    asmcode.append("call malloc")
    asmcode.append("add $4, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_printi(instr):
    inp = instr[0]
    loadVar("eax", inp)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp, %ebp")
    asmcode.append("push %eax")
    asmcode.append("push $printi_fmt")
    asmcode.append("call printf")
    asmcode.append("add $8, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_printc(instr):
    inp = instr[0]
    loadVar("eax", inp)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp, %ebp")
    asmcode.append("push %eax")
    asmcode.append("push $printc_fmt")
    asmcode.append("call printf")
    asmcode.append("add $8, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_printnl(instr):
    asmcode.append("push %ebp")
    asmcode.append("mov %esp, %ebp")
    asmcode.append("push %eax")
    asmcode.append("push $printnl_fmt")
    asmcode.append("call printf")
    asmcode.append("add $8, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_scani(instr):
    inp = instr[0]
    loadAddr("eax", inp)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp, %ebp")
    asmcode.append("push %eax")
    asmcode.append("push $scani_fmt")
    asmcode.append("call scanf")
    asmcode.append("add $8, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_scanc(instr):
    inp = instr[0]
    loadAddr("eax", inp)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp, %ebp")
    asmcode.append("push %eax")
    asmcode.append("push $scanc_fmt")
    asmcode.append("call scanf")
    asmcode.append("add $8, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def gencode(instr):
    if(instr["op"] == "+"):
        op_add(instr["arg"])
    elif instr["op"] == "-":
        op_sub(instr["arg"])
    elif instr["op"] == "*":
        op_mult(instr["arg"])
    elif instr["op"] == "/":
        op_div(instr["arg"])
    elif instr["op"] == "%":
        op_modulo(instr["arg"])
    elif instr["op"] == "<<":
        op_lshift(instr["arg"])
    elif instr["op"] == ">>":
        op_rshift(instr["arg"])
    elif instr["op"] == "++":
        op_inc(instr["arg"])
    elif instr["op"] == "--":
        op_dec(instr["arg"])
    elif instr["op"] == "=":
        op_assign(instr["arg"])
    elif instr["op"] == "&":
        op_bitwise_and(instr["arg"])
    elif instr["op"] == "|":
        op_bitwise_or(instr["arg"])
    elif instr["op"] == "^":
        op_bitwise_xor(instr["arg"])
    elif instr["op"] in ["~"]:
        op_bitwise_not(instr["arg"])
    elif instr["op"] == "&&":
        op_logical_and(instr["arg"])
    elif instr["op"] == "||":
        op_logical_or(instr["arg"])
    elif instr["op"] in ["!"]:
        op_logical_not(instr["arg"])
    elif instr["op"] == "ifz":
        op_ifz(instr["arg"])
    elif instr["op"] == "ifnz":
        op_ifnz(instr["arg"])
    elif instr["op"] == "lea":
        op_lea(instr["arg"])
    elif instr["op"] == "<":
        op_comp_lt(instr["arg"])
    elif instr["op"] == ">":
        op_comp_gt(instr["arg"])
    elif instr["op"] == "<=":
        op_comp_lte(instr["arg"])
    elif instr["op"] == ">=":
        op_comp_gte(instr["arg"])
    elif instr["op"] == "==":
        op_comp_eq(instr["arg"])
    elif instr["op"] == "!=":
        op_comp_neq(instr["arg"])
    elif instr["op"] == "label":
        op_label(instr["arg"])
    elif instr["op"] == "goto":
        op_goto(instr["arg"])
    elif instr["op"] == "pushParam":
        op_pushparam(instr["arg"])
    elif instr["op"] == "removeParams":
        op_removeparam(instr["arg"])
    elif instr["op"] == "fCall":
        op_fcall(instr["arg"])
    elif instr["op"] == "beginFunc":
        op_beginfunc(instr["arg"])
    elif instr["op"] == "return":
        op_return(instr["arg"])
    elif instr["op"] == "malloc":
        op_malloc(instr["arg"])
    elif instr["op"] == "free":
        op_free(instr["arg"])
    elif instr["op"] == "printi":
        op_printi(instr["arg"])
    elif instr["op"] == "printc":
        op_printc(instr["arg"])
    elif instr["op"] == "printnl":
        op_printnl(instr["arg"])
    elif instr["op"] == "scani":
        op_scani(instr["arg"])
    elif instr["op"] == "scanc":
        op_scanc(instr["arg"])
    
    elif instr["op"][:5] == "float":
        print("error: float is not done")
        exit(-1)


if __name__ == "__main__":
    asmcode.append(".data")
    asmcode.append('printc_fmt:\n\t\t .string "%c"')
    asmcode.append('printi_fmt:\n\t\t .string "%d"')
    asmcode.append('printf_fmt:\n\t\t .string "%f"')
    asmcode.append('printnl_fmt:\n\t\t .string "\\n"')
    asmcode.append('scanc_fmt:\n\t\t .string "%c"')
    asmcode.append('scani_fmt:\n\t\t .string "%d"')
    for globl in scopeTables[0].table.items():
        data = globl[1]
        if isinstance(data, dict) and "base" in data.keys() and "offset" in data.keys():
            asmcode.append(str(data["offset"]) + ':\n\t\t .zero ' + str(data["size"]) + ' ')
    asmcode.append(".text")
    asmcode.append(".global main")
    asmcode.append(".type main, @function")

    for code in code3ac:
        lineno = lineno + 1
        code = code.replace(' ', '')
        stmt = []
        for arg in code.split("$"):
            if arg != '':
                stmt.append(arg)
        instr = {"op": stmt[1].strip(), "arg": stmt[2:-1]}
        currentScopeId = int(stmt[-1])
        gencode(instr)

    asmfile = open('asmfile.s', 'w')
    for asmcode in asmcode:
        asmcode = asmcode.replace('|', '').replace('#', '').replace('@', '')
        if asmcode[-1] == ':': asmfile.write(asmcode + "\n") #label
        else:
            asmfile.write("\t" + asmcode + "\n")
