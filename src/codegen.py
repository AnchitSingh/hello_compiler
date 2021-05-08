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


# def binary(float_):
#     return bin(struct.unpack('!i', struct.pack('!f', float_))[0])


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
    global code
    var = str(var)
    if "@" in var:
        if var.split('@')[0] == "tmp":
            var_entry = checkEntry(var)[0]
        else:
            var_entry = checkEntry(
                var.split('@')[0], int(var.split('@')[1]))[0]

        offset = var_entry["offset"]
        base = var_entry["base"]
        if base == "0":
            loadVar(reg, offset)
        elif base == "rbp":
            if "@" in str(offset):
                # offset is variable
                code.append("push %esi")
                loadVar("esi", offset)
                code.append("neg %esi")
                code.append("lea (%ebp, %esi, 1), %" + reg)
                code.append("pop %esi")
            else:
                # offset is int
                code.append("lea " + str(-offset) + "(%ebp), %" + reg)
        else:
            print("error in load Addr, base is not rbp or zero ")
            exit(-1)
    else:
        print("var is not a variable ")
        exit(-1)


def loadVar(reg, var):
    global code
    var = str(var)
    if "@" in var:
        if var.split('@')[0] == "tmp":
            var_entry = checkEntry(var)[0]
        elif var.split('@')[0] == "gbl":
            code.append("mov $" + var + ", %" + reg)
            return
        else:
            var_entry = checkEntry(var.split('@')[0], int(var.split('@')[1]))

        offset = var_entry["offset"]
        base = str(var_entry["base"])
        type_ = var_entry["type"]

        if "@" in str(offset):
            # offset is variable
            r =
            if base == "0":
                loadVar("esi", offset)
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    code.append("mov (%esi), %" + reg)
                elif type_ == "char":
                    code.append("movb (%esi), %" + reg[1] + "l")
                else:
                    print("struct error in load")
                    exit(-1)
            elif base == "rbp":
                loadVar("esi", offset)
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    code.append("neg %esi")
                    code.append("mov (%ebp , %esi, 1), %" + reg)
                elif type_ == "char":
                    code.append("neg %esi")
                    code.append("movb (%ebp , %esi, 1), %" + reg[1] + "l")
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
                    code.append("mov " + str(-offset) + "(%ebp), %" + reg)
                elif type_ == "char":
                    code.append("movb " + str(-offset) +
                                "(%ebp), %" + reg[1] + "l")
                else:
                    print("class error in load")
                    exit(-1)
            else:
                print("wrong base in load")
                exit(-1)
    else:
        if var[0] == "'" and var[2] == "'" and len(var) == 3:
            code.append("movb $" + str(ord(var[1]))+" , %" + reg[1] + "l")
        elif var.lstrip("-").isdigit():
            code.append("mov $" + var + " , %" + reg)
        else:
            print(var + " | Error in load var")
            exit(-1)


def storeVar(reg, var):
    global code
    var = str(var)
    if "@" in var:
        if var.split('@')[0] == "tmp":
            var_entry = checkEntry(var)[0]
        else:
            var_entry = checkEntry(var.split('@')[0], int(var.split('@')[1]))

        offset = var_entry["offset"]
        base = str(var_entry["base"])
        type_ = var_entry["type"]

        if "@" in str(offset):
            # offset is variable
            if base == "0":
                loadVar("edi", offset)
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    code.append("mov %" + reg + ", (%edi)")
                elif type_ == "char":
                    code.append("movb %" + reg[1] + "l" + ", (%edi)")
                else:
                    print(var, " struct error in store")
                    exit(-1)
            elif base == "rbp":
                loadVar("edi", offset)
                if type_[-1] == '*' or type_ in ["int", "float"]:
                    code.append("neg %edi")
                    code.append("mov %" + reg + ", (%ebp , %edi, 1)")
                elif type_ == "char":
                    code.append("neg %edi")
                    code.append("movb %" + reg[1] + "l" + ", (%ebp , %edi, 1)")
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
                    code.append("mov %" + reg + " , " +
                                str(-offset) + "(%ebp)")
                elif type_ == "char":
                    code.append(
                        "movb %" + reg[1] + "l" + " , " + str(-offset) + "(%ebp)")
                else:
                    print(type_, var, " struct error in store")
                    exit(-1)
            else:
                print("wrong base in store")
                exit(-1)
    else:
        print("Error in storing var")
        exit(-1)


# def loadFloatVar(var):
#     global code
#     var = str(var)
#     if "@" in var:
#         if var.split('@')[0] == "tmp":
#             info = checkEntry(var, "all")["var"]
#         else:
#             info = checkEntry(var.split('@')[0], int(var.split('@')[1]))

#         offset = info["offset"]
#         base = info["base"]
#         type_ = info["type"]
#         if "@" in str(offset):
#             # offset in variable
#             if str(base) == "0":
#                 loadVar("esi", offset)
#                 if type_ == "int":
#                     code.append("fild " + "(%esi)")
#                 elif type_ == "float":
#                     code.append("fld " + "(%esi)")
#                 else:
#                     print("error in load float")
#                     exit(-1)
#             elif str(base) == "rbp":
#                 loadVar("esi", offset)
#                 if type_ == "int":
#                     code.append("neg %esi")
#                     code.append("fild (%ebp , %esi, 1)")
#                 elif type_ == "float":
#                     code.append("neg %esi")
#                     code.append("fld (%ebp , %esi, 1)")
#                 else:
#                     print("error in load float")
#                     exit(-1)
#             else:
#                 print("wrong base in load")
#                 exit(-1)
#         else:
#             if type_ == "int":
#                 code.append("fild " + str(-offset) + "(%ebp)")
#             elif type_ == "float":
#                 code.append("fld " + str(-offset) + "(%ebp)")
#             else:
#                 print("error in load float")
#                 exit(-1)
#     else:
#         pass
#         print("var is not var")
#         exit(-1)


# def storeFloatVar(var):
#     global code
#     var = str(var)
#     if "@" in var:
#         if var.split('@')[0] == "tmp":
#             info = checkEntry(var, "all")["var"]
#         else:
#             info = checkEntry(var.split('@')[0], int(var.split('@')[1]))

#         offset = info["offset"]
#         base = info["base"]
#         if "@" in str(offset):
#             if str(base) == "0":
#                 loadVar("esi", offset)
#                 code.append("fstp " + "(%esi)")
#             elif str(base) == "rbp":
#                 loadVar("esi", offset)
#                 code.append("neg %esi")
#                 code.append("fstp (%ebp , %esi, 1)")
#             else:
#                 print("wrong base in load")
#                 exit(-1)
#         else:
#             code.append("fstp " + str(-offset) + "(%ebp)")
#     else:
#         pass
#         print("verror in store float")
#         exit(-1)


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
        code.append(mov + " (%" + srcOffset + "), %" + reg)

    if srcBase == "rbp":
        code.append("neg %" + srcOffset)
        code.append(mov + " (%ebp, %" + srcOffset + ",1) , %" + reg)
        code.append("neg %" + srcOffset)

    if destBase == "0":
        code.append(mov + " %" + reg + ", (%" + destOffset + ")")

    if destBase == "rbp":
        code.append("neg %" + destOffset)
        code.append(mov + " %" + reg + ", (%ebp, %" + destOffset + ",1)")
        code.append("neg %" + destOffset)


class CodeGenerator:
    def __init__(self):

    def op_print_int(self, instr):
        to_print_int = instr[0]
        loadVar("eax", to_print_int)
        code.append("push %ebp")
        code.append("mov %esp,%ebp")
        code.append("push %eax")
        code.append("push $print_fmt_int")
        code.append("call printf")
        code.append("add  $8, %esp")
        code.append("mov %ebp, %esp")
        code.append("pop %ebp")

    def op_print_char(self, instr):
        to_print_int = instr[0]
        loadVar("eax", to_print_int)
        code.append("push %ebp")
        code.append("mov %esp,%ebp")
        code.append("push %eax")
        code.append("push $print_fmt_char")
        code.append("call printf")
        code.append("add  $8, %esp")
        code.append("mov %ebp, %esp")
        code.append("pop %ebp")

    def op_print_float(self, instr):
        to_print_int = instr[0]
        loadVar("eax", to_print_int)
        code.append("push %ebp")
        code.append("mov %esp,%ebp")
        code.append("push %eax")
        code.append("push $print_fmt_hex")
        code.append("call printf")
        code.append("add  $8, %esp")
        code.append("mov %ebp, %esp")
        code.append("pop %ebp")

    # def op_print_float(self, instr):
    #     to_print_int = instr[0]
    #     loadFloatVar(to_print_int)
    #     code.append("push %ebp")
    #     code.append("mov %esp,%ebp")
    #     # code.append("sub $4, %esp")
    #     code.append("fstp -4(%esp)" )
    #     code.append("push $print_fmt_float")
    #     code.append("call printf")
    #     code.append("add  $4, %esp")
    #     code.append("mov %ebp, %esp")
    #     code.append("pop %ebp")

    def op_malloc(self, instr):
        to_malloc, size = instr
        loadVar("edi", size)

        code.append("push %ebp")
        code.append("mov %esp,%ebp")
        code.append("push %edi")
        code.append("call malloc")
        code.append("add $4, %esp")
        code.append("mov %ebp, %esp")
        code.append("pop %ebp")
        storeVar("eax", to_malloc)

    def op_free(self, instr):
        to_free = instr[0]
        loadVar("edi", to_free)

        code.append("push %ebp")
        code.append("mov %esp,%ebp")
        code.append("push %edi")
        code.append("call malloc")
        code.append("add $4, %esp")
        code.append("mov %ebp, %esp")
        code.append("pop %ebp")

    def op_scan_int(self, instr):
        to_scan_int = instr[0]
        loadAddr("eax", to_scan_int)
        code.append("push %ebp")
        code.append("mov %esp,%ebp")
        code.append("push %eax")
        code.append("push $scan_fmt_int")
        code.append("call scanf")
        code.append("add  $8, %esp")
        code.append("mov %ebp, %esp")
        code.append("pop %ebp")

    def op_scan_char(self, instr):
        to_scan_int = instr[0]
        loadAddr("eax", to_scan_int)
        code.append("push %ebp")
        code.append("mov %esp,%ebp")
        code.append("push %eax")
        code.append("push $scan_fmt_char")
        code.append("call scanf")
        code.append("add  $8, %esp")
        code.append("mov %ebp, %esp")
        code.append("pop %ebp")

    def op_add(self, instr):
        out, inp1, inp2 = instr
        loadVar("eax", inp1)
        loadVar("ebx", inp2)
        code.append("add %ebx, %eax")
        storeVar("eax", out)

    def op_float_add(self, instr):
        out, inp1, inp2 = instr
        loadFloatVar(inp1)
        loadAddr("eax", inp2)
        code.append("fadd (%eax)")
        storeFloatVar(out)

    def op_sub(self, instr):
        out, inp1, inp2 = instr
        loadVar("eax", inp1)
        loadVar("ebx", inp2)
        code.append("sub %ebx, %eax")
        storeVar("eax", out)

    def op_float_sub(self, instr):
        out, inp1, inp2 = instr
        loadFloatVar(inp1)
        loadAddr("eax", inp2)
        code.append("fsub (%eax)")
        storeFloatVar(out)

    def op_mult(self, instr):
        out, inp1, inp2 = instr
        loadVar("eax", inp1)
        loadVar("ebx", inp2)
        code.append("imul %ebx, %eax")
        storeVar("eax", out)

    def op_float_mult(self, instr):
        out, inp1, inp2 = instr
        loadFloatVar(inp1)
        loadAddr("eax", inp2)
        code.append("fmul (%eax)")
        storeFloatVar(out)

    def op_div(self, instr):
        # idiv %ebx — divide the contents of EDX:EAX by the contents of EBX. Place the quotient in EAX and the remainder in EDX.
        out, inp1, inp2 = instr
        loadVar("eax", inp1)
        loadVar("ebx", inp2)
        code.append("mov $0, %edx")
        code.append("idiv %ebx")
        storeVar("eax", out)

    def op_float_div(self, instr):
        out, inp1, inp2 = instr
        loadFloatVar(inp1)
        loadAddr("eax", inp2)
        code.append("fdiv (%eax)")
        storeFloatVar(out)

    def op_modulo(self, instr):
        # idiv %ebx — divide the contents of EDX:EAX by the contents of EBX. Place the quotient in EAX and the remainder in EDX.
        out, inp1, inp2 = instr
        loadVar("eax", inp1)
        loadVar("ebx", inp2)
        code.append("mov $0, %edx")
        code.append("idiv %ebx")
        storeVar("edx", out)

    def op_lshift(self, instr):
        out, inp1, inp2 = instr
        loadVar("eax", inp1)
        loadVar("cl", inp2)
        code.append("shl %cl, %eax")
        storeVar("eax", out)

    def op_rshift(self, instr):
        out, inp1, inp2 = instr
        loadVar("eax", inp1)
        loadVar("cl", inp2)
        code.append("shr %cl, %eax")
        storeVar("eax", out)

    def op_inc(self, instr):
        inp = instr[0]
        loadVar("eax", inp)
        code.append("inc  %eax")
        storeVar("eax", inp)

    def op_dec(self, instr):
        inp = instr[0]
        loadVar("eax", inp)
        code.append("dec  %eax")
        storeVar("eax", inp)

    def op_logical_dual(self, instr, lt):
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
        code.append(log_op(lt) + " %ebx, %eax")
        if lt == "&&" or lt == "||":
            code.append("cmp $0, %eax")
            code.append("mov $0, %eax")
            code.append("setne %al")

        storeVar("eax", out)

    def op_bitwise_not(self, instr):
        out, inp = instr
        loadVar("eax", inp)
        code.append("not %eax")
        storeVar("eax", out)

    def op_logical_not(self, instr):
        out, inp = instr
        loadVar("eax", inp)

        code.append("cmp $0, %eax")
        code.append("mov $0, %eax")
        code.append("sete %al")

        storeVar("eax", out)

    def op_comp(self, instr, comp):
        out, inp1, inp2 = instr
        loadVar("eax", inp1)
        loadVar("ebx", inp2)
        code.append("cmp %ebx, %eax")
        code.append("mov $0, %ecx")
        if comp == "<":
            code.append("setl %cl")
        elif comp == ">":
            code.append("setg %cl")
        elif comp == "<=":
            code.append("setle %cl")
        elif comp == ">=":
            code.append("setge %cl")
        elif comp == "==":
            code.append("sete %cl")
        elif comp == "!=":
            code.append("setne %cl")

        storeVar("ecx", out)

    def op_float_comp(self, instr, comp):
        out, inp1, inp2 = instr
        loadFloatVar(inp2)
        loadFloatVar(inp1)
        code.append("fcomip")
        code.append("fstp %st(0)")
        code.append("mov $0, %ecx")
        if comp == "float<":
            code.append("setb %cl")
        elif comp == "float>":
            code.append("seta %cl")
        elif comp == "float<=":
            code.append("setbe %cl")
        elif comp == "float>=":
            code.append("setae %cl")
        elif comp == "float==":
            code.append("sete %cl")
        elif comp == "float!=":
            code.append("setne %cl")

        storeVar("ecx", out)

    def op_float_assign(self, instr):
        out, inp = instr
        if "@" in inp:
            loadFloatVar(inp)
            storeFloatVar(out)
        else:
            # it is constant assignment like a = 1.4 ;
            dec = float(str(inp))
            bin_ = binary(dec)
            code.append("mov $" + str(bin_) + " ,%eax")
            storeVar("eax", out)

    def op_assign(self, instr):
        out, inp = instr
        if "@" in inp:
            if inp.split('@')[0] == "gbl":
                loadVar("eax", inp)
                storeVar("eax", out)
                return

            info = checkEntry(inp, "all")["var"] if inp.split(
                '@')[0] == "tmp" else checkEntry(inp.split('@')[0], int(inp.split('@')[1]))
            type_ = info["type"]
            if "|" in type_ or type_ in ["int", "char", "float"]:
                loadVar("eax", inp)
                storeVar("eax", out)
            else:
                offset = info["offset"]
                base = info["base"]
                size = info["size"]
                inp = out
                info = checkEntry(inp, "all")["var"] if inp.split(
                    '@')[0] == "tmp" else checkEntry(inp.split('@')[0], int(inp.split('@')[1]))
                offset_d = info["offset"]
                base_d = info["base"]
                size_d = info["size"]

                loadVar("eax", offset)
                loadVar("ebx", offset_d)

                def add_to_offset(base, base_d, size):
                    if base == "0":
                        code.append("add $" + str(size) + ", %eax")
                    else:
                        code.append("sub $" + str(size) + ", %eax")
                    if base_d == "0":
                        code.append("add $" + str(size) + ", %ebx")
                    else:
                        code.append("sub $" + str(size) + ", %ebx")
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
            info = checkEntry(out, "all")["var"] if out.split(
                '@')[0] == "tmp" else checkEntry(out.split('@')[0], int(out.split('@')[1]))
            type_ = info["type"]
            if type_ == "char":
                code.append("mov $" + str(ord(inp[1])) + ",%eax")
                storeVar("eax", out)
            else:
                code.append("mov $" + inp + ", %eax")
                storeVar("eax", out)

    def op_label(self, instr):
        label = instr[0]
        code.append(str(label) + ":")

    def op_ifnz(self, instr):
        var = instr[0]
        label = instr[1]
        loadVar("eax", var)
        code.append("cmp $0 , %eax ")
        code.append("jne " + label)

    def op_ifz(self, instr):
        var = instr[0]
        label = instr[1]
        loadVar("eax", var)
        code.append("cmp $0 , %eax ")
        code.append("je " + label)

    def op_goto(self, instr):
        label = instr[0]
        code.append("jmp " + label)

    def op_lea(self, instr):
        out, inp = instr
        loadAddr("eax", inp)
        storeVar("eax", out)

    def op_pushParam(self, instr):
        inp = instr[0]
        info = checkEntry(inp, "all")["var"] if inp.split(
            '@')[0] == "tmp" else checkEntry(inp.split('@')[0], int(inp.split('@')[1]))
        if "|" in info["type"] and info["type"][-1] == "a":
            # this is array
            loadAddr("eax", inp)
            code.append("push %eax")
        elif "|" in info["type"]:
            # this is pointer
            loadVar("eax", inp)
            code.append("push %eax")
        elif info["type"] in ["int", "char", "float"]:
            loadVar("eax", inp)
            code.append("push %eax")
        else:
            offset = info["offset"]
            base = info["base"]
            size = info["size"]

            base_d = "0"
            loadVar("eax", offset)
            code.append("sub $" + str(size) + ", %esp")
            code.append("mov %esp, %ebx")

            def add_to_offset(base, base_d, size):
                if base == "0":
                    code.append("add $" + str(size) + ", %eax")
                else:
                    code.append("sub $" + str(size) + ", %eax")
                if base_d == "0":
                    code.append("add $" + str(size) + ", %ebx")
                else:
                    code.append("sub $" + str(size) + ", %ebx")

            for i in range(0, size, 1):
                movVar("eax", base, "ebx", base_d, 1)
                add_to_offset(base, base_d, 1)

    def op_fcall(self, instr):
        out, label = instr
        code.append("call " + label)
        storeVar("eax", out)

    def op_removeParam(self, instr):
        pop_size = instr[0]
        if not pop_size.isdigit():
            print(" pop size should be int")
            exit(-1)

        code.append("add " + pop_size + " %esp")

    def op_beginFunc(self, instr):
        expand_size = instr[0]
        if not expand_size.isdigit():
            print(" expand size should be int")
            exit(-1)
        code.append("push %ebp")
        code.append("mov %esp, %ebp")
        code.append("sub $" + expand_size + ", %esp")
        code.append("push %ebx")
        code.append("push %ecx")
        code.append("push %edx")
        code.append("push %esi")
        code.append("push %edi")

    def op_return(self, instr):
        ret_val = instr[0]
        loadVar("eax", ret_val)
        code.append("pop %ebx")
        code.append("pop %ecx")
        code.append("pop %edx")
        code.append("pop %esi")
        code.append("pop %edi")
        code.append("mov %ebp, %esp")
        code.append("pop %ebp")
        code.append("ret ")


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
    # elif instr["op"] == "print_int":
    #     op_print_int(instr["arg"])
    # elif instr["op"] == "print_char":
    #     op_print_char(instr["arg"])
    # elif instr["op"] == "print_float":
    #     op_print_float(instr["arg"])
    # elif instr["op"] == "scan_int":
    #     op_scan_int(instr["arg"])
    # elif instr["op"] == "scan_char":
    #     op_scan_char(instr["arg"])
    # elif instr["op"] == "malloc":
    #     op_malloc(instr["arg"])
    # elif instr["op"] == "free":
    #     op_free(instr["arg"])
    # elif instr["op"] == "float=":
    #     op_float_assign(instr["arg"])
    # elif instr["op"] == "float+":
    #     op_float_add(instr["arg"])
    # elif instr["op"] == "float-":
    #     op_float_sub(instr["arg"])
    # elif instr["op"] == "float*":
    #     op_float_mult(instr["arg"])
    # elif instr["op"] == "float/":
    #     op_float_div(instr["arg"])
    # elif instr["op"] in ["float<", "float>", "float==", "float<=", "float>=", "float!="]:
    #     op_float_comp(instr["arg"], instr["op"])


if __name__ == "__main__":

    asmcode.append(".data")
    asmcode.append('print_fmt_int:\n\t\t .string "%d " ')
    asmcode.append('print_fmt_char:\n\t\t .string "%c" ')
    asmcode.append('print_fmt_float:\n\t\t .string "%f" ')
    asmcode.append('scan_fmt_int:\n\t\t .string "%d" ')
    asmcode.append('scan_fmt_char:\n\t\t .string "%c" ')
    for j in scopeTables[0].table.items():
        if isinstance(j[1], dict) and "base" in j[1].keys() and "offset" in j[1].keys():
            asmcode.append(str(j[1]["offset"]) +
                           ':\n\t\t .zero ' + str(j[1]["size"]) + ' ')
    asmcode.append(".text")
    asmcode.append(".global main|")
    asmcode.append(".type main|, @function")

    for code in code3ac:
        lineno = lineno + 1
        code = code.replace(' ', '')
        stmt = []
        for arg in code.split("$"):
            if arg != '':
                stmt.append(arg)
        instr = {"op": stmt[1].strip(), "arg": stmt[2:-1]}
        currentScopeId = int(stmt[-1])
        asmcode.append("// " + code.split('$')[0])
        gencode(instr)

    asmfile = open('asmfile.s', 'w')
    for code in asmcode:
        code = code.replace('|', '').replace('#', '').replace('@', '')
        if code[-1] == ':':  # label
            asmfile.write(code + "\n")
        else:
            asmfile.write("\t" + code + "\n")
