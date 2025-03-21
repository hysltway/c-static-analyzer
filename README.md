#  C语言静态分析器

这是一个基于Python开发的C语言静态分析工具，提供了词法分析、语法分析、语义分析等功能，并可以生成中间代码和汇编代码。


## 📂 项目结构

```
.
├── main.py              # 主程序入口，包含GUI界面
├── lexer.py             # 词法分析器
├── LR.py                # LR(1)语法分析器
├── semantic_analysis.py # 语义分析模块
├── generate.py          # 中间代码生成器
├── to_asm.py            # 汇编代码生成器
├── get_predict_table.py # 预测表生成器
├── test/                # 测试用例目录
└── other/               # 其他辅助文件
```

## 🛠️ 环境要求

- Python 3.x
- ttkbootstrap (用于GUI界面)
- pyparsing (用于语法解析)

## ▶️ 使用方法

1. 运行主程序：
   ```bash
   python main.py
   ```

2. 在GUI界面中：

   ![image-20250321095620004](./image/image-20250321095620004.png)

   - 选择C语言源文件
   - 点击"词法分析"按钮进行词法分析

   ![image-20250321095656797](./image/image-20250321095656797.png)

   - 点击"语法分析"按钮进行语法分析

   ![image-20250321095727835](./image/image-20250321095727835.png)

   - 点击"生成中间代码"按钮生成中间代码
   - 点击"生成汇编代码"按钮生成汇编代码
   - 选择汇编文件并点击"解析汇编文件"按钮查看汇编代码结构

## ✨ 主要功能说明

###  词法分析
词法分析器负责将输入的C语言源代码分解成token序列。它能够识别并分类各种基本语法单元，包括关键字、标识符、运算符、数字常量等。分析过程中会生成详细的token列表，并维护一个变量表，用于后续的语法分析和语义分析。

###  语法分析
语法分析器采用LR(1)分析法，通过构建预测分析表来实现自底向上的语法分析。分析过程中会生成完整的语法树，并能够处理各种C语言语法结构，包括变量声明、函数定义、控制语句等。分析器会实时显示分析过程和结果，帮助理解代码的语法结构。

###  语义分析
语义分析模块负责进行类型检查和语义验证。它会检查变量的声明和使用是否符合规范，验证函数调用的参数是否匹配，并确保各种表达式和语句的语义正确性。分析器会检测并报告各种语义错误，如类型不匹配、未声明变量使用等。

###  代码生成
代码生成模块首先将语法树转换为四元式形式的中间代码，这种中间表示形式便于优化和转换。随后，代码生成器将中间代码转换为目标汇编代码，支持基本的汇编指令生成。生成的汇编代码可以直接使用gcc等工具进行汇编和链接，最终生成可执行文件。

## ⚠️ 注意事项

- 确保输入的C语言源代码符合标准C语法
- 汇编代码生成支持基本的指令集
- 建议使用UTF-8编码的源文件

## 🙏 鸣谢

本项目参考了 [Py-Compiler](https://github.com/flymysql/Py-Compiler) 项目的实现思路和部分代码，特此鸣谢。
