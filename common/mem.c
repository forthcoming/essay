#include<stdio.h>
#include<string.h>
#include <malloc.h>

int main(){
    // 内存操作函数单位是1byte即8bit
    int a[5] = {1, 2, 3, 4, 5}, b[5];
    memmove(b, a, sizeof(a));  // b=[1,2,3,4,5],基本可替代memcpy
    memset(a, 0, sizeof(a));   // a=[0,0,0,0,0]

    char c[]="avatar";  // sizeof(c)=7,c是char* const类型即指针常量
    memset(c, 97, sizeof(c));  // c=['a','a','a','a','a','a','a']

    char* d="avatar";  // sizeof(d)=4
    // d[0]='a';  // error
    // while(*d) printf("%c\t",*d++);
    char* f="avatar";
    printf("\n%p,%p,%p\n",c,d,f);  // d==f!=c

    int *p = (int *)malloc(20*sizeof(int));  // 申请的内存段内数据没有初始化
    free(p);
}
