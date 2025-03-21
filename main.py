import io
import sys
import chardet
from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.dialogs import Messagebox

import generate
import get_predict_table
import lexer
import LR
import to_asm
import semantic_analysis  # 新增：引入语义分析模块

from pyparsing import (
    Literal, Word, alphanums, Combine, quotedString, removeQuotes,
    delimitedList, Group, Suppress, Optional, restOfLine, Regex
)

# 定义语法规则相关的元素
colon = Literal(":")
identifier = Word("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_.",
                  "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.")
label = Combine(identifier + colon).setResultsName("label")
directive = Combine(Literal(".") + Word("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_", alphanums + "_")).setResultsName("directive")
instruction = Word("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_", alphanums + "_").setResultsName("instruction")
quoted_operand = quotedString.setParseAction(removeQuotes)
token = Regex(r"[\w@.$\-\(\)%]+")
operand = quoted_operand | token
operands = Group(delimitedList(operand)).setResultsName("operands")
comment = Suppress("#") + Optional(restOfLine).setResultsName("comment")
label_line = label + Optional(comment)
directive_line = Optional(label) + directive + Optional(operands) + Optional(comment)
instruction_line = Optional(label) + instruction + Optional(operands) + Optional(comment)
lineGrammar = label_line | directive_line | instruction_line

def parse_line(line):
    # 解析一行汇编代码，出错就把错误信息和该行内容一起返回
    try:
        result = lineGrammar.parseString(line, parseAll=True)
        return result.asDict()
    except Exception as e:
        return {"error": str(e), "line": line}

def detect_file_encoding(filename):
    # 读取文件二进制内容，然后检测文件的编码格式
    with open(filename, "rb") as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result["encoding"]
        print(f"检测到的文件编码: {encoding}")
        return encoding

def pretty_print(parsed):
    # 把解析结果整合成好看的字符串输出
    lines = []
    if "label" in parsed:
        lines.append(f"标签: {parsed['label']}")
    if "directive" in parsed:
        lines.append(f"伪指令: {parsed['directive']}")
    if "instruction" in parsed:
        lines.append(f"指令: {parsed['instruction']}")
    if "operands" in parsed:
        ops = []
        for op in parsed["operands"]:
            if op.startswith("PCC:"):
                op = op[len("PCC:"):].lstrip()
            ops.append(op)
        lines.append("操作数: " + ", ".join(ops))
    if "comment" in parsed:
        lines.append(f"注释: {parsed['comment']}")
    if "error" in parsed:
        lines.append(f"错误: {parsed['error']}")
    return "\n".join(lines)

def parse_assembly_file_to_string(filename):
    # 逐行读取汇编文件，并把每行的解析结果拼接成一个大字符串返回
    encoding = detect_file_encoding(filename)
    output_str = ""
    with open(filename, "r", encoding=encoding, errors="replace") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            parsed = parse_line(line)
            output_str += f"第 {lineno} 行:\n"
            output_str += pretty_print(parsed) + "\n"
            output_str += "-" * 40 + "\n"
    return output_str

def main():
    # 初始化主窗口，设置标题、主题和大小
    app = ttk.Window(
        title="C语言编译器与汇编解析器",
        themename="darkly",
        size=(1000, 1000)
    )

    # 顶部区域：显示标题
    top_frame = ttk.Frame(app, padding=10)
    top_frame.pack(side=TOP, fill=X)
    title_label = ttk.Label(
        top_frame,
        text="C语言编译器与汇编解析器",
        font=("Microsoft YaHei", 20, "bold"),
        bootstyle="inverse-primary"
    )
    title_label.pack(pady=10)

    # 创建Notebook，用来放置不同的功能页
    notebook = ttk.Notebook(app, bootstyle=PRIMARY)
    notebook.pack(fill=BOTH, expand=YES, padx=10, pady=5)

    # ---------------- C语言编译功能页 ----------------
    frame_c = ttk.Frame(notebook, padding=10)
    notebook.add(frame_c, text="C语言编译")

    # C源文件选择区
    frame_file_c = ttk.Frame(frame_c)
    frame_file_c.pack(fill=X, pady=5)
    label_c = ttk.Label(frame_file_c, text="C 源文件路径：", width=16)
    label_c.pack(side=LEFT)
    entry_file_c = ttk.Entry(frame_file_c, width=60)
    entry_file_c.pack(side=LEFT, padx=5)

    def browse_file_c():
        # 弹出对话框选择C文件
        file_path = filedialog.askopenfilename(
            title="选择 C 源文件",
            filetypes=[("C 文件", "*.c"), ("所有文件", "*.*")]
        )
        if file_path:
            entry_file_c.delete(0, END)
            entry_file_c.insert(0, file_path)

    btn_browse_c = ttk.Button(
        frame_file_c, text="浏览", command=browse_file_c, bootstyle=INFO
    )
    btn_browse_c.pack(side=LEFT, padx=5)

    # C源文件输出区
    output_text_c = ScrolledText(
        frame_c, wrap="word", height=25, font=("Consolas", 10)
    )
    output_text_c.pack(fill=BOTH, expand=YES, padx=5, pady=5)

    # 按钮区（执行各种编译相关操作）
    frame_buttons_c = ttk.Frame(frame_c)
    frame_buttons_c.pack(pady=5)

    def run_lexical_analysis():
        # 进行词法分析，展示词法和变量列表
        filename = entry_file_c.get()
        if not filename:
            Messagebox.show_warning("请先选择 C 源文件！", "警告")
            return
        try:
            wl = lexer.word_list(filename)
            output = "==== 词法分析结果 ====\n"
            for token in wl.word_list:
                output += f"{token}\n"
            output += "\n==== 变量表 ====\n"
            for name in wl.name_list:
                output += f"{name}\n"
            output_text_c.delete("1.0", END)
            output_text_c.insert(END, output)
        except Exception as e:
            Messagebox.show_error(str(e), "错误")

    def run_syntax_analysis():
        # 进行语义分析
        filename = entry_file_c.get()
        if not filename:
            Messagebox.show_warning("请先选择 C 源文件！", "警告")
            return
        try:
            analyzer = semantic_analysis.SemanticAnalyzer(filename)
            analyzer.parse()
            analyzer.analyze()
            # 捕获语义分析报告输出
            old_stdout = sys.stdout
            sys.stdout = mystdout = io.StringIO()
            analyzer.report()
            output = mystdout.getvalue()
            sys.stdout = old_stdout
            output_text_c.delete("1.0", END)
            output_text_c.insert(END, output)
        except Exception as e:
            Messagebox.show_error(str(e), "错误")

    def run_generate_intermediate_code():
        # 生成中间代码并展示相关信息
        filename = entry_file_c.get()
        if not filename:
            Messagebox.show_warning("请先选择 C 源文件！", "警告")
            return
        try:
            result = generate.creat_mcode(filename)
            output = "==== 中间代码生成结果 ====\n"
            output += "\n---- 词法分析得到的名称列表 ----\n"
            for name in result["name_list"]:
                output += f"{name}\n"
            output += "\n---- 生成的中间代码（四元式） ----\n"
            for idx, node in enumerate(result["mid_code"]):
                output += f"{idx}: {node}\n"
            output += f"\n---- 临时变量计数：{result['tmp']} ----\n"
            output += "\n---- 字符串常量列表 ----\n"
            for s in result["strings"]:
                output += f"{s}\n"
            output += "\n---- 变量数组信息 ----\n"
            for var, info in result["arrs"].items():
                output += f"{var}: {info}\n"
            output_text_c.delete("1.0", END)
            output_text_c.insert(END, output)
        except Exception as e:
            Messagebox.show_error(str(e), "错误")

    def run_show_predict_table():
        # 显示预测表，把标准输出捕获后显示到界面上
        try:
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            get_predict_table.show_tables()
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            output_text_c.delete("1.0", END)
            output_text_c.insert(END, output)
        except Exception as e:
            Messagebox.show_error(str(e), "错误")

    def run_generate_assembly_code():
        # 生成汇编代码，并提示生成成功
        filename = entry_file_c.get()
        if not filename:
            Messagebox.show_warning("请先选择 C 源文件！", "警告")
            return
        try:
            to_asm.to_asm(filename)
            Messagebox.show_info("汇编代码生成成功！\n已生成同名 .s 文件。", "成功")
        except Exception as e:
            Messagebox.show_error(str(e), "错误")

    btn_lex = ttk.Button(frame_buttons_c, text="词法分析", command=run_lexical_analysis, bootstyle=SUCCESS)
    btn_lex.grid(row=0, column=0, padx=5, pady=5)
    # 修改按钮文本及功能为语义分析
    btn_syntax = ttk.Button(frame_buttons_c, text="语义分析", command=run_syntax_analysis, bootstyle=SUCCESS)
    btn_syntax.grid(row=0, column=1, padx=5, pady=5)
    btn_midcode = ttk.Button(frame_buttons_c, text="生成中间代码", command=run_generate_intermediate_code, bootstyle=INFO)
    btn_midcode.grid(row=0, column=2, padx=5, pady=5)
    btn_predict = ttk.Button(frame_buttons_c, text="显示预测表", command=run_show_predict_table, bootstyle=SECONDARY)
    btn_predict.grid(row=1, column=0, padx=5, pady=5)
    btn_asm = ttk.Button(frame_buttons_c, text="生成汇编代码", command=run_generate_assembly_code, bootstyle=WARNING)
    btn_asm.grid(row=1, column=1, padx=5, pady=5)
    btn_exit_c = ttk.Button(frame_buttons_c, text="退出", command=app.quit, bootstyle=DANGER)
    btn_exit_c.grid(row=1, column=2, padx=5, pady=5)

    # ---------------- 汇编解析功能页 ----------------
    frame_asm = ttk.Frame(notebook, padding=10)
    notebook.add(frame_asm, text="汇编解析")

    # 汇编文件选择区
    frame_file_asm = ttk.Frame(frame_asm)
    frame_file_asm.pack(fill=X, pady=5)
    label_asm = ttk.Label(frame_file_asm, text="汇编文件路径：", width=16)
    label_asm.pack(side=LEFT)
    entry_file_asm = ttk.Entry(frame_file_asm, width=60)
    entry_file_asm.pack(side=LEFT, padx=5)

    def browse_file_asm():
        # 弹出对话框选择汇编文件
        file_path = filedialog.askopenfilename(
            title="选择 汇编文件",
            filetypes=[("汇编文件", "*.s"), ("所有文件", "*.*")]
        )
        if file_path:
            entry_file_asm.delete(0, END)
            entry_file_asm.insert(0, file_path)

    btn_browse_asm = ttk.Button(frame_file_asm, text="浏览", command=browse_file_asm, bootstyle=INFO)
    btn_browse_asm.pack(side=LEFT, padx=5)

    output_text_asm = ScrolledText(frame_asm, wrap="word", height=25, font=("Consolas", 10))
    output_text_asm.pack(fill=BOTH, expand=YES, padx=5, pady=5)

    # 汇编文件解析按钮区
    frame_buttons_asm = ttk.Frame(frame_asm)
    frame_buttons_asm.pack(pady=5)

    def run_parse_assembly_file():
        # 解析选中的汇编文件，并在界面上显示解析结果
        filename = entry_file_asm.get()
        if not filename:
            Messagebox.show_warning("请先选择汇编文件！", "警告")
            return
        try:
            output = parse_assembly_file_to_string(filename)
            output_text_asm.delete("1.0", END)
            output_text_asm.insert(END, output)
        except Exception as e:
            Messagebox.show_error(str(e), "错误")

    btn_parse_asm = ttk.Button(frame_buttons_asm, text="解析汇编代码", command=run_parse_assembly_file, bootstyle=SUCCESS)
    btn_parse_asm.pack(side=LEFT, padx=5, pady=5)
    btn_exit_asm = ttk.Button(frame_buttons_asm, text="退出", command=app.quit, bootstyle=DANGER)
    btn_exit_asm.pack(side=LEFT, padx=5, pady=5)

    app.mainloop()

if __name__ == "__main__":
    main()
