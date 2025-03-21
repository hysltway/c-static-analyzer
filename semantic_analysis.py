# // 1. 正确的函数定义和调用
# // 2. 同一作用域内变量的重复声明错误
# // 3. 未声明变量的使用错误
# // 4. 数组越界访问错误
# // 5. 函数调用参数数量不匹配错误
# // 6. 调用未声明函数错误
# // 7. 对非数组变量的数组引用错误
# // 8. 嵌套作用域中重复声明错误
# // 9. // 注释的处理

import re
from pycparser import c_parser, c_ast

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]  # 每个元素表示一个作用域中的符号字典

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def add(self, name, info, lineno=None):
        # 检查当前作用域中是否已声明该符号
        if name in self.scopes[-1]:
            raise Exception(f"Redeclaration of '{name}' at line {lineno}")
        self.scopes[-1][name] = info

    def lookup(self, name):
        # 从最近的作用域向外查找符号
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

class SemanticAnalyzerVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        # 预定义内置函数 printf（variadic 表示可变参数，这里跳过参数数量检查）
        self.symbol_table.add("printf", {"kind": "function", "type": "int", "params": None, "variadic": True}, lineno=0)

    def error(self, msg, node):
        line = node.coord.line if node.coord else "unknown"
        self.errors.append(f"Error at line {line}: {msg}")

    def visit_FuncDef(self, node):
        func_name = node.decl.name
        func_type = self.get_type_from_decl(node.decl)
        params = self.get_func_params(node.decl)
        try:
            self.symbol_table.add(func_name, {'kind': 'function', 'type': func_type, 'params': params},
                                    lineno=node.decl.coord.line if node.decl.coord else None)
        except Exception as e:
            self.error(str(e), node.decl)
        # 进入函数体前，新建一个作用域，并将函数参数加入该作用域
        self.symbol_table.push_scope()
        if params:
            for param in params:
                try:
                    self.symbol_table.add(param['name'], param, lineno=node.decl.coord.line if node.decl.coord else None)
                except Exception as e:
                    self.error(str(e), node.decl)
        self.visit(node.body)
        self.symbol_table.pop_scope()

    def visit_Compound(self, node):
        # 进入复合语句时新建一个作用域
        self.symbol_table.push_scope()
        for stmt in node.block_items or []:
            self.visit(stmt)
        self.symbol_table.pop_scope()

    def visit_Decl(self, node):
        if isinstance(node.type, (c_ast.TypeDecl, c_ast.ArrayDecl)):
            var_name = node.name
            var_type = self.get_type_from_decl(node)
            info = {'kind': 'variable', 'type': var_type}
            if isinstance(node.type, c_ast.ArrayDecl):
                size = self.eval_constant(node.type.dim)
                info['array'] = True
                info['size'] = size
            else:
                info['array'] = False
            try:
                self.symbol_table.add(var_name, info, lineno=node.coord.line if node.coord else None)
            except Exception as e:
                self.error(str(e), node)
        # 如果声明有初始化表达式，也访问该表达式
        if node.init:
            self.visit(node.init)

    def visit_Assignment(self, node):
        # 检查赋值语句：左值必须已声明，右侧表达式进行递归检查
        self.check_lvalue(node.lvalue)
        self.visit(node.rvalue)

    def check_lvalue(self, node):
        if isinstance(node, c_ast.ID):
            symbol = self.symbol_table.lookup(node.name)
            if not symbol:
                self.error(f"Variable '{node.name}' not declared", node)
        elif isinstance(node, c_ast.ArrayRef):
            self.visit_ArrayRef(node)
        else:
            self.visit(node)

    def visit_ArrayRef(self, node):
        # 检查数组引用
        if isinstance(node.name, c_ast.ID):
            symbol = self.symbol_table.lookup(node.name.name)
            if not symbol:
                self.error(f"Array '{node.name.name}' not declared", node)
            else:
                if not symbol.get('array', False):
                    self.error(f"Variable '{node.name.name}' is not an array", node)
                else:
                    # 若下标为常量，则检查是否越界
                    index_val = self.eval_constant(node.subscript)
                    if index_val is not None and symbol.get('size') is not None:
                        if index_val < 0 or index_val >= symbol['size']:
                            self.error(f"Array index {index_val} out of bounds for array '{node.name.name}' of size {symbol['size']}", node)
        else:
            self.visit(node.name)
        self.visit(node.subscript)

    def visit_ID(self, node):
        # 检查标识符是否已声明
        symbol = self.symbol_table.lookup(node.name)
        if not symbol:
            self.error(f"Identifier '{node.name}' not declared", node)

    def visit_FuncCall(self, node):
        if isinstance(node.name, c_ast.ID):
            func_symbol = self.symbol_table.lookup(node.name.name)
            if not func_symbol:
                self.error(f"Function '{node.name.name}' not declared", node)
            elif func_symbol.get('kind') != 'function':
                self.error(f"Identifier '{node.name.name}' is not a function", node)
            else:
                # 如果函数参数为 None 或标记为 variadic，则不检查参数数量
                if func_symbol.get('params') is not None:
                    expected_params = func_symbol.get('params')
                    provided_args = node.args.exprs if node.args and node.args.exprs else []
                    if len(expected_params) != len(provided_args):
                        self.error(f"Function '{node.name.name}' expects {len(expected_params)} arguments, but {len(provided_args)} provided", node)
                    for arg in provided_args:
                        self.visit(arg)
                else:
                    if node.args:
                        for arg in node.args.exprs:
                            self.visit(arg)
        else:
            self.visit(node.name)
        if node.args:
            self.visit(node.args)

    def visit_BinaryOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def get_type_from_decl(self, decl):
        return "int"

    def get_func_params(self, decl):
        params = []
        if isinstance(decl.type, c_ast.FuncDecl) and decl.type.args:
            for param in decl.type.args.params:
                if isinstance(param, c_ast.Decl):
                    param_type = self.get_type_from_decl(param)
                    params.append({'name': param.name, 'type': param_type})
        return params

    def eval_constant(self, node):
        if isinstance(node, c_ast.Constant) and node.type == 'int':
            try:
                return int(node.value)
            except:
                return None
        elif isinstance(node, c_ast.BinaryOp):
            left = self.eval_constant(node.left)
            right = self.eval_constant(node.right)
            if left is not None and right is not None:
                try:
                    if node.op == '+':
                        return left + right
                    elif node.op == '-':
                        return left - right
                    elif node.op == '*':
                        return left * right
                    elif node.op == '/':
                        return left // right  # 整数除法
                    else:
                        return None
                except Exception:
                    return None
        else:
            return None

class SemanticAnalyzer:
    def __init__(self, filename):
        self.filename = filename
        self.ast = None
        self.errors = []

    def preprocess_code(self, code):
        # 删除代码中的 // 风格注释
        return re.sub(r'//.*', '', code)

    def parse(self):
        try:
            parser = c_parser.CParser()
            with open(self.filename, "r", encoding="utf-8") as f:
                code = f.read()
            # 预处理代码，移除 // 注释
            code = self.preprocess_code(code)
            self.ast = parser.parse(code, filename=self.filename)
        except Exception as e:
            self.errors.append(f"Parsing error: {e}")
            # 不再退出程序，以便后续能收集更多错误

    def analyze(self):
        if not self.ast:
            self.errors.append("No AST generated due to previous parsing errors.")
            return
        visitor = SemanticAnalyzerVisitor()
        visitor.visit(self.ast)
        self.errors.extend(visitor.errors)

    def report(self):
        print("Semantic Analysis Report:")
        print(f"File: {self.filename}")
        if self.errors:
            print(f"Total errors found: {len(self.errors)}")
            for err in self.errors:
                print(err)
        else:
            print("No semantic errors found.")

if __name__ == "__main__":
    filename = "./test/erroc2.c"
    analyzer = SemanticAnalyzer(filename)
    analyzer.parse()
    analyzer.analyze()
    analyzer.report()
