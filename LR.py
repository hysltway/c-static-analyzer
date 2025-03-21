# -*- coding: utf-8 -*-

import re
from get_predict_table import creat_predict_table

# 运算符集合（算术、关系及逻辑）
y_list = {"+", "-", "*", "/", "<", "<=", ">", ">=", "=", "==", "!=", "^", ",", "&", "&&", "|", "||", "%", "~", "<<", ">>", "!"}

# 分隔符集合（各种标点和括号）
f_list = {";", "(", ")", "[", "]", "{", "}", ".", ":", "\"", "#", "\'", "\\", "?"}

# 关键字集合（C 语言常用关键字）
k_list = {
    "auto", "break", "case", "const", "continue", "default", "do", "else", "enum", "extern",
    "for", "goto", "if", "register", "return", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "volatile", "while", "printf"
}

# 比较运算符列表
Cmp = ["<", ">", "==", "!=", ">=", "<="]

# 数据类型集合
Type = {"int", "float", "char", "double", "void", "long", "unsigned", "string"}

# 括号对应关系，用于括号匹配检测
kuo_cp = {'{': '}', '[': ']', '(': ')'}

# ----------------- 词法分析器（独立实现） -----------------
def lex(filename):
    """
    独立的词法分析函数，返回 token 列表和检测到的错误列表。
    每个 token 为一个字典，包含 'line'、'type'、'word' 三个字段。
    """
    tokens = []
    errors = []
    with open(filename, encoding="utf-8") as f:
        lines = f.readlines()

    # 定义分词的正则表达式，注意多字符运算符的优先匹配
    token_specification = [
         ('STRING', r'"([^"\\]*(\\.[^"\\]*)*)"'),
         ('CHAR', r"'([^'\\]*(\\.[^'\\]*)*)'"),
         ('NUMBER', r'\d+(\.\d*)?'),
         ('ID', r'[A-Za-z_]\w*'),
         ('OP', r'==|!=|<=|>=|&&\|\||[+\-*/<>=%!^]'),
         ('SEP', r'[,;\(\)\[\]\{\}\.:\"#\'\\\?]'),
         ('SKIP', r'[ \t]+'),
         ('NEWLINE', r'\n'),
         ('MISMATCH', r'.'),
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    get_token = re.compile(tok_regex).match

    line_num = 1
    for line in lines:
        pos = 0
        while pos < len(line):
            m = get_token(line, pos)
            if not m:
                break
            typ = m.lastgroup
            value = m.group(typ)
            if typ == 'NEWLINE':
                pos = m.end()
                continue
            elif typ == 'SKIP':
                pos = m.end()
                continue
            elif typ == 'MISMATCH':
                errors.append(f"在第{line_num}行发现无法识别的字符: {value}")
                pos = m.end()
                continue
            else:
                # 对标识符进行关键字和数据类型判断
                if typ == 'ID':
                    if value in k_list or value in Type:
                        token_type = value
                    else:
                        token_type = 'ID'
                elif typ == 'OP':
                    token_type = value  # 运算符 token 类型取其符号
                elif typ == 'SEP':
                    token_type = value  # 分隔符 token 类型取其符号
                elif typ == 'STRING':
                    token_type = 'TEXT'
                elif typ == 'CHAR':
                    token_type = 'CHAR'
                else:
                    token_type = typ
                tokens.append({'line': line_num, 'type': token_type, 'word': value})
                pos = m.end()
        line_num += 1

    # 括号匹配检查
    bracket_stack = []
    for token in tokens:
        if token['word'] in kuo_cp.keys():
            bracket_stack.append(token)
        elif token['word'] in kuo_cp.values():
            if bracket_stack and token['word'] == kuo_cp[bracket_stack[-1]['word']]:
                bracket_stack.pop()
            else:
                errors.append(f"在第{token['line']}行的 '{token['word']}' 无法匹配")
    for token in bracket_stack:
        errors.append(f"在第{token['line']}行的 '{token['word']}' 无法匹配")
    return tokens, errors

# ----------------- 语法分析部分 -----------------
# 此处保留预测分析表生成和相关定义，但语法分析功能将被禁用
predict_table = creat_predict_table()

# 以下部分保留原有代码，仅用于类和工具函数的定义
if "Program" not in predict_table:
    predict_table["Program"] = {}
predict_table["Program"]["int"] = "ExtDefList"

if "ExtDefList" not in predict_table:
    predict_table["ExtDefList"] = {}
predict_table["ExtDefList"]["int"] = "ExtDef ExtDefList"
predict_table["ExtDefList"]["#"] = "null"  # ε 产生式

if "ExtDef" not in predict_table:
    predict_table["ExtDef"] = {}
predict_table["ExtDef"]["int"] = "Specifier Declarator CompoundStmt"

if "Specifier" not in predict_table:
    predict_table["Specifier"] = {}
predict_table["Specifier"]["int"] = "int"  # 终结符

if "Declarator" not in predict_table:
    predict_table["Declarator"] = {}
predict_table["Declarator"]["ID"] = "ID ParamList"

if "ParamList" not in predict_table:
    predict_table["ParamList"] = {}
predict_table["ParamList"]["("] = "( )"  # 简单假设无参数

if "CompoundStmt" not in predict_table:
    predict_table["CompoundStmt"] = {}
predict_table["CompoundStmt"]["{"] = "{ StmtList }"

if "StmtList" not in predict_table:
    predict_table["StmtList"] = {}
predict_table["StmtList"]["int"] = "Stmt StmtList"
predict_table["StmtList"]["ID"] = "Stmt StmtList"
predict_table["StmtList"]["while"] = "Stmt StmtList"
predict_table["StmtList"]["printf"] = "Stmt StmtList"
predict_table["StmtList"]["}"] = "null"  # ε 产生式

if "Stmt" not in predict_table:
    predict_table["Stmt"] = {}
predict_table["Stmt"]["int"] = "Declaration"
predict_table["Stmt"]["ID"] = "Assignment"
predict_table["Stmt"]["while"] = "WhileStmt"
predict_table["Stmt"]["printf"] = "PrintStmt"

if "Declaration" not in predict_table:
    predict_table["Declaration"] = {}
predict_table["Declaration"]["int"] = "int ID SEMI"

if "Assignment" not in predict_table:
    predict_table["Assignment"] = {}
predict_table["Assignment"]["ID"] = "ID = Expr SEMI"

if "WhileStmt" not in predict_table:
    predict_table["WhileStmt"] = {}
predict_table["WhileStmt"]["while"] = "while ( Expr ) CompoundStmt"

if "PrintStmt" not in predict_table:
    predict_table["PrintStmt"] = {}
predict_table["PrintStmt"]["printf"] = "printf ( TEXT ) SEMI"

if "Expr" not in predict_table:
    predict_table["Expr"] = {}
predict_table["Expr"]["ID"] = "ID"
predict_table["Expr"]["NUMBER"] = "NUMBER"
predict_table["Expr"]["("] = "( Expr )"

for terminal in ["SEMI", "(", ")", "TEXT", "NUMBER", "ID"]:
    if terminal not in predict_table:
        predict_table[terminal] = {}
    predict_table[terminal][terminal] = terminal

# 定义非终结符的语法树节点类
class Node:
    def __init__(self, Type, text=None):
        self.type = Type
        self.text = text
        self.child = []
    def __str__(self):
        return f"<{self.type}, {self.text}>"
    def __repr__(self):
        return self.__str__()

def stack_text(stack):
    return " -> ".join([s.type for s in stack])

def compute_tree_depth(node):
    if not node.child:
        return 1
    depth = 0
    for child in node.child:
        d = compute_tree_depth(child)
        if d > depth:
            depth = d
    return depth + 1

def check_tree_integrity(node):
    total = 1
    for child in node.child:
        total += check_tree_integrity(child)
    return total

# 修改后的语法分析函数：仅输出提示，不进行语法分析
def analysis(token_list, show=False):
    print("语法分析功能已被禁用。")
    dummy_root = Node("Program")
    return [True, dummy_root, []]

def print_syntax_tree(node, prefix="", is_last=True):
    connector = "└── " if is_last else "├── "
    print(prefix + connector + f"{node.type}" + (f": {node.text}" if node.text is not None else ""))
    new_prefix = prefix + ("    " if is_last else "│   ")
    child_count = len(node.child)
    for i, child in enumerate(node.child):
        print_syntax_tree(child, new_prefix, i == child_count - 1)

# ----------------- 主程序 -----------------
if __name__ == "__main__":
    filename = input("请输入要编译的.c文件: ")
    if not filename:
        filename = 'test/test.c'
    # 独立的词法分析
    token_list, lex_errors = lex(filename)
    if lex_errors:
        print("词法分析检测到以下错误：")
        for err in lex_errors:
            print(err)
        exit(1)
    else:
        print("词法分析结果：")
        for token in token_list:
            print(token)

