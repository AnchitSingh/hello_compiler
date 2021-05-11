import re
import pickle
import operator
import struct


f1 = open("symTab.obj", "rb")
scopeTables = pickle.load(f1)
currentScopeId = 0

f2 = open("3AC.obj", "rb")
code3ac = pickle.load(f2)

FileName = ""
lineno = 0
asmcode = []


def binary(float_):
    return bin(struct.unpack('!i', struct.pack('!f', float_))[0])

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
        return False
    else:
        for scope in range(len(scopeTables)):
            symbol_table = scopeTables[scope]
            if symbol_table.lookUp(identifier):
                return (symbol_table.getDetail(identifier), scope)
        return False


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
                # offset is int
                asmcode.append("lea -" + offset + "(%ebp), %" + reg)
        else:
            print("error in load Addr, base is not rbp or zero ")
            exit(-1)
    else:
        print("var is not a variable ")
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
            var_entry = checkEntry(var.split('@')[0], int(var.split('@')[1]))

        offset = str(var_entry["offset"])
        base = str(var_entry["base"])
        type_ = var_entry["type"]

        if "@" in offset:
            # offset is variable
            r = "esi"
            if base == "0":
                loadVar("esi", offset)
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    asmcode.append("mov (%esi), %" + reg)
                elif type_ == "char":
                    asmcode.append("movb (%esi), %" + reg[1] + "l")
                else:
                    print("struct error in load")
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
                    print(" struct error in load")
                    exit(-1)
            else:
                print("wrong base in load")
                exit(-1)
        else:
            # offset is int
            if base == "0":
                print("constant offset with base 0")
                exit(-1)
            elif base == "rbp":
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    asmcode.append("mov -" + str(-int(offset)) + "(%ebp), %" + reg)
                elif type_ == "char":
                    asmcode.append("movb -" + offset +
                                   "(%ebp), %" + reg[1] + "l")
                else:
                    print("class error in load")
                    exit(-1)
            else:
                print("wrong base in load")
                exit(-1)
    else:
        if var[0] == "'" and var[2] == "'" and len(var) == 3:
            asmcode.append("movb $" + str(ord(var[1]))+" , %" + reg[1] + "l")
        elif var.lstrip("-").isdigit():
            asmcode.append("mov $" + var + " , %" + reg)
        else:
            print(var + " | Error in load var")
            exit(-1)


def storeVar(reg, var):
    global asmcode
    var = str(var)
    if "@" in var:
        if var.split('@')[0] == "tmp":
            var_entry = checkEntry(var)[0]
        else:
            var_entry = checkEntry(var.split('@')[0], int(var.split('@')[1]))

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
                    print(var, " struct error in store")
                    exit(-1)
            elif base == "rbp":
                loadVar("edi", offset)
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    asmcode.append("neg %edi")
                    asmcode.append("mov %" + reg + ", (%ebp , %edi, 1)")
                elif type_ == "char":
                    asmcode.append("neg %edi")
                    asmcode.append(
                        "movb %" + reg[1] + "l" + ", (%ebp , %edi, 1)")
                else:
                    print(var, " struct error in store")
                    exit(-1)
            else:
                print("wrong base in store")
                exit(-1)
        else:
            # offset is int
            if base == "0":
                print("error : constant offset with base 0")
                exit(-1)
            elif base == "rbp":
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    asmcode.append("mov %" + reg + " , " + str(-int(offset)) + "(%ebp)")
                elif type_ == "char":
                    asmcode.append(
                        "movb %" + reg[1] + "l" + " , -" + offset + "(%ebp)")
                else:
                    print(type_, var, " struct error in store")
                    exit(-1)
            else:
                print("wrong base in store")
                exit(-1)
    else:
        print("Error in storing var")
        exit(-1)


def loadFloatVar(var):
    global asmcode
    var = str(var)
    if "@" in var:
        if var.split('@')[0] == "tmp":
            var_entry = checkEntry(var, "all")["var"]
        else:
            var_entry = checkEntry(var.split('@')[0], int(var.split('@')[1]))

        offset = str(var_entry["offset"])
        base = str(var_entry["base"])
        type_ = var_entry["type"]
        if "@" in offset:
            # offset in variable
            if base == "0":
                loadVar("esi", offset)
                if type_ == "int":
                    asmcode.append("fild " + "(%esi)")
                elif type_ == "float":
                    asmcode.append("fld " + "(%esi)")
                else:
                    print("error in load float")
                    exit(-1)
            elif base == "rbp":
                loadVar("esi", offset)
                if type_ == "int":
                    asmcode.append("neg %esi")
                    asmcode.append("fild (%ebp , %esi, 1)")
                elif type_ == "float":
                    asmcode.append("neg %esi")
                    asmcode.append("fld (%ebp , %esi, 1)")
                else:
                    print("error in load float")
                    exit(-1)
            else:
                print("wrong base in load")
                exit(-1)
        else:
            if type_ == "int":
                asmcode.append("fild -" + offset + "(%ebp)")
            elif type_ == "float":
                asmcode.append("fld -" + offset + "(%ebp)")
            else:
                print("error in load float")
                exit(-1)
    else:
        pass
        print("var is not var")
        exit(-1)


def storeFloatVar(var):
    global asmcode
    var = str(var)
    if "@" in var:
        if var.split('@')[0] == "tmp":
            var_entry = checkEntry(var, "all")["var"]
        else:
            var_entry = checkEntry(var.split('@')[0], int(var.split('@')[1]))

        offset = str(var_entry["offset"])
        base = str(var_entry["base"])
        if "@" in offset:
            if base == "0":
                loadVar("esi", offset)
                asmcode.append("fstp " + "(%esi)")
            elif base == "rbp":
                loadVar("esi", offset)
                asmcode.append("neg %esi")
                asmcode.append("fstp (%ebp , %esi, 1)")
            else:
                print("wrong base in load")
                exit(-1)
        else:
            asmcode.append("fstp -" + offset + "(%ebp)")
    else:
        pass
        print("verror in store float")
        exit(-1)


def movVar(srcOffset, srcBase, destOffset, destBase, size=8):
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
        asmcode.append(mov + " (%ebp, %" + srcOffset + ",1) , %" + reg)
        asmcode.append("neg %" + srcOffset)

    if destBase == "0":
        asmcode.append(mov + " %" + reg + ", (%" + destOffset + ")")

    if destBase == "rbp":
        asmcode.append("neg %" + destOffset)
        asmcode.append(mov + " %" + reg + ", (%ebp, %" + destOffset + ",1)")
        asmcode.append("neg %" + destOffset)

def op_print_int(instr):
    to_print = instr[0]
    loadVar("eax", to_print)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp,%ebp")
    asmcode.append("push %eax")
    asmcode.append("push $print_fmt_int")
    asmcode.append("call printf")
    asmcode.append("add  $8, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_print_char(instr):
    to_print = instr[0]
    loadVar("eax", to_print)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp,%ebp")
    asmcode.append("push %eax")
    asmcode.append("push $print_fmt_char")
    asmcode.append("call printf")
    asmcode.append("add  $8, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_print_hex(instr):
    to_print = instr[0]
    loadVar("eax", to_print)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp,%ebp")
    asmcode.append("push %eax")
    asmcode.append("push $print_fmt_hex")
    asmcode.append("call printf")
    asmcode.append("add  $8, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_print_float(instr):
    to_print = instr[0]
    loadFloatVar(to_print)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp,%ebp")
    asmcode.append("sub $4, %esp")
    asmcode.append("fstp -4(%esp)")
    asmcode.append("push $print_fmt_float")
    asmcode.append("call printf")
    asmcode.append("add  $4, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_malloc(instr):
    to_malloc, size = instr
    loadVar("edi", size)

    asmcode.append("push %ebp")
    asmcode.append("mov %esp,%ebp")
    asmcode.append("push %edi")
    asmcode.append("call malloc")
    asmcode.append("add $4, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")
    storeVar("eax", to_malloc)


def op_free(instr):
    to_free = instr[0]
    loadVar("edi", to_free)

    asmcode.append("push %ebp")
    asmcode.append("mov %esp,%ebp")
    asmcode.append("push %edi")
    asmcode.append("call malloc")
    asmcode.append("add $4, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_scan_int(instr):
    to_scan_int = instr[0]
    loadAddr("eax", to_scan_int)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp,%ebp")
    asmcode.append("push %eax")
    asmcode.append("push $scan_fmt_int")
    asmcode.append("call scanf")
    asmcode.append("add  $8, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_scan_char(instr):
    to_scan_int = instr[0]
    loadAddr("eax", to_scan_int)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp,%ebp")
    asmcode.append("push %eax")
    asmcode.append("push $scan_fmt_char")
    asmcode.append("call scanf")
    asmcode.append("add  $8, %esp")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")


def op_add(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("add %ebx, %eax")
    storeVar("eax", out)


def op_float_add(instr):
    out, inp1, inp2 = instr
    loadFloatVar(inp1)
    loadAddr("eax", inp2)
    asmcode.append("fadd (%eax)")
    storeFloatVar(out)


def op_sub(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("sub %ebx, %eax")
    storeVar("eax", out)


def op_float_sub(instr):
    out, inp1, inp2 = instr
    loadFloatVar(inp1)
    loadAddr("eax", inp2)
    asmcode.append("fsub (%eax)")
    storeFloatVar(out)


def op_mult(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("imul %ebx, %eax")
    storeVar("eax", out)


def op_float_mult(instr):
    out, inp1, inp2 = instr
    loadFloatVar(inp1)
    loadAddr("eax", inp2)
    asmcode.append("fmul (%eax)")
    storeFloatVar(out)


def op_div(instr):
    # idiv %ebx — divide the contents of EDX:EAX by the contents of EBX. Place the quotient in EAX and the remainder in EDX.
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("mov $0, %edx")
    asmcode.append("idiv %ebx")
    storeVar("eax", out)


def op_float_div(instr):
    out, inp1, inp2 = instr
    loadFloatVar(inp1)
    loadAddr("eax", inp2)
    asmcode.append("fdiv (%eax)")
    storeFloatVar(out)


def op_modulo(instr):
    # idiv %ebx — divide the contents of EDX:EAX by the contents of EBX. Place the quotient in EAX and the remainder in EDX.
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("mov $0, %edx")
    asmcode.append("idiv %ebx")
    storeVar("edx", out)

def op_lshift(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("cl", inp2)
    asmcode.append("shl %cl, %eax")
    storeVar("eax", out)


def op_rshift(instr):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("cl", inp2)
    asmcode.append("shr %cl, %eax")
    storeVar("eax", out)


def op_inc(instr):
    inp = instr[0]
    loadVar("eax", inp)
    asmcode.append("inc  %eax")
    storeVar("eax", inp)


def op_dec(instr):
    inp = instr[0]
    loadVar("eax", inp)
    asmcode.append("dec  %eax")
    storeVar("eax", inp)


def op_logical_dual(instr, lt):
    out, inp1, inp2 = instr

    def log_op(x):
        d = {
            "&": "and ",
            "|": "or ",
            "^": "xor ",
            "&&": "and ",
            "||": "or ",
        }
        return d[x]

    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append(log_op(lt) + " %ebx, %eax")
    if lt == "&&" or lt == "||":
        asmcode.append("cmp $0, %eax")
        asmcode.append("mov $0, %eax")
        asmcode.append("setne %al")

    storeVar("eax", out)

def op_bitwise_not(instr):
    out, inp = instr
    loadVar("eax", inp)
    asmcode.append("not %eax")
    storeVar("eax", out)

def op_logical_not(instr):
    out, inp = instr
    loadVar("eax", inp)

    asmcode.append("cmp $0, %eax")
    asmcode.append("mov $0, %eax")
    asmcode.append("sete %al")

    storeVar("eax", out)

def op_comp(instr, comp):
    out, inp1, inp2 = instr
    loadVar("eax", inp1)
    loadVar("ebx", inp2)
    asmcode.append("cmp %ebx, %eax")
    asmcode.append("mov $0, %ecx")
    if comp == "<":
        asmcode.append("setl %cl")
    elif comp == ">":
        asmcode.append("setg %cl")
    elif comp == "<=":
        asmcode.append("setle %cl")
    elif comp == ">=":
        asmcode.append("setge %cl")
    elif comp == "==":
        asmcode.append("sete %cl")
    elif comp == "!=":
        asmcode.append("setne %cl")

    storeVar("ecx", out)

def op_float_comp(instr, comp):
    out, inp1, inp2 = instr
    loadFloatVar(inp2)
    loadFloatVar(inp1)
    asmcode.append("fcomip")
    asmcode.append("fstp %st(0)")
    asmcode.append("mov $0, %ecx")
    if comp == "float<":
        asmcode.append("setb %cl")
    elif comp == "float>":
        asmcode.append("seta %cl")
    elif comp == "float<=":
        asmcode.append("setbe %cl")
    elif comp == "float>=":
        asmcode.append("setae %cl")
    elif comp == "float==":
        asmcode.append("sete %cl")
    elif comp == "float!=":
        asmcode.append("setne %cl")

    storeVar("ecx", out)

def op_float_assign(instr):
    out, inp = instr
    if "@" in inp:
        loadFloatVar(inp)
        storeFloatVar(out)
    else:
        # it is constant assignment like a = 1.4 ;
        dec = float(str(inp))
        bin_ = binary(dec)
        asmcode.append("mov $" + str(bin_) + " ,%eax")
        storeVar("eax", out)

def op_assign(instr):
    out, inp = instr
    if "@" in inp:
        if inp.split('@')[0] == "gbl":
            loadVar("eax", inp)
            storeVar("eax", out)
            return

        var_entry = checkEntry(inp, "all")["var"] if inp.split('@')[0] == "tmp" else checkEntry(inp.split('@')[0], int(inp.split('@')[1]))
        type_ = var_entry["type"]
        if "|" in type_ or type_ in ["int", "char", "float"]:
            loadVar("eax", inp)
            storeVar("eax", out)
        else:
            offset = var_entry["offset"]
            base = var_entry["base"]
            size = var_entry["size"]
            inp = out
            var_entry = checkEntry(inp, "all")["var"] if inp.split('@')[0] == "tmp" else checkEntry(inp.split('@')[0], int(inp.split('@')[1]))
            offset_d = var_entry["offset"]
            base_d = var_entry["base"]
            size_d = var_entry["size"]
            loadVar("eax", offset)
            loadVar("ebx", offset_d)

            def add_to_offset(base, base_d, size):
                if base == "0":
                    asmcode.append("add $" + str(size) + ", %eax")
                else:
                    asmcode.append("sub $" + str(size) + ", %eax")
                if base_d == "0":
                    asmcode.append("add $" + str(size) + ", %ebx")
                else:
                    asmcode.append("sub $" + str(size) + ", %ebx")
                # if size % 4 == 0:
                #     for i in range(0, size, 4):
                #         movVar("eax", base, "ebx", base_d, 4)
                #         add_to_offset(base,base_d, 4)
                # elif size % 2 == 0 :
                #     for i in range(0, size % 4, 2 ):
                #         movVar("eax", base, "ebx", base_d, 2)
                #         add_to_offset(base,base_d, 2)
                # else:
                #     for i in range(0, size, 1 ):
                #         movVar("eax", base, "ebx", base_d, 1)
                #         add_to_offset(base,base_d, 1)
            for i in range(0, size, 1):
                movVar("eax", base, "ebx", base_d, 1)
                add_to_offset(base, base_d, 1)

    else:
        # it is constant assignment like a =1;
        var_entry = checkEntry(out, "all")["var"] if out.split('@')[0] == "tmp" else checkEntry(out.split('@')[0], int(out.split('@')[1]))
        type_ = var_entry["type"]
        if type_ == "char":
            asmcode.append("mov $" + str(ord(inp[1])) + ",%eax")
            storeVar("eax", out)
        else:
            asmcode.append("mov $" + inp + ", %eax")
            storeVar("eax", out)

def op_label(instr):
    label = instr[0]
    asmcode.append(str(label) + ":")

def op_ifnz(instr):
    var = instr[0]
    label = instr[1]
    loadVar("eax", var)
    asmcode.append("cmp $0 , %eax ")
    asmcode.append("jne " + label)

def op_ifz(instr):
    var = instr[0]
    label = instr[1]
    loadVar("eax", var)
    asmcode.append("cmp $0 , %eax ")
    asmcode.append("je " + label)

def op_goto(instr):
    label = instr[0]
    asmcode.append("jmp " + label)

def op_lea(instr):
    out, inp = instr
    loadAddr("eax", inp)
    storeVar("eax", out)

def op_pushParam(instr):
    inp = instr[0]
    var_entry = checkEntry(inp, "all")["var"] if inp.split('@')[0] == "tmp" else checkEntry(inp.split('@')[0], int(inp.split('@')[1]))
    if "|" in var_entry["type"] and var_entry["type"][-1] == "a":
        # this is array
        loadAddr("eax", inp)
        asmcode.append("push %eax")
    elif "|" in var_entry["type"]:
        # this is pointer
        loadVar("eax", inp)
        asmcode.append("push %eax")
    elif var_entry["type"] in ["int", "char", "float"]:
        loadVar("eax", inp)
        asmcode.append("push %eax")
    else:
        offset = var_entry["offset"]
        base = var_entry["base"]
        size = var_entry["size"]

        base_d = "0"
        loadVar("eax", offset)
        asmcode.append("sub $" + str(size) + ", %esp")
        asmcode.append("mov %esp, %ebx")

        def add_to_offset(base, base_d, size):
            if base == "0":
                asmcode.append("add $" + str(size) + ", %eax")
            else:
                asmcode.append("sub $" + str(size) + ", %eax")
            if base_d == "0":
                asmcode.append("add $" + str(size) + ", %ebx")
            else:
                asmcode.append("sub $" + str(size) + ", %ebx")

        for i in range(0, size, 1):
            movVar("eax", base, "ebx", base_d, 1)
            add_to_offset(base, base_d, 1)

def op_fcall(instr):
    out, label = instr
    asmcode.append("call " + label)
    storeVar("eax", out)

def op_removeParam(instr):
    pop_size = instr[0]
    if not pop_size.isdigit():
        print(" pop size should be int")
        exit(-1)

    asmcode.append("add " + pop_size + " %esp")

def op_beginFunc(instr):
    expand_size = instr[0]
    if not expand_size.isdigit():
        print(" expand size should be int")
        exit(-1)
    asmcode.append("push %ebp")
    asmcode.append("mov %esp, %ebp")
    asmcode.append("sub $" + expand_size + ", %esp")
    asmcode.append("push %ebx")
    asmcode.append("push %ecx")
    asmcode.append("push %edx")
    asmcode.append("push %esi")
    asmcode.append("push %edi")

def op_return(instr):
    ret_val = instr[0]
    loadVar("eax", ret_val)
    asmcode.append("pop %ebx")
    asmcode.append("pop %ecx")
    asmcode.append("pop %edx")
    asmcode.append("pop %esi")
    asmcode.append("pop %edi")
    asmcode.append("mov %ebp, %esp")
    asmcode.append("pop %ebp")
    asmcode.append("ret ")


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
    elif instr["op"] in ["&&", "||", "|", "&"]:
        op_logical_dual(instr["arg"], instr["op"])
    elif instr["op"] in ["!"]:
        op_logical_not(instr["arg"])
    elif instr["op"] in ["~"]:
        op_bitwise_not(instr["arg"])
    elif instr["op"] == "label":
        op_label(instr["arg"])
    elif instr["op"] == "ifz":
        op_ifz(instr["arg"])
    elif instr["op"] == "ifnz":
        op_ifnz(instr["arg"])
    elif instr["op"] == "lea":
        op_lea(instr["arg"])
    elif instr["op"] in ["<", ">", "==", "<=", ">=", "!="]:
        op_comp(instr["arg"], instr["op"])
    elif instr["op"] == "goto":
        op_goto(instr["arg"])
    elif instr["op"] == "PushParam":
        op_pushParam(instr["arg"])
    elif instr["op"] == "Fcall":
        op_fcall(instr["arg"])
    elif instr["op"] == "BeginFunc":
        op_beginFunc(instr["arg"])
    elif instr["op"] == "return":
        op_return(instr["arg"])
    elif instr["op"] == "print_int":
        op_print_int(instr["arg"])
    elif instr["op"] == "print_char":
        op_print_char(instr["arg"])
    elif instr["op"] == "print_float":
        op_print_float(instr["arg"])
    elif instr["op"] == "scan_int":
        op_scan_int(instr["arg"])
    elif instr["op"] == "scan_char":
        op_scan_char(instr["arg"])
    elif instr["op"] == "malloc":
        op_malloc(instr["arg"])
    elif instr["op"] == "free":
        op_free(instr["arg"])
    elif instr["op"] == "float=":
        op_float_assign(instr["arg"])
    elif instr["op"] == "float+":
        op_float_add(instr["arg"])
    elif instr["op"] == "float-":
        op_float_sub(instr["arg"])
    elif instr["op"] == "float*":
        op_float_mult(instr["arg"])
    elif instr["op"] == "float/":
        op_float_div(instr["arg"])
    elif instr["op"] in ["float<", "float>", "float==", "float<=", "float>=", "float!="]:
        op_float_comp(instr["arg"], instr["op"])


if __name__ == "__main__":

    asmcode.append(".data")
    asmcode.append('print_fmt_int:\n\t\t .string "%d " ')
    asmcode.append('print_fmt_char:\n\t\t .string "%c" ')
    asmcode.append('print_fmt_float:\n\t\t .string "%f" ')
    asmcode.append('scan_fmt_int:\n\t\t .string "%d" ')
    asmcode.append('scan_fmt_char:\n\t\t .string "%c" ')
    for j in scopeTables[0].table.items():
        if isinstance(j[1], dict) and "base" in j[1].keys() and "offset" in j[1].keys():
            asmcode.append(str(j[1]["offset"]) + ':\n\t\t .zero ' + str(j[1]["size"]) + ' ')
    asmcode.append(".text")
    asmcode.append(".global main")
    asmcode.append(".type main, @function")

    for asmcode in code3ac:
        lineno = lineno + 1
        asmcode = asmcode.replace(' ', '')
        stmt = []
        for arg in asmcode.split("$"):
            if arg != '':
                stmt.append(arg)
        instr = {"op": stmt[1].strip(), "arg": stmt[2:-1]}
        currentScopeId = int(stmt[-1])
        asmcode.append("// " + asmcode.split('$')[0])
        gencode(instr)

    asmfile = open('asmfile.s', 'w')
    for asmcode in asmcode:
        asmcode = asmcode.replace('|', '').replace('#', '').replace('@', '')
        if asmcode[-1] == ':': asmfile.write(asmcode + "\n") #label
        else:
            asmfile.write("\t" + asmcode + "\n")