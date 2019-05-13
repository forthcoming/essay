kill(跟linux一致)
pid > 0: 向进程号pid的进程发送信号,可以验证kill杀死父进程,子进程会不会结束
pid = 0: 向当前进程所在的进程组发送信号
pid < 0: 向进程组号为-pid的所有进程发送信号

#######################################################################################################################

#include <stdio.h>
#include <unistd.h>  
int main(){
    for(int i = 0; i<3; i++){
        fork();
        printf("pid:%d ppid:%d pgid:%d\n",getpid(),getppid(),getpgid(0));  // 2+4+8=14 outputs
    }
}
// 子进程是从fork后面到那个指令开始执行
// 在父进程中fork返回新创建子进程的进程ID

#######################################################################################################################

#include <stdio.h>  
#include <unistd.h>
int main()   // 总共有20个进程,除了main进程,还有19个子进程
{  
   fork();  
   fork() && fork() || fork();  
   fork();  
   printf("+\n");  
}  

#######################################################################################################################

#include <stdio.h>  
#include <unistd.h>
#include <wait.h>
#include <stdlib.h>
int main()
{
    pid_t pid = fork();
    if (pid < 0){
        puts("fork error");
    }
    else if(pid == 0){
        sleep(4);
        printf("I am a Child Process, pid is %d.\n", getpid());
        exit(1);
        printf("此处不会被输出\n");
    }
    else{
        pid_t _pid=wait(NULL);  // 相当于join,调用wait()函数的父进程将阻塞式等待该进程的任意一个子进程结束后,回收该子进程的内核进程资源
        printf("子进程%d结束,开始执行父进程\n",_pid);  // 注意要加\n刷新缓冲区
        sleep(8);       
    }
}
// 如果需要用父进程回收子进程,就要在父进程里使用waitpid,这个函数会让父进程阻塞,直到子进程执行完成
// waitpid各种参数都只能针对一个进程生效,如果在options参数中指定WNOHANG可以使父进程不阻塞而立即返回0,作用是回收子进程并收集子进程的pid
// 若希望父进程退出子进程也退出的话,可以使用线程.因为若进程结束,则还没结束的线程一定会立刻结束

#######################################################################################################################

#include <stdio.h>  
#include <unistd.h>
int main()  // 孤儿进程,multiprocessing不会产生孤儿进程,可以产生僵尸进程,需要用os.fork模拟产生孤儿进程
{
    pid_t pid = fork();
    if(pid == 0){
        for(int i=0;i<5;++i){
            sleep(1);
            printf("I am a Child Process, pid is %d, ppid is %d.\n", getpid(),getppid());    
        }
    }
    else{
        printf("I am a Parent Process, pid is %d, ppid is %d.\n", getpid(),getppid());
        sleep(2);
    }
}
/*
I am a Parent Process, pid is 9758, ppid is 2426.
I am a Child Process, pid is 9759, ppid is 9758.
I am a Child Process, pid is 9759, ppid is 1349.
I am a Child Process, pid is 9759, ppid is 1349.
I am a Child Process, pid is 9759, ppid is 1349.
I am a Child Process, pid is 9759, ppid is 1349.
*/
// 孤儿进程: 父进程退出,而它的一个或多个子进程还在运行,那么那些子进程将成为孤儿进程.孤儿进程将被init进程(进程号为1)所收养,成为该子进程的父进程,并对它们完成状态收集工作
// 僵尸进程: 进程使用fork创建子进程,如果子进程退出,父进程还在运行,并且没有调用wait或waitpid获取子进程的状态信息,那么子进程的进程描述符仍然保存在系统中,形成僵死进程
// 僵尸进程将会导致资源浪费,而孤儿进程并不会有什么危害
// 僵尸进程kill -9都不能杀掉,有一个办法是,找到僵尸进程的父进程,将父进程杀掉,子进程就自动消失了
// 找僵尸进程的父进程: ps -ef | grep defunct

#######################################################################################################################

#include <stdio.h>  
#include <unistd.h>
#include <wait.h>
#include <stdlib.h>
#include <signal.h>

void sig_int(int signo)
{
    // 放在子进程中会执行一遍,放在主进程中会执行两遍
    printf("pid:%d,当在终端上按下ctrl+c后会产生SIGINT信号\n",getpid());
}

/*
当子进程退出的时候,内核都会给父进程一个SIGCHLD信号,如果父进程不关心子进程什么时候结束,可以用signal(SIGCHLD,SIG_IGN)通知内核,当子进程结束后内核会回收
默认采用SIG_DFL,代表默认的处理方式为不会理会这个信号,但是也不会丢弃该信号量,如果系统不调用wait/waitpid,则会变成僵尸进程
通过fork两次的方式也可以消除僵尸进程,即"主进程 => 儿子进程"修改为"主进程 => 爸爸进程 => 儿子进程",爸爸进程就是初始化儿子进程,然后结束,注意要在主进程中调用join()回收爸爸进程
*/
int main()  
{
    int x=1;
    signal(SIGCHLD,SIG_IGN);  // 第二个参数可以自定义,如将SIG_IGN修改为自定义sig_int方法,专门用来处理对应的信号
    pid_t pid = fork();
    if(pid == 0){
        x+=3;
        printf("x:%d &x:%p I am a Child Process, pid is %d,进程组id:%d.\n", x,&x,getpid(),getpgid(0));   // 获得pid为p的进程所在组的组ID,当p为0时,获得本进程的组ID
        sleep(4);
        exit(1);
    }
    else{
        sleep(8);         
        printf("x:%d &x:%p 父进程%d开始执行,进程组id:%d.\n",x,&x,getpid(),getpgid(0)); //进程组id = 父进程id,只要进程组中有一个进程存在,进程组就存在,与组长进程是否终止无关
        printf("父进程执行结束\n");
    }

}
// 每一个进程都属于一个进程组,当一个进程被创建的时候,它默认是其父进程所在组的成员
// 子进程派生的子进程也属于父进程为组长的进程组
// 可以使用ps j这个命令获取进程的PPID, PID, PGID and SID(会话ID)
