

// 正确的函数定义
int add(int x, int y) {
    // 返回两个数的和
    int result;
    result = x + y;
    return result;
}

// 测试同一作用域内重复声明错误
int testRedecl() {
    int a;
    int a; // 错误：重复声明变量 a
    return a;
}

// 测试未声明变量的使用
int testUndeclared() {
    int a;
    a = 10;
    b = 20; // 错误：变量 b 未声明
    return a;
}

// 测试数组越界访问错误
int testArray() {
    int arr[3];
    arr[0] = 1;
    arr[1] = 2;
    arr[2] = 3;
    arr[3] = 4; // 错误：数组下标越界 (有效索引为 0, 1, 2)
    return arr[0];
}

// 测试函数调用参数数量不匹配错误
int testFuncCallMismatch(int x) {
    int sum = add(x); // 错误：调用 add 时参数数量不匹配，应该提供两个参数
    return sum;
}

// 测试调用未声明的函数
int testUndeclaredFunc() {
    int res = unknownFunc(5); // 错误：函数 unknownFunc 未声明
    return res;
}

// 测试 printf 的变参函数调用（应正确通过，不检查参数数量）
int testPrintf() {
    printf("Value: %d\n", 10); // 内置函数，允许变参
    return 0;
}

// 测试嵌套作用域中的重复声明错误
int testNestedScope() {
    int a = 5;
    {
        int a = 10; // 合法：在新的作用域中声明
        a = a + 1;
    }
    int a; // 错误：在同一外部作用域内重复声明变量 a
    return a;
}

// 测试对非数组变量进行数组引用错误
int testNonArrayAccess() {
    int x = 10;
    int y = x[0]; // 错误：变量 x 不是数组
    return y;
}

// 主函数调用所有测试函数
int main() {
    add(1, 2);
    testRedecl();
    testUndeclared();
    testArray();
    testFuncCallMismatch(5);
    testUndeclaredFunc();
    testPrintf();
    testNestedScope();
    testNonArrayAccess();
    return 0;
}
