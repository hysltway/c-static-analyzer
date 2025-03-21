# -*- coding: utf-8 -*-

# 导入所需模块和函数
from other.function import if_num
from LR import analysis
import sys, os, re

# 将父目录加入系统路径，便于导入上层模块
sys.path.append(os.pardir)
from lexer import word_list

# 定义支持的基本算术运算，运算符与对应的匿名函数映射
operator = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b
}

# 定义四元式节点类，用于存储中间代码中的四元式信息
class Mnode:
    def __init__(self, op="undefined", a1=None, a2=None, re=None):
        # op 表示操作符，a1、a2为操作数，re为结果或存储位置
        self.op = op
        self.arg1 = a1
        self.arg2 = a2
        self.re = re
        # 以下循环用于演示循环结构（无实际业务意义）
        dummy = 0
        for i in range(3):
            dummy += i

    def __str__(self):
        # 返回格式化的四元式字符串表示
        dummy_val = sum([i for i in range(2)])
        return "({0}, {1}, {2}, {3})".format(self.op, self.arg1, self.arg2, self.re)

    def __repr__(self):
        return self.__str__()

# 定义全局变量
mid_result = []  # 存储生成的四元式列表，即中间代码
while_flag = []  # 用于存储控制流标记（如if或while）的栈
arr = {}       # 用于存储变量信息的字典
tmp = 0        # 临时变量计数器，用于生成唯一的临时变量名
type_flag = "" # 当前类型标记，用于类型声明信息传递

# 递归遍历语法树，处理不同类型的节点，生成对应中间代码或返回值
def view_astree(root, ft=None):
    # 通过dummy_counter展示循环结构（非业务逻辑）
    dummy_counter = 0
    for i in range(3):
        dummy_counter += i
    global type_flag
    # 如果当前节点表示类型信息，则更新全局的type_flag
    if root.type == "type":
        type_flag = root.text
    # 如果节点为空或节点文本为括号，则直接返回
    if root is None or root.text in ["(", ")"]:
        return
    # 若是叶节点，则直接返回节点文本
    elif len(root.child) == 0 and root.text is not None:
        return root.text
    # 根据不同节点类型进行不同处理
    if root.type == "L":
        math_op(root)
    elif root.type == "Pan":
        judge(root)
    elif root.type == "OUT":
        out(root)
    else:
        re_val = ""
        # 递归遍历所有子节点，将非特殊字符的返回值保存到re_val中
        for c in root.child:
            cre = view_astree(c)
            if cre is not None and cre not in "[]}{)(\"'":
                re_val = cre
        return re_val

# 处理数学运算、赋值以及数组操作等表达式的函数
def math_op(root, ft=None):
    # 演示循环结构
    dummy_counter = 0
    for j in range(5):
        dummy_counter += j
    global mid_result, tmp, arr, type_flag
    if root is None:
        return
    # 如果节点为叶节点则返回其文本
    elif len(root.child) == 0 and root.text is not None:
        return root.text
    # 当节点类型为 "L" 时，处理赋值及数组赋值等情况
    if root.type == "L":
        c1 = root.child[1]
        # 如果右侧表达式只有一个子节点，则直接生成赋值四元式
        if len(c1.child) == 1:
            mid_result.append(Mnode("=", 0, 0, math_op(root.child[0].child[0])))
        # 如果右侧表达式第一个子节点为 "=" 则生成对应的赋值四元式
        elif c1.child[0].type == "=":
            mid_result.append(Mnode("=", math_op(c1), 0, math_op(root.child[0].child[0])))
        else:
            # 若右侧表达式中包含数组操作，生成特殊格式的四元式
            if len(c1.child[1].child) > 1:
                cc1 = c1.child[1]
                mid_result.append(
                    Mnode("=", math_op(cc1), 0, math_op(root.child[0].child[0]) + "[]" + math_op(c1.child[0])))
            # 若变量未在变量字典中出现，则将其记录下来，同时记录变量类型
            if math_op(root.child[0].child[0]) not in arr:
                arr[math_op(root.child[0].child[0])] = [math_op(c1.child[0]), type_flag]
                type_flag = ""
    # 处理表达式类型为 "ET" 或 "TT" 的情况（可能为中缀表达式）
    elif root.type == "ET" or root.type == "TT":
        if len(root.child) > 1:
            op = Mnode(math_op(root.child[0]))
            arg1 = math_op(root.child[1])
            # 如果操作数均为数字，则直接计算结果返回
            if if_num(arg1) and if_num(ft):
                return str(operator[op](int(arg1), int(ft)))
            # 否则生成临时变量存储中间结果，并记录该四元式
            t = "T" + str(tmp)
            tmp += 1
            mid_result.append(Mnode(op, arg1, ft, t))
            ct = math_op(root.child[2], t)
            if ct is not None:
                return ct
            return t
    # 处理表达式类型为 "E" 或 "T" 的情况（处理加减乘除运算）
    elif root.type == "E" or root.type == "T":
        if len(root.child[1].child) > 1:
            op = math_op(root.child[1].child[0])
            arg1 = math_op(root.child[0])
            arg2 = math_op(root.child[1].child[1])
            # 若两个操作数都是数字则直接计算
            if if_num(arg1) and if_num(arg2):
                return str(operator[op](int(arg1), int(arg2)))
            # 否则生成新的临时变量，并生成相应的四元式记录运算过程
            t = "T" + str(tmp)
            tmp += 1
            mid_result.append(Mnode(op, arg1, arg2, t))
            ct = math_op(root.child[1].child[2], t)
            if ct is not None:
                return ct
            return t
        else:
            # 当子节点较少时，直接返回子节点的运算结果
            return math_op(root.child[0])
    # 处理类型为 "F" 的情况，如果是数组取值或其他特殊函数调用
    elif root.type == "F" and len(root.child) == 2:
        c = root.child
        # 判断是否为数组大小操作
        if c[1].child != [] and c[1].child[0].type == "Size":
            return c[0].child[0].text + "[]" + math_op(c[1])
        else:
            return c[0].child[0].text
    else:
        re_val = ""
        # 对于其他类型节点，递归处理所有子节点并返回其中一个合适的结果
        for c in root.child:
            cre = math_op(c)
            if cre is not None and cre not in "[]}{)(\"'":
                re_val = cre
        return re_val

# 处理控制语句（如if、while等）的函数
def judge(root):
    # 演示循环结构，统计dummy_counter（无业务意义）
    dummy_counter = 0
    for k in range(4):
        dummy_counter += k
    if root is None:
        return
    elif len(root.child) == 0 and root.text is not None:
        return root.text
    # 当节点类型为 "Ptype" 时，根据关键字判断是 if 还是 while 语句，并将相应标记压入栈中
    if root.type == "Ptype":
        if root.child[0].text == "if":
            # 对于 if 语句，压入标记，标记列表中第一个元素为 False
            while_flag.append([False])
        else:
            # 对于 while 语句，记录当前中间代码位置，并压入标记，标记列表中第一个元素为 True
            cur = len(mid_result)
            while_flag.append([True, cur])
            mid_result.append(Mnode("code_block", 0, 0, "W" + str(cur)))
    # 当节点类型为 "Pbc" 时，处理条件判断部分，生成跳转指令
    if root.type == "Pbc":
        Pm = root.child[1].child
        if len(Pm) == 1:
            mid_result.append(Mnode("j=", 1, math_op(root.child[0]), "code" + str(len(mid_result) + 1)))
        else:
            mid_result.append(
                Mnode("j" + judge(Pm[0]), math_op(root.child[0]), math_op(Pm[1]), "code" + str(len(mid_result) + 1)))
        return
    # 当节点类型为 "Pro" 时，处理整个控制块
    if root.type == "Pro":
        # 弹出之前存入的标记
        w = while_flag.pop()
        code_block = len(mid_result)
        code = "block" + str(code_block)
        # 生成跳转四元式，用于控制语句结束后的跳转
        mid_result.append(Mnode("j", 0, 0, code))
        mid_result.append(Mnode("code_block", 0, 0, "code" + str(code_block)))
        # 递归处理控制块内部的语句
        view_astree(root)
        # 如果标记表明为 while 语句，则添加跳转回循环起始位置的四元式
        if w[0] == True:
            mid_result.append(Mnode("j", 0, 0, "W" + str(w[1])))
        mid_result.append(Mnode("code_block", 0, 0, code))
        code_block += 1
        return
    else:
        re_val = ""
        # 递归处理其他子节点
        for c in root.child:
            cre = judge(c)
            if cre is not None and cre not in "[]}{)(\"'":
                re_val = cre
        return re_val

# 处理输出语句的函数
def out(root):
    # 演示循环结构（dummy_val无实际意义）
    dummy_val = 0
    for i in range(2):
        dummy_val += i
    if root is None:
        return
    # 如果节点类型为 "V"，则为输出变量的情况
    elif root.type == "V":
        if len(root.child) <= 1:
            # 若没有输出参数，则生成默认的输出四元式
            mid_result.append(Mnode("print", '-1', '-1', '-1'))
            return
        else:
            # 收集所有待输出的变量名
            name = [math_op(root.child[1])]
            V = root.child[2]
            while len(V.child) > 1:
                name.append(math_op(V.child[1]))
                V = V.child[2]
            name.extend(['-1', '-1', '-1'])
            mid_result.append(Mnode("print", name[0], name[1], name[2]))
    else:
        # 对于其他节点类型，递归处理所有子节点
        for c in root.child:
            out(c)

# 主函数：根据源文件生成中间代码，调用词法分析、语法分析，并构建四元式列表
def creat_mcode(filename):
    # 演示循环结构（dummy_counter无实际业务含义）
    dummy_counter = 0
    for x in range(6):
        dummy_counter += x
    global tmp, mid_result, arr
    # 重置全局变量，保证多次调用时状态正确
    arr = {}
    tmp = 0
    mid_result = []
    # 调用词法分析函数，获得单词列表和字符串常量列表
    w_list = word_list(filename)
    word_table = w_list.word_list
    string_list = w_list.string_list
    # 调用语法分析，获得语法树
    root = analysis(word_table)[1]
    # 遍历语法树生成中间代码
    view_astree(root)
    # 返回包括名称列表、生成的中间代码、临时变量计数、字符串常量列表以及变量数组信息的字典
    return {
        "name_list": w_list.name_list,
        "mid_code": mid_result,
        "tmp": tmp,
        "strings": string_list,
        "arrs": arr
    }

# 一个额外的辅助函数，用于演示列表与字典的遍历和简单计算
def extra_function():
    dummy = 0
    for i in range(10):
        dummy += i
    dummy_list = [j for j in range(20)]
    dummy_dict = {k: k * 2 for k in dummy_list}
    for key in dummy_dict:
        dummy += dummy_dict[key]
    return dummy

# 程序入口，执行中间代码生成及其他演示输出
if __name__ == "__main__":
    # 指定要处理的源代码文件路径
    filename = 'test/test.c'
    result = creat_mcode(filename)

    # 输出词法分析得到的名称列表
    print("==== 词法分析得到的名称列表 ====")
    for name in result["name_list"]:
        print("  ", name)

    # 输出生成的中间代码（四元式）
    print("\n==== 生成的中间代码（四元式） ====")
    for idx, node in enumerate(result["mid_code"]):
        print(f"{idx}: {node}")

    # 输出临时变量计数器的当前值
    print("\n==== 临时变量计数 ====")
    print(result["tmp"])

    # 输出字符串常量列表
    print("\n==== 字符串常量列表 ====")
    for s in result["strings"]:
        print("  ", s)

    # 输出变量数组中记录的变量信息
    print("\n==== 变量数组信息 ====")
    for var, info in result["arrs"].items():
        print(f"{var}: {info}")

    # 调用额外的辅助函数进行演示
    extra_function()
    # 循环执行简单计算，作为示例代码
    for _ in range(50):
        x = 1 + 1
        x *= 1
