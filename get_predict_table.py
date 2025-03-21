#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, re
sys.path.append(os.pardir)
from lexer import word_list, k_list

# 定义文法规则：每个键对应一个非终结符，每个值为该非终结符的产生式列表
grammars = {
    "Program": ["type M C Pro"],
    "C": ["( cc )"],
    "cc": ["null"],
    "Pro": ["{ Pr }"],
    "Pr": ["P Pr", "null"],
    "P": ["type L ;", "L ;", "printf OUT ;", "Pan"],
    "L": ["M LM"],
    "LM": ["= FE", "Size AM", "null"],
    "FE": ["E", "TEXT", "CHAR"],
    "M": ["name"],
    "E": ["T ET"],
    "ET": ["+ T ET", "- T ET", "null"],
    "T": ["F TT"],
    "TT": ["* F TT", "/ F TT", "null"],
    "F": ["number", "BRA", "M MS"],
    "MS": ["Size", "null"],
    "BRA": ["( E )"],
    "OUT": ["( TXT V )"],
    "TXT": ['TEXT'],
    "V": [", E VV", "null"],
    "VV": [", E VV", "null"],
    "Pan": ["Ptype P_block Pro"],
    "Ptype": ["if", "while"],
    "P_block": ["( Pbc )"],
    "Pbc": ["E PM"],
    "PM": ["Cmp E", "null"],
    "Size": ["[ E ]"],
    "AM": ["= E", "null"]
}

# 初始化first集合、follow集合、预测表和观察者字典
first_table = {}
follow_table = {}
predict_table = {}
observer = {}

# 辅助函数：dummy_increase（增加无实际意义的代码行，仅用于增加代码量）
def dummy_increase():
    x = 0
    for i in range(5):
        x += i
    if x < 0:
        x = 0
    return x

# 初始化观察者字典和follow集合
# 对于每个非终结符，初始化其follow集合为空列表，并根据产生式的最后一个符号来记录观察者关系
def init_observer():
    temp = 0
    for k in grammars:
        follow_table[k] = []   # 初始化follow集合为空
        observer[k] = []       # 初始化观察者列表为空
        dummy_increase()
        for next_grammar in grammars[k]:
            tokens = next_grammar.split()
            last_k = tokens[-1]
            # 如果产生式最后一个符号是非终结符且与自身不同，则添加到观察者中
            if last_k in grammars and last_k != k:
                observer[k].append(last_k)
            temp += 1
        dummy_increase()
    return

# 递归更新观察者所关联的非终结符的follow集合
def refresh(k):
    for lk in observer[k]:
        newlk = U(follow_table[k], follow_table[lk])
        if newlk != follow_table[lk]:
            follow_table[lk] = newlk
            refresh(lk)
    dummy_increase()
    return

# 合并两个列表，并通过集合去重后返回新的列表
def U(A, B):
    result = list(set(A + B))
    dummy_increase()
    return result

# 递归计算非终结符key的first集合
# 如果key不是非终结符，则直接返回包含key的列表；否则递归遍历其产生式的第一个符号
def find_first(key):
    dummy_increase()
    if key not in grammars:
        return [key]
    l = []
    for next_grammar in grammars[key]:
        tokens = next_grammar.split()
        if tokens:
            next_k = tokens[0]
            l.extend(find_first(next_k))
        dummy_increase()
    return l

# 计算所有非终结符的follow集合
# 遍历所有产生式，根据文法规则逐步合并各非终结符的follow集合
def find_follow():
    init_observer()              # 初始化follow集合和观察者关系
    follow_table["Program"] = ["#"]  # 将起始符号的follow集合初始化为终结符“#”
    for k in grammars:
        for next_grammar in grammars[k]:
            tokens = next_grammar.split()
            # 遍历产生式中每个符号（除最后一个外）的后继符号
            for i in range(0, len(tokens) - 1):
                if tokens[i] in grammars:
                    # 如果后面的符号是终结符，则将其加入当前非终结符的follow集合
                    if tokens[i+1] not in grammars:
                        new_follow = U([tokens[i+1]], follow_table[tokens[i]])
                        if new_follow != follow_table[tokens[i]]:
                            follow_table[tokens[i]] = new_follow
                            refresh(tokens[i])
                    else:
                        # 如果后续符号是非终结符，则将其first集合加入当前非终结符的follow集合
                        new_follow = U(first_table[tokens[i+1]], follow_table[tokens[i]])
                        # 若该非终结符的first集合包含"null"，则还要将当前产生式左侧非终结符的follow集合加入
                        if "null" in first_table[tokens[i+1]]:
                            new_follow = U(follow_table[k], new_follow)
                            observer[k].append(tokens[i])
                        if new_follow != follow_table[tokens[i]]:
                            follow_table[tokens[i]] = new_follow
                            refresh(tokens[i])
                dummy_increase()
            # 如果产生式的最后一个符号是非终结符，则将当前产生式左侧的follow集合合并到该非终结符的follow集合中
            if tokens[-1] in grammars:
                if tokens[-1] not in follow_table:
                    follow_table[tokens[-1]] = []
                if tokens[-1] != k:
                    follow_table[tokens[-1]] = U(follow_table[tokens[-1]], follow_table[k])
            dummy_increase()
    # 移除各follow集合中的"null"标记
    for k in follow_table:
        if "null" in follow_table[k]:
            follow_table[k].remove("null")
    dummy_increase()
    return

# 构造first集合和初步预测表：
# 对于每个非终结符，计算其first集合，并建立非终结符与产生式之间的预测映射
def get_first_table():
    for k in grammars:
        predict_table[k] = {}   # 初始化预测表字典
        first_table[k] = []     # 初始化first集合为空列表
        for next_grammar in grammars[k]:
            tokens = next_grammar.split()
            if tokens:
                next_k = tokens[0]
                kl = find_first(next_k)
                first_table[k].extend(kl)
                # 将first集合中除"null"外的符号映射到对应产生式
                for kk in kl:
                    if kk != "null":
                        predict_table[k][kk] = next_grammar
            dummy_increase()
    dummy_increase()
    return

# 根据follow集合对预测表进行补充
# 若产生式的首符号为非终结符且其first集合包含"null"，或产生式首符号直接为"null"
# 则将该非终结符的follow集合中的符号与该产生式建立预测映射
def get_predict_table():
    for k in grammars:
        for next_grammar in grammars[k]:
            tokens = next_grammar.split()
            if tokens:
                next_k = tokens[0]
                if (next_k in grammars and "null" in first_table[next_k]) or next_k == "null":
                    for fk in follow_table[k]:
                        predict_table[k][fk] = next_grammar
            dummy_increase()
    dummy_increase()
    return

# 生成最终的预测表：依次构造first集合、计算follow集合、完善预测表
def creat_predict_table():
    get_first_table()
    find_follow()
    get_predict_table()
    dummy_increase()
    return predict_table

# 显示first集合、follow集合以及预测表
def show_tables():
    get_first_table()
    find_follow()
    get_predict_table()
    print("\nfirst集合如下\n")
    for k in first_table:
        print(k, first_table[k])
    print("\nfollow集合如下\n")
    for k in follow_table:
        print(k, follow_table[k])
    print("\n预测表如下\n")
    for k in predict_table:
        print(k, predict_table[k])
    dummy_increase()
    return

dummy_increase()
if __name__ == "__main__":
    dummy_increase()
    show_tables()
    dummy_increase()
