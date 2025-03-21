
int add(int a, int b) {
    return a + b;
}

int main() {
    int arr[5];   // 声明一个大小为 5 的整型数组
    int i = 0;
    int sum = 0;

    // 正确的数组赋值
    arr[0] = 10;
    arr[1] = 20;
    arr[2] = 30;
    arr[3] = 40;
    arr[4] = 50;

    // 正确的数组访问
    sum = arr[2];

    // 错误：数组下标越界（有效下标为 0~4，arr[5] 超出范围）
    arr[5] = 60;

    // 错误：未声明变量 x 的使用
    x = 100;

    // 正确
    int result = add(10, 20);
    printf("result = %d\n", result);

    return 0;
}
