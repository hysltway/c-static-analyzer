int main(){

    int i = 1;
    printf("正在打印99乘法表！\n");
    while(i < 10){
        int j = i;
        while(j < 10){
            printf("%d*%d=%d\t",i, j, i*j);
            j = j + 1;
        }
        printf("\n");
        i = i +1;
    }
}