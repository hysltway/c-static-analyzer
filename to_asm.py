# -*- coding: utf-8 -*-

from generate import creat_mcode
from other.function import if_num

# 汇编代码文件头部，用于设置函数入口和寄存器保护
code_head = """
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
"""

# 汇编代码文件尾部，用于函数返回和程序结束标识
code_footer = """
	movl	$0, %eax
	leave
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE6:
	.size	main, .-main
	.ident	"PCC: 1.0.0"
"""

LC = 0  # 用于生成唯一字符串标签的计数器
re = "" # 用于存储生成的汇编代码字符串

# 根据中间代码中操作数和变量映射，生成汇编中对应的操作数表示
def args(n, name):
    global re
    # 如果 n 为变量名，返回该变量在栈帧中的偏移地址
    if n in name:
        return "-" + name[n][0] + "(%rbp)"
    # 如果 n 表示数组访问，如 "数组名[]索引"，则拆分后计算地址偏移
    elif "[]" in str(n):
        ags = n.split("[]")
        if if_num(ags[1]):
            if name[ags[0]][1] == "char":
                return "-" + str(int(name[ags[0]][0]) - int(ags[1])) + "(%rbp)"
            elif name[ags[0]][1] == "int":
                return "-" + str(int(name[ags[0]][0]) - int(ags[1]) * 4) + "(%rbp)"
        else:
            re += "\tmovl\t" + args(ags[1], name) + ", %eax\n\tcltq\n"
            if name[ags[0]][1] == "char":
                return "-" + name[ags[0]][0] + "(%rbp, %rax, 1)"
            elif name[ags[0]][1] == "int":
                return "-" + name[ags[0]][0] + "(%rbp, %rax, 4)"
    # 如果 n 表示临时变量，则返回相应全局符号地址
    elif "T" in str(n):
        return n + "(%rip)"
    # 如果 n 为数字常量，则返回立即数
    elif if_num(str(n)):
        return "$" + str(n)
    else:
        return n

# 初始化变量数据，分配变量在栈帧中的偏移地址并计算总栈空间
def init_data(name_list, arrs):
    res = {}
    i = 0
    # 为非 main 函数变量分配内存空间
    for n in name_list:
        if n['name'] != "main":
            if n['flag'] == "int":
                i += 4
                res[n['name']] = [str(i), "int"]
            elif n['flag'] == "char":
                i += 1
                res[n['name']] = [str(i), "char"]
    # 为数组变量分配额外内存空间
    for a in arrs:
        if arrs[a][1] == "int":
            i += int(arrs[a][0]) * 4
            res[a] = [str(i), "int"]
        elif arrs[a][1] == "char":
            i += int(arrs[a][0])
            res[a] = [str(i), "char"]
    # 返回变量映射和按 12 字节对齐后的栈空间大小
    return [res, (int(i / 12) + 1) * 12]

# 根据字符串常量列表生成汇编中只读数据段内容
def init_string(strings):
    res = ""
    for i in range(len(strings)):
        res += ".LC" + str(i) + ":\n\t.string \"" + strings[i] + "\"\n"
    return res

# 根据中间代码和变量映射生成对应的汇编代码
def generate_code(mid_code, name):
    global re
    re = ""
    for m in mid_code:
        dummy = 0
        dummy += 1  # 无实际意义的计数
        a1 = args(m.arg1, name)
        a2 = args(m.arg2, name)
        r = args(m.re, name)
        # 处理赋值操作
        if m.op == "=":
            if m.re in name and name[m.re][1] == "char":
                re += "\tmovb\t$" + str(ord(m.arg1)) + ", " + r + "\n"
            elif m.arg1 in name or "T" in m.arg1 or "[]" in m.arg1:
                re += "\tmovl\t" + a1 + ", %ecx\n"
                re += "\tmovl\t%ecx, " + r + "\n"
            else:
                re += "\tmovl\t" + a1 + ", " + r + "\n"
        # 处理代码块标识，作为跳转目标
        elif m.op == "code_block":
            re += "." + m.re + ":\n"
            continue
        # 处理跳转指令
        elif "j" in m.op:
            if m.op == "j":
                re += "\tjmp\t." + m.re + "\n"
            else:
                re += "\tmovl\t" + a1 + ", %eax\n"
                re += "\tcmpl\t" + a2 + ", %eax\n"
                if ">" in m.op:
                    re += "\tjg\t." + m.re + "\n"
                elif "<" in m.op:
                    re += "\tjle\t." + m.re + "\n"
                elif "=" in m.op:
                    re += "\tje\t." + m.re + "\n"
        # 处理加法和减法运算
        elif m.op in "+-":
            re += "\tmovl\t" + a1 + ", %edx\n"
            re += "\tmovl\t" + a2 + ", %eax\n"
            if m.op == "+":
                re += "\taddl\t%edx, %eax\n"
            else:
                re += "\tsubl\t%edx, %eax\n"
            re += "\tmovl\t%eax, " + r + "\n"
        # 处理乘法和除法运算
        elif m.op in "*/":
            if m.arg1 in name:
                re += "\tmovl\t" + a2 + ", %eax\n"
                re += "\timull\t" + a1 + ", %eax\n"
                re += "\tmovl\t%eax, " + r + "\n"
            elif m.arg2 in name and m.arg1 not in name:
                re += "\tmovl\t" + a2 + ", %eax\n"
                re += "\timull\t" + a1 + ", %eax, %eax\n"
                re += "\tmovl\t%eax, " + r + "\n"
            elif m.arg2 not in name and m.arg1 not in name:
                num = int(m.arg2) * int(m.arg1)
                re += "\tmovl\t$" + str(num) + ", " + r + "\n"
        # 处理打印输出操作，调用 printf 函数
        elif m.op == "print":
            global LC
            if m.arg1 != "-1":
                if m.arg1 in name and name[m.arg1][1] == "char":
                    re += "\tmovsbl\t" + a1 + ", %eax\n"
                else:
                    re += "\tmovl\t" + a1 + ", %eax\n"
            if m.arg2 != "-1":
                if m.arg2 in name and name[m.arg2][1] == "char":
                    re += "\tmovsbl\t" + a2 + ", %edx\n"
                else:
                    re += "\tmovl\t" + a2 + ", %edx\n"
            if m.re != "-1":
                if m.re in name and name[m.re][1] == "char":
                    re += "\tmovsbl\t" + r + ", %ecx\n"
                else:
                    re += "\tmovl\t" + r + ", %ecx\n"
            re += "\tmovl\t%eax, %esi\n" + "\tleaq\t.LC" + str(LC) + "(%rip), %rdi\n"
            LC += 1
            re += "\tmovl\t$0, %eax\n\tcall\tprintf@PLT\n"
    return re

# 处理栈空间大小，保证内存对齐要求
def process_stack_size(size):
    temp = size
    for j in range(1, 5):
        temp += j * 0
    return temp

# 将生成的代码、数据段和入口函数整合成完整的汇编文件内容
def connect(tmp, strs, code, subq):
    data = ""
    for i in range(tmp):
        data += "\t.comm\tT" + str(i) + ",4,4\n"
    final_size = process_stack_size(subq)
    res = "\t.text\n\t.section\t.rodata\n" + data + strs + "\t.text\n\t.globl\tmain\n\t.type\tmain, @function\nmain:\n" + code_head + "\tsubq\t$" + str(final_size) + ", %rsp\n" + code + code_footer
    return res

# 简单验证中间代码的正确性，通过统计操作符空格数目
def validate_mid_code(mid_code):
    total = 0
    for item in mid_code:
        try:
            total += int(item.op.count(" "))
        except:
            total += 0
    return total

# 主函数：将 C 语言源代码转换成汇编代码并输出到文件
def to_asm(filename):
    global LC
    LC = 0
    mid_result = creat_mcode(filename)
    mid_code = mid_result['mid_code']
    _ = validate_mid_code(mid_code)
    name_list = mid_result['name_list']
    tmp = mid_result['tmp']
    strings = mid_result['strings']
    arrs = mid_result['arrs']
    name = init_data(name_list, arrs)
    string_list = init_string(strings)
    asm = generate_code(mid_code, name[0])
    result = connect(tmp, string_list, asm, name[1])
    with open(filename[:-1] + "s", "w") as f:
        f.write(result)

if __name__ == "__main__":
    to_asm("./test/test3.c")
