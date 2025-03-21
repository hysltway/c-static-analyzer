# -*- coding: utf-8 -*-

import re
import sys, os


sys.path.append(os.pardir)
from other.function import if_num, if_name, have_name, printf, get_word

# 定义运算符集合，包含常用的算术、关系及逻辑运算符
y_list = {"+", "-", "*", "/", "<", "<=", ">", ">=", "=", "==", "!=", "^", ",", "&", "&&", "|", "||", "%", "~", "<<", ">>", "!"}

# 定义分隔符集合，包括各种标点、括号等
f_list = {";", "(", ")", "[", "]", "{", "}", ".", ":", "\"", "#", "\'", "\\", "?"}

# 定义关键字集合，包含 C 语言中常用的关键字
k_list = {
    "auto", "break", "case", "const", "continue", "default", "do", "else", "enum", "extern",
    "for", "goto", "if", "register", "return", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "volatile", "while", "printf"
}

# 定义比较运算符列表
Cmp = ["<", ">", "==", "!=", ">=", "<="]

# 定义数据类型集合
Type = {"int", "float", "char", "double", "void", "long", "unsigned", "string"}

# 定义括号对应关系，用于判断括号匹配
kuo_cp = {'{': '}', '[': ']', '(': ')'}


# 定义一个函数，用于以美观的表格形式打印数据
def print_pretty_table(data, title):
    if not data:
        print(f"{title} 为空！")
        return
    # 提取所有列标题
    headers = list(data[0].keys())
    # 计算每列最大宽度
    col_widths = {header: len(header) for header in headers}
    for item in data:
        for header in headers:
            col_widths[header] = max(col_widths[header], len(str(item.get(header, ""))))
    # 构造分隔线和表头
    divider = "+" + "+".join(["-" * (col_widths[h] + 2) for h in headers]) + "+"
    header_line = "|" + "|".join(f" {h.ljust(col_widths[h])} " for h in headers) + "|"
    print(f"\n{title}")
    print(divider)
    print(header_line)
    print(divider)
    # 输出每一行数据
    for item in data:
        row = "|" + "|".join(f" {str(item.get(h, '')).ljust(col_widths[h])} " for h in headers) + "|"
        print(row)
    print(divider)


# 定义词法分析类，用于读取源文件并生成各类单词和符号表
class word_list():
    def __init__(self, filename='test.c'):
        # 保存当前数据类型标记
        self.type_flag = ""
        # 存储所有单词记录
        self.word_list = []
        # 存储所有分隔符记录
        self.separator_list = []
        # 存储所有运算符记录
        self.operator_list = []
        # 存储变量记录（标识符）
        self.name_list = []
        # 存储关键字记录
        self.key_word_table = []
        # 存储字符串常量列表
        self.string_list = []
        # 存储所有检测到的错误信息
        self.errors = []
        # 标记源代码是否正确（如果有错误则置为 False）
        self.flag = True

        # 调用 get_word 函数将源代码切分成单词，再创建各个记录表
        self.creat_table(get_word(filename))

    # 根据 get_word 返回的单词列表创建词法分析表
    def creat_table(self, in_words):
        name_id = 0  # 用于变量的唯一编号
        kuo_list = []  # 用于存储未匹配的左括号信息
        char_flag = False  # 标记是否处于字符常量中
        str_flag = False   # 标记是否处于字符串常量中
        strings = ""       # 存储字符串常量内容
        chars = ""         # 存储字符常量内容
        for word in in_words:
            w = word['word']
            line = word['line']
            # 处理字符串常量，遇到双引号切换状态
            if w == '"':
                if not str_flag:
                    str_flag = True
                else:
                    str_flag = False
                    self.word_list.append({'line': line, 'type': 'TEXT', 'word': strings})
                    self.string_list.append(strings)
                    strings = ""
                continue
            # 若处于字符串内部，直接累加内容
            if str_flag:
                strings += w
                continue
            # 处理字符常量，遇到单引号切换状态
            if w == "'":
                if not char_flag:
                    char_flag = True
                else:
                    char_flag = False
                    self.word_list.append({'line': line, 'type': 'CHAR', 'word': chars})
                    chars = ""
                continue
            if char_flag:
                chars += w
                continue
            # 判断是否为关键字
            if w in k_list:
                self.key_word_table.append({'line': line, 'type': 'keyword', 'word': w})
                self.word_list.append({'line': line, 'type': w, 'word': w})
            # 判断是否为比较运算符
            elif w in Cmp:
                self.word_list.append({'line': line, 'type': "Cmp", 'word': w})
            # 判断是否为数据类型关键字
            elif w in Type:
                self.type_flag = w
                self.key_word_table.append({'line': line, 'type': 'type', 'word': w})
                self.word_list.append({'line': line, 'type': 'type', 'word': w})
            # 判断是否为运算符
            elif w in y_list:
                self.operator_list.append({'line': line, 'type': 'operator', 'word': w})
                self.word_list.append({'line': line, 'type': w, 'word': w})
            # 判断是否为分隔符或括号
            elif w in f_list:
                if w in kuo_cp.values() or w in kuo_cp.keys():
                    if w in kuo_cp.keys():
                        kuo_list.append({'kuo': w, 'line': line})
                    elif kuo_list and w == kuo_cp[kuo_list[-1]['kuo']]:
                        kuo_list.pop()
                    else:
                        self.errors.append(f"在第{line}行的 '{w}' 无法匹配")
                        self.flag = False
                        continue
                self.separator_list.append({'line': line, 'type': 'separator', 'word': w})
                self.word_list.append({'line': line, 'type': w, 'word': w})
            # 处理数字和标识符
            else:
                if if_num(w):
                    self.word_list.append({'line': line, 'type': 'number', 'word': w})
                elif if_name(w):
                    if have_name(self.name_list, w):
                        self.word_list.append({'line': line, 'type': 'name', 'word': w, 'id': name_id})
                    else:
                        self.name_list.append({'line': line, 'id': name_id, 'word': 0.0, 'name': w, 'flag': self.type_flag})
                        self.word_list.append({'line': line, 'type': 'name', 'word': w, 'id': name_id})
                        name_id += 1
                else:
                    self.errors.append(f"在第{line}行的变量名 '{w}' 不可识别")
                    self.flag = False
                    continue
        # 检查是否有未匹配的左括号
        for item in kuo_list:
            self.errors.append(f"在第{item['line']}行的 '{item['kuo']}' 无法匹配")
            self.flag = False


if __name__ == '__main__':
    filename = input("请输入要编译的.c文件: ")
    if not filename:
        filename = 'test/test.c'
    w_list = word_list(filename)
    if w_list.errors:
        print("错误检测：")
        for error in w_list.errors:
            print(error)
    if w_list.flag:
        print_pretty_table(w_list.word_list, "词法分析结果")
        print_pretty_table(w_list.name_list, "变量表")
