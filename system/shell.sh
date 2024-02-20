#include <stdio.h>
#include <string.h>
#include <cstdlib>
#include <unistd.h>

int main()
{
    # VIRT: virtual memory usage RES: resident memory usage,进程当前使用的内存大小 SHR: shared memory
    printf("%d\n", getpid());
    int test = 0;
  
    char * p = (char *)malloc(1024*1024*512);  // new效果类似,分配512M,未使用,下面的VIRT, RES, SHR单位是KB
    scanf("%d", &test);                  // VIRT: 526740     RES: 752    SHR: 688

    memset(p, 0, 1024 * 1024 * 10);      // 使用10M
    scanf("%d", &test);                  // VIRT: 526740     RES: 11808  SHR: 1516

    memset(p, 0, 1024 * 1024 * 50);      // 使用50M
    scanf("%d", &test);                  // VIRT: 526740     RES: 52728  SHR: 1516

    free(p);
    scanf("%d", &test);                  // VIRT: 2448       RES: 1444   SHR: 1364
}
# 堆、栈分配的内存,如果没有使用是不会占用实存的,只会记录到虚存
# g++ test.c -o out
# ./out 运行
# top -p 15870
------------------------------------------------------------------------------------------------------------------------
shadowsocks
pip install git+https://github.com/shadowsocks/shadowsocks.git@master
vim /etc/shadowsocks.json
{
    "server":"47.75.73.29",
    "server_port":8080,
    "local_address": "127.0.0.1",
    "local_port":1080,
    "password":"******",
    "timeout":60,
    "method":"rc4-md5",
    "fast_open": false
}
sslocal -c /etc/shadowsocks.json -d start  # -d代表后台运行
------------------------------------------------------------------------------------------------------------------------
touch file.txt # 创建一个空文件,改变文件或目录时间
-a: 修改atime
-m: 修改mtime
-c: 仅修改文件的时间,(三个时间一起修改),若该文件不存在则不建立新的文件
-d: 后面可以接想修改的日期而不用目前的日期,也可以使用–date="日期或时间"
-t: 后面可以接想修改是时间而不用目前的时间,格式为[YYMMDDhhmm]
------------------------------------------------------------------------------------------------------------------------
lsof(list open files)
lsof file_name              # 查看哪些进程正在使用这个文件
lsof -t -u user_name        # 查看某个用户打开的文件,-t选项只返回PID
lsof | grep mysql           # 列出某个进程打开的文件
lsof -p 12,34               # 列出多个进程号打开的文件
lsof -i :3306               # 列出使用某个端口的进程信息
kill -9 `lsof -t -u daniel` # 杀死某个用户运行的所有进程
------------------------------------------------------------------------------------------------------------------------
find                 
find . -maxdepth 1 -iname '[a-z][0-9]'.sh       # iname忽略大小写,后面跟的是字符串or通配符,非正则,如果跟通配符则两边需要加引号
find /etc -maxdepth 1 -name '*.conf'            # 查找/etc下名称中带有*.conf的文件,查找一层
find /etc -maxdepth 2 -mindepth 2 -name 1.txt   # 查找/etc下名称是1.txt的文件,且只查找第二层
find /mnt -user student -group student          # 查找/mnt下所有人和所有组都是student的文件
find /mnt -type d|f|l                           # 查找/mnt下目录/文件/链接,不指定的话默认查找所有类型
find /mnt -name "init*" -a -type l              # 查找/mnt目录下名字带有init的软连接文件,-a 逻辑与(and),可省略;-o 逻辑或(or);! 逻辑非(not)
find /mnt -perm 444                             # 查找/mnt下文件权限为444的文件
find /mnt -size +20K                            # 查找/mnt下文件大小大于20k的文件
find /mnt -size -20K                            # 查找/mnt下文件大小小于20k的文件
find /mnt -mtime -10                            # 查找/mnt下10天内有修改的文件
find /mnt -name '*.conf' -exec rm -rf {} +      # 删除/mnt名称中带有.conf的文件,每条命令以+分隔,{}代表find的结果
如何删除形如"-a","a b"等文件?
touch -- -a "a b"
ls -i   
find -inum 节点数 -exec rm -rf {} +
------------------------------------------------------------------------------------------------------------------------
vim
:w [filename]   保存[另存为]
:wq             写入并离开vi,等价于ZZ
:q!             强迫离开并放弃编辑的文件

yy       复制光标所在行
p        粘贴字符到光标所在行下方
shift+p  粘贴字符到光标所在行上方

dd  删除光标所在行(删除也带有剪切的意思,可配合p键使用)
#dd 删除多个行,#代表数字,比如3dd表示删除光标行及光标的下两行

/search  正向查找,按n键把光标移动到下一个符合条件的地方
:%s/search/replace/g  把当前光标所处的行中的search单词,替换成replace,并把所有search高亮显示
:n1,n2s/search/replace/g  表示从多少行到多少行,把search替换成replace

Ctrl+u 向文件首翻半屏
Ctrl+d 向文件尾翻半屏
Ctrl+f 向文件首翻一屏
Ctrl+b 向文件尾翻一屏
gg  跳到行首
G   跳到末尾
ctrl+r   #反撤销
u  取消上一步操作,取消到上次打开文件的点上,并不是上次保存的点(相当于ctrl+z)
:r [ 文件名 ] - 导入下一个文件
:!Command  #在vim中执行shell命令
:set nu   文档每一行前列出行号
:set ff  查看文件格式,如果是dos,应该为:set ff=unix,用于解决shell脚本出现找不到路径或其他莫名错误(dos和linux换行符不一样)
:set nonu  取消行号(默认)
:set ic  搜索时忽略大小写
:set noic  严格区分大小写(默认)
:#   #代表数字,表示跳到第几行
注意:r可配合:!Command使用  如 :r !date
在/etc/vim/vimrc下对vim的修改对所有用户永久有效
在~/.vimrc下对vim的修改仅对当前用户永久有效
可以设置一些:set nu   :set ic
------------------------------------------------------------------------------------------------------------------------
sed
sed '5q' datafile                      # 打印前5行后,q让sed程序退出
sed -n '/north/p' datafile             # p指打印,默认打印所有行,-n只打印含有north的行
sed -n '/north/w newfile' datafile     # w指写操作,将匹配的行写入newfile文件中
sed -i 's/west/north/g' datafile       # 将所有行中的west替换成north,默认只打印结果,i让改动保存到datafile
sed -i '1,3d' datafile                 # 删除1~3行,'3,$d'删除从第3行到最后一行
sed -i '/north/c bus' datafile         # c指替换操作,将匹配的行更改为bus,a匹配north的下一行追加行bus,i匹配north的前一行追加行bus
sed -i 's/[0-9][0-9]$/&.5/' datafile   # &指匹配到的内容,所有两位数结尾的行后面加上.5
------------------------------------------------------------------------------------------------------------------------
正则表达式 & 通配符
正则表达式: 用于文本内容字符串的搜索和替换
通配符: 用来匹配文件名
*      匹配任意多个字符,与dos相同,sql用%
?      匹配任意单个字符,与dos相同,sql用_
[...]  匹配括号内出现的任意一个字符
[!...] 不匹配括号内出现的任意一个字符
\      代表转义字符,可以转义Enter,适用于指令太长的情况
------------------------------------------------------------------------------------------------------------------------
Hard Link & Symbolic Link
默认不带参数情况下,ln命令创建的是硬链接
硬链接文件与源文件的inode节点号相同,他们是完全平等关系,是同一个文件,硬链接不占用源文件大小空间
软链接文件(可理解为快捷方式)的inode节点号与源文件不同,他们是两个不同的文件
不能对目录/跨文件系统创建硬链接,创建软链接则没有限制
删除软链接/硬链接文件,对源文件无任何影响
删除链接文件的原文件,对硬链接文件无影响,会导致其软链接失效(红底白字闪烁状)
同时删除原文件及其硬链接文件,整个文件才会被真正的删除
------------------------------------------------------------------------------------------------------------------------
管道
echo "--help"|cat         # --help
echo "--help"|xargs cat   # 显示的是cat --help命令的帮助内容
cat `echo "--help"`       # 最终结果等价于 echo "--help"|xargs cat

-d: 默认情况下xargs将其标准输入中的内容以空白(包括空格/Tab/回车换行等)分割成多个之后当作命令行参数传递给其后面的命令,我们可以使用-d命令指定分隔符
-n: 表示将xargs生成的命令行参数,每次传递几个参数给其后面的命令执行
echo '11@22@33@44@55@66@77' |xargs -d '@' -n 3 echo 
output:
11 22 33
44 55 66
77

|将前面标准输出当做后面命令的标准输入,xargs将标准输入作为命令的参数
ls -l|awk '/\.zip/ {print $9}'|xargs -n 1 unzip  # xargs后面的命令必须支持多参数,有些命令如unzip就不支持输入多参数需要用-n 1解决
ps -ef|awk '/ktv-micseq/ && !/awk/ {print $2}'|xargs kill -9

exec只是find的一个参数,但``与|xargs可以用于任何命令
ls -l `find -perm 644`             //不推荐,不能处理带空格的文件,不能处理长参数
find -perm 644 |xargs ls -l        //推荐,不能处理带空格的文件,能处理长参数
find -perm 644 -exec ls -l '{}' +  //推荐,可以处理带空格等特殊字符的文件,能处理长参数,{}里面房find每条结果的+是固定格式
------------------------------------------------------------------------------------------------------------------------
awk -F|-v 'BEGIN{ } // {comand1;comand2} END{ }' file
-F 定义列分隔符
' ' 引用代码块,awk执行语句必须包含在内,注意必须是单引号
BEGIN{} 在对每一行进行处理之前,初始化代码,主要是引用全局变量,设置FS分隔符,BEGIN和END必须大写
{} 命令代码块,包含一条或多条命令,处理每一行时要执行的语句,命令之间用;间隔
// 用来定义需要匹配的模式(字符串或正则表达式)
END{} 在对每一行进行处理之后再执行的代码块,主要是进行最终计算或输出结尾摘要信息

对于G单位的大文件,awk正则速度比grep慢很多,但控制的粒度可以很小,比如精确到某个字段的正则匹配
建议是遇到大文件,先用grep筛选,然后再通过管道交给awk处理
awk数组是一种关联数组,下标可以是数字和字符串,使用前无需对数组名和下标提前声明,也无需指定元素个数

$0       当前记录(这个变量中存放着整个行的内容)
$1~$n    当前记录的第n个字段,字段间由FS分隔
NF       当前记录中的字段(列)个数,$(NF-2)代表分割后的倒数第2列
NR       行号(Number of Record),从1开始,如果有多个文件话,这个值会不断累加
FNR      行号,与NR不同的是这个值会是各个文件自己的行号
FS       输入字段分隔符,默认是空格或Tab
RS       输入的记录分隔符,默认为换行符
OFS      输出字段分隔符,默认也是空格
ORS      输出的记录分隔符,默认为换行符
FILENAME 当前输入文件的名字

统计每个用户的进程占了多少内存(统计的是RSS那一列)
ps aux | awk 'NR!=1 {a[$1]+=$6} END{for(i in a) print i":"a[i]"KB"}'
ntp:712KB
root:101716KB
redis:100644KB

计算接口一天的平均耗时
cat api.log|grep 'room_list'|grep '2019-10-15'|awk -F '\t' 'BEGIN{avg=0;cnt=0} {avg+=$8;cnt+=1} END{print avg/cnt}'

统计总行数和满足条件的总行数
cat api.log |awk -F '[:|,]' 'BEGIN{sum=0;cnt=0} {sum+=1} $2 ~/2019/ {cnt+=1;print cnt} END{print sum,cnt}'

cat netstat.txt
Proto Recv-Q Send-Q Local-Address          Foreign-Address             State
tcp        0   4166 coolshell.cn:80        61.148.242.38:30901         ESTABLISHED
tcp        0      1 coolshell.cn:70        124.152.181.209:26825       FIN_WAIT1
tcp        0      0 coolshell.cn:80        110.194.134.189:70        ESTABLISHED
tcp        0      0 coolshell.cn:80        183.60.212.163:51082        TIME_WAIT
tcp        0      1 coolshell.cn:70        208.115.113.92:70        LAST_ACK
tcp        0      0 coolshell.cn:80        123.169.124.111:70       ESTABLISHED
tcp        0      0 coolshell.cn:80        117.136.20.85:50025         FIN_WAIT2
awk -F ' ' '$3>0 && $3<=1 || NR==1 || $6 ~/FIN|TIME/ {print NR,$1,"avatar",$2}' OFS="\t" netstat.txt 
1	Proto	avatar	Recv-Q
3	tcp	avatar	0
5	tcp	avatar	0
6	tcp	avatar	0
8	tcp	avatar	0
awk '/70/' netstat.txt
tcp        0      1 coolshell.cn:70        124.152.181.209:26825       FIN_WAIT1
tcp        0      0 coolshell.cn:80        110.194.134.189:70        ESTABLISHED
tcp        0      1 coolshell.cn:70        208.115.113.92:70        LAST_ACK
tcp        0      0 coolshell.cn:80        123.169.124.111:70       ESTABLISHED
awk '!/70/' netstat.txt
Proto Recv-Q Send-Q Local-Address          Foreign-Address             State
tcp        0   4166 coolshell.cn:80        61.148.242.38:30901         ESTABLISHED
tcp        0      0 coolshell.cn:80        183.60.212.163:51082        TIME_WAIT
tcp        0      0 coolshell.cn:80        117.136.20.85:50025         FIN_WAIT2
awk '$5 !~/70/' netstat.txt   # 正则取反
Proto Recv-Q Send-Q Local-Address          Foreign-Address             State
tcp        0   4166 coolshell.cn:80        61.148.242.38:30901         ESTABLISHED
tcp        0      1 coolshell.cn:70        124.152.181.209:26825       FIN_WAIT1
tcp        0      0 coolshell.cn:80        183.60.212.163:51082        TIME_WAIT
tcp        0      0 coolshell.cn:80        117.136.20.85:50025         FIN_WAIT2
awk 'NR!=1 {print $4,$5 > $6}' netstat.txt   # 把指定的列输出到文件
awk 'NR!=1 {if($6 ~/TIME|ESTABLISHED/) print > "1.txt"; else if($6 ~/FIN/) print > "2.txt"; else print > "3.txt" }' netstat.txt 
------------------------------------------------------------------------------------------------------------------------
ab
sudo apt install apache2-utils
Usage: ab [options] [http[s]://]hostname[:port]/path    # 注意命令要加单引号,-T和-p要一起使用
Options are:
    -n requests     Number of requests to perform
    -c concurrency  Number of multiple requests to make at a time
    -t timelimit    Seconds to max. to spend on benchmarking This implies -n 50000
    -s timeout      Seconds to max. wait for each response Default is 30 seconds
    -T content-type Content-type header to use for POST/PUT data, eg.'application/x-www-form-urlencoded' Default is 'text/plain'
    -p postfile     File containing data to POST. Remember also to set -T
    -X proxy:port   Proxyserver and port number to use
    -C attribute    Add cookie, eg. 'Apache=1234'. (repeatable)
    -H attribute    Add Arbitrary header line, eg. 'Accept-Encoding: gzip',Inserted after all normal header lines. (repeatable)
ab -c 30 -n 5000 -H 'admin:sz_xlp' -X '127.0.0.1:80' 'http://ring.com/room/room_list?birthday=1990&app_agent=ccktv-ios&page_index=0&page_size=50'
data.json  => {"user_ids": "1,2","room_ids":"1,2","app_agent":"ccktv-ios"}  # 必须是双引号
ab -c 30 -n 5000 -H 'admin:sz_xlp' -T 'application/json' -X '127.0.0.1:80' -p /home/ccktv/data.json 'http://ring.com/room/room_list'
Server Hostname:        ring.com
Server Port:            80
Document Path:          room/room_list
Document Length:        825 bytes                                          (供测试的URL返回的文档大小)
Non-2xx responses:      0                                                  (非200状态码次数,n次请求中失败的次数,只有失败了才会出现该项)
Concurrency Level:      30                                                 (c参数)
Time taken for tests:   8.192 seconds                                      (压力测试消耗的总时间)
Complete requests:      5000                                               (压测总次数)
Failed requests:        0                                                  (失败的请求数)
Write errors:           0
Total transferred:      4805000 bytes
Total POSTed:           1430000
HTML transferred:       4125000 bytes
Requests per second:    610.34 [#/sec] (mean)                              (平均每秒的请求数,Complete requests/Time taken for tests)
Time per request:       49.153 [ms] (mean)                                 (所有并发用户(这里是30)都请求一次的平均时间)
Time per request:       1.638 [ms] (mean, across all concurrent requests)  (单个用户请求一次的平均时间,Time per request/Concurrency Level)
Transfer rate:          572.79 [Kbytes/sec] received
                        170.47 kb/s sent
                        743.26 kb/s total
------------------------------------------------------------------------------------------------------------------------
download & upload
ssh -p port user@ip     # 远程连接
scp file1 user@ip:file2 # 上传or下载文件(传输方向由file1 -> file2),文件夹需要在scp后加-r参数
rz -y #  Receive Zmodem,上传文件,y代表覆(默认不覆盖)
sz filename  # Send Zmodem,下载文件
rsync -a 源文件 user@目标IP:路径 # -a表示递归方式传输文件,并保持所有文件属性,rsync默认只对差异文件做更新,也可以全量(优于scp),使用时需要目标服务器开启sshd
1. apt install openssh-server
2. /etc/init.d/ssh start
------------------------------------------------------------------------------------------------------------------------
~/.bash_history  #记录用户的历史命令,当用户logout时才会将本次历史缓存写入其中,history -c与echo>~/.bash_history同时使用才能彻底删除历史记录
~/.bashrc # 作用于当前用户,该文件还可以定义别名
/etc/profile # 作用于所有用户,写错后可能导致系统登不进去,该文件还可以定义别名
/etc/hosts # 作用与windows的hosts文件相同

vim ~/.bashrc
REDIS=/root/redis/bin
PYCHARM=/root/pycharm/bin
CONDA=/root/miniconda3/bin
export PATH=$PATH:$REDIS:$PYCHARM:$CONDA
export PYSPARK_PYTHON=/usr/local/bin/python3

alias # 列出所有别名
avatar='ls -al /home' #给命令起别名(命令带参数时要加引号)
------------------------------------------------------------------------------------------------------------------------
crontab(minute hour day month week)
43 21 * * *          # 每天21:43
0 17 * * 1           # 每周一17:00
0,10 17 * * 0,2,3    # 每周日,周二,周三的17:00和17:10
0-10 17 1 * *        # 毎月1日从17:00到7:10毎隔1分钟
42 4 1 * * 　 　     # 毎月1日的4:42分
0 21 * * 1-6　　     # 周一到周六21:00
*/10 * * * *　　　　  # 每隔10分
* 1 * * *　　　　　　 # 从1:0到1:59每隔1分钟
0 1 * * *　　　　　　 # 1:00 执行
0 * * * *　　　　　　 # 毎时0分每隔1小时
2 8-20/3 * * *　 　　# 8:02,11:02,14:02,17:02,20:02
30 5 1,15 * *　　 　 # 1日和5日的5:30
less /var/log/cron 可以查看crontab执行脚本的时间
------------------------------------------------------------------------------------------------------------------------
kill
kill -9 pid  #强行关闭进程
kill -1 pid  #重启进程(重新读取配置,也可写为kill -HUP)
pkill httpd  #杀掉进程及其子进程 
------------------------------------------------------------------------------------------------------------------------
init [0~6] #切换运行级别,必须是root用户
0: 系统关机
1: 单用户状态(用于维护)
2: 多用户模式,没有网络模式
3: 多用户模式,有网络模式
4: 系统未使用,留给用户自定义
5: 多用户模式&运行Xwindow
6: 重新启动
------------------------------------------------------------------------------------------------------------------------
重定向
/dev/null  #空设备,它丢弃一切写入其中的数据
<          #标准输入重定向
>          #标准输出运算符,覆盖写
>>         #标准输出运算符,追加写
2>         #错误重定向,如果命令执行正确则什么都不做
2>>        #错误重定向,如果命令执行正确则什么都不做
&>         #正确错误一起输入到某个文件中
&>>        #正确错误一起输入到某个文件中
cat xyz >> access.log 2>> error.log
------------------------------------------------------------------------------------------------------------------------
df & du & fdisk
df -h  # 查看磁盘使用状态
du -ah /home/user  # 显示所有文件大小信息(显示文件所占用的block大小,默认linux系统分区的block size是4k,即使文件只有1个字节也会占用4k)
du -sh /home/user  # 显示指定目录占有空间总和,不循环显示子目录,ls -lh显示的是文件夹下文件的路径占用空间大小
fdisk -l  # 查看磁盘分区信息
------------------------------------------------------------------------------------------------------------------------
快捷键
ctrl C 终止当前命令
ctrl Z 挂起当前命令(暂停),jobs查看被挂起的进程
ctrl U 在提示符下,将整行命令删除
ctrl R 在history中搜索匹配命令
ctrl L 等价于clear
ctrl insert 复制
shift insert 粘贴
ctrl shift T   打开一个新的终端窗口
------------------------------------------------------------------------------------------------------------------------
tar(打包压缩目录或文件,压缩后文件格式为*.tar.gz)
tar czf new.tar.gz old1 old2 #压缩文件夹生成new.tar.gz
tar xzf new.tar.gz #解压缩*.tar.gz格式的文件
-----------------------------------------------------------------------------------------------------------------------
ssh -C -f -N -g -L 12450:10.1.138.93:3306 coolshot@10.1.138.64     # 端口转发
该命令一般在跳板机(10.16.2.46)中执行
12450                                       # 跳板机中监听的端口
10.1.138.93:3306                            # 需要连接的mysql
coolshot@10.1.138.64                        # 最终连接mysql的主机
mysql -uu_coolshot -P12450 -h10.16.2.46 -p  # 外部连接mysql
------------------------------------------------------------------------------------------------------------------------
ps & netstat
ps -ef | grep httpd # 查看httpd进程,第二列显示的是进程ID,可配合kill命令来关闭进程,dos下用tasklist | findstr httpd.exe
常用参数:
-ef: 标准格式输出,注意"-"不能省
aux: BSD格式输出
netstat -apn | grep 27017 # 查看27017端口使用情况(包括进程名,pid,port等信息),dos下用-abn
ps -efL|grep pid # 查看某个进程下的所有线程,用LWP表示
pstree -p pid    # 查看某个进程下的所有线程
top -p pid       # 然后按H,查看某个进程下的所有线程
ps -efj          # j获取进程的PPID, PID, PGID and SID(会话ID)

top(动态显示进程列表)
top -d n: 每n秒刷新一次,默认设置每3秒钟刷新一次,按CPU占有率降序排列
u: 显示某个用户下的进程信息
h: 帮助信息
k: 输入进程ID关闭进程
i: 忽略空闲进程
s: 修改刷新间隔
M: 按内存占有率降序排列
P: 按CPU占有率降序排列
N: 以PID大小降序排列
q: 退出top模式
c: 开启COMMAND列详情,可以找到对应的进程启动者
空格: 手动刷新
%MEM: 进程使用物理内存百分比
S: 进程状态  R=>运行 S=>睡眠  Z=>僵尸进程
------------------------------------------------------------------------------------------------------------------------
nohup &
&: 后台运行,即使你用ctrl C,进程照样运行,因为对SIGINT信号免疫.但如果你直接关掉shell,进程同样消失.可见&对SIGHUP信号不免疫
nohup: 忽略SIGHUP信号,关闭shell,进程还是存在的.但如果你直接在shell中用Ctrl C,进程也会消失,因为对SIGINT信号不免疫
所以要让进程真正不受Ctrl C和shell关闭的影响,就同时用nohup processname &,nohup命令使标准输出和标准错误默认重定向到nohup.out文件
nohup java -jar monitor.jar > /home/java.log &
nohup python -u counter.py args >> /logs/counter.log &   # -u参数可以立即输出
------------------------------------------------------------------------------------------------------------------------
合并文件(uniq命令可以去除排序过的文件中的重复行,也就是说为了使uniq起作用,所有的重复行必须是相邻的)
取出两个文件行的并集(重复的行只保留一份),结果按行排序
cat file1 file2 | sort | uniq
取出两个文件行的交集(只留下同时存在于两个文件的行),结果按行排序
cat file1 file2 | sort | uniq -d
合并两个文件,删除行交集,留下其他的行,结果按行排序
cat file1 file2 | sort | uniq -u
sort filename -r  # 逆序排序
------------------------------------------------------------------------------------------------------------------------
date
[root@local ~]# date
Thu Dec 15 16:55:22 CST 2016
[root@local ~]# date -d yesterday +%Y-%m-%d
2016-12-14
------------------------------------------------------------------------------------------------------------------------
ls -l
drwxr-xr-x  2  avatar  root  4096  Mar 10 22:25  Desktop
d: 文件类型为目录,此外-代表普通文件,l代表链接文件,s代表套接字文件
rwx: 文件所有者对该文件的权限
r-x: 文件所在组用户对该文件的权限
r-x: 其他组用户对该文件的权限
2: 文件数,对于目录文件只统计第一级子目录数
avatar: 用户名
root: 组名
4096: 文件大小,单位bit
Mar 10 22:25: 创建日期或mtime(非ctime与atime即cat chmod等不会改变时间)
Desktop: 文件名

ls -lrt   # 最近访问的文件会出现在最下方
ls -l `which touch` # 命令替换,注意与管道的区别
ls -l *.conf *.aof | awk 'BEGIN{sum=0} {sum+=$5} END {print sum}'  # 计算所有的.conf和.aof文件大小
------------------------------------------------------------------------------------------------------------------------
common
好用的终端工具推荐 MobaXterm
file file_name # 显示文件类型
telnet 10.73.20.5 3306 测试ip端口是否被监听
zip -r data.zip data/   # -r代表压缩文件夹
curl -i -X POST -H 'admin:test' -H "Content-Type:application/json" -d '{"room_id":5330380,"rp_id":"b22634cd1acdfa83"}' 'http://10.1.4.63:5678/room/talk'
zcat app.[0-9].log.gz|grep '1514806437'  # 查看app.0.log.gz到app.9.log.gz压缩文件的内容并过滤
watch -n 1 -d netstat -ant  # 每隔1s高亮显示网络链接数变化情况
iostat -x 1  # 实时查看磁盘IO使用情况
du -s * | sort -n | tail  # 列出当前目录里最大的10个文件
ps aux | sort -nk +4 | tail  #  列出头十个最耗内存的进程
tail -f file.log | sed '/^Finished: SUCCESS$/ q'  # 当file.log里出现Finished: SUCCESS时候就退出tail,用于实时监控并过滤log是否出现了某条记录
history | awk '{CMD[$2]++;count++;} END { for (a in CMD )print CMD[a] " " CMD[a]/count*100 "% " a }' | grep -v "./" | column -c3 -s " " -t | sort -nr | nl | head -n10  # 输出最常用的十条命令
uname -a     #  -n: 显示主机名 -r: 显示内核版本 -a: 显示所有信息
uptime    # 统计系统从启动到现在运行了多久
mv #移动文件(夹)or改文件(夹)名,不需用-r
cp -a #复制整个文件夹/目录,并保持属性不变,相当于cp -pdr
cd - #返回到上个目录
wc a.txt  #行数  单词数  字节数  文件名, ls | wc -l
last -n   # 显示最近n次用户登录信息
curl ifconfig.me # 查看服务器公网IP,还可以通过curl cip.cc,ifconfig等方式获取
chmod -R 777 /data2 # R代表递归下面所有目录,使用者为root或自己
chown -R root:ccktv /data2 # 改变文件所属的[用户]:[组信息]
ln [-s] 源 目标  # 建立硬链接文件, -s软链接文件(源文件必须写成绝对路径)
time find . -name "*.c"  # 执行命令并计算执行时间
mkdir -p project/{lib/ext,bin,src/com/bjhee/{web,dao,service},test}  # brace expansion语法,","前后不能有空格,在bash中生效
mkdir -p /1/2 # 创建目录树
grep -C 2 -v -n "^$" test.txt  # 匹配test文件中的非空行,C意思是显示匹配行的上下指定行数,v意思是反向查找,n意思是显示字符串在文件中出现的行号,E意思是正则模式匹配,特殊字符如[需要转意\[表示
sudo su ccktv  # 输入的密码是执行sudo命令的用户密码,环境变量会一起被切换
sudo -s ccktv  # 输入的密码是执行sudo命令的用户密码,不切换环境变量
firewall-cmd --zone=public --list-port  # centos查看开放的端口信息
bash -c 'TAG="test-k8s-$(date +%Y%m%d%H%M)"; git tag ${TAG}; git push origin tag ${TAG}' # 一次执行多条命令,引用变量TAG要使用${TAG}
------------------------------------------------------------------------------------------------------------------------
Ubuntu
launcher地址: /usr/share/applications/eclipse.desktop
apt镜像地址: /etc/apt/sources.list  
安装增强功能: mount -t vboxsf Share /media/sf_Share
安装Chrome: 注意不能以root身份运行,需要在/usr/share/applications/google-chrome.desktop中添加--no-sandbox
安装sublime: 
ctrl+shift+p -> Build:New Build System
{
  "shell_cmd":"/opt/miniconda3/bin/python3.6 -u \"$file\"",
  "selector":"source.python"
}
------------------------------------------------------------------------------------------------------------------------
dpkg -P elasticsearch #卸载软件,包括其配置文件
dpkg -i chrome.deb   #安装chrome.deb软件包,-i等价于--install
dpkg -l|grep google  #查看安装包名称
dpkg -L google-chrome-stable  #列出安装位置
dpkg -s google-chrome-stable  #查看包的详细信息
Package: google-chrome-stable
Status: install ok installed
Priority: optional
Section: web
Installed-Size: 233197
Maintainer: Chrome Linux Team <chromium-dev@chromium.org>
Architecture: amd64
Version: 59.0.3071.104-1
Provides: www-browser
Depends: gconf-service, libasound2 (>= 1.0.16), libatk1.0-0 (>= 1.12.4), libc6 (>= 2.15), libcairo2 (>= 1.6.0)
Pre-Depends: dpkg (>= 1.14.0)
Description: The web browser from Google.
------------------------------------------------------------------------------------------------------------------------
apt install <package> # 常见的如redis,mysql-server,vim等
apt remove <package>  # remove packages
apt purge <package>   # remove packages and configs
apt upgrade
------------------------------------------------------------------------------------------------------------------------
ufw enable   #开启防火墙
ufw disable  #关闭防火墙
ufw status
------------------------------------------------------------------------------------------------------------------------
#! /usr/bin/expect
spawn ssh -p 32200 ccktv@10.1.169.215
expect "*password:"
# 注意要加\r
send "ccktv@123\r"   
interact
------------------------------------------------------------------------------------------------------------------------
文件：（对root用户权限失效）
r(4)：可以查看文件内容（cat more等）
w(2)：可以修改文件内容（vi pico等），并不代表可以删除文件
x(1)：可以执行文件

目录：（对root用户权限失效。）
r(4)：可以列出目录内容（ls,前提是有x权限）
w(2)：可以在目录中创建删除文件（rm mkdir touch等，前提是有x权限）
x(1)：可以进入目录（cd）

cp既要有文件夹的可写权限，又要有文件的可读权限
某文件有w权限并不代表可以被删除，得看其所在目录是否有w权限
mv与rm只需要文件夹有可写权限即可（但前提是有x权限）

umask #显示新建文件or目录缺省权限
umask 027 #改变默认的掩码
so:
创建目录默认权限为755
缺省创建的文件不能授予x权限，其权限默认为644
sh -x shell.sh  #执行脚本并显示所有变量的值
sh -n shell.sh  #不执行脚本，只是检查语法，并返回错误

使用stat命令可以查看三时间值:如 stat filename

1.  mtime(modify time):最后一次修改文件或目录的时间
2.  ctime(chang time) :最后一次改变文件或目录属性的时间
如:更改该文件的目录。
3.  atime(access time)::最后一次访问/执行文件或目录的时间

对于文件:
当修改mtime时,ctime必须随着改变.因为文件大小等都属性；
有人说说atime也一定会改变，要想修改文件必须先访问；其实是不对的
不必访问文件就能修改其内容：如：#echo “This is a test !” >> /etc/issue,
issue文件内容会变，但并没有访问文件，所以atime并没有改变.

对于目录：
访问一个目录其atime改变，mtime ，ctime不变；
修改一个目录如在一个目录下touch一个文件，mtime与ctime会改变，atime不一定会变；

文件夹：
文件夹的 Access time，atime 是在读取文件或者执行文件时更改的
我们只cd进入一个目录然后cd ..不会引起atime的改变，但ls一下就不同了。

文件夹的 Modified time，mtime 是在文件夹中有文件的新建、删除才会改变
如果只是改变文件内容不会引起mtime的改变，换句话说如果ls -f <directory>的结果发生改变mtime就会被刷新。
这里可能有人要争论了：我进入dd这个文件夹vi了一个文件然后退出，
前后ls -f <directory>的结果没有改变但是文件夹的mtime发生改变了……
这点请主意vi命令在编辑文件时会在本文件夹下产生一 个".file.swp"临时文件，该文件随着vi的退出而被删除……
这就导致了mtime的改变 [Auxten:p]不信你可以用nano修改文件来试验）。

文件夹的 Change time，ctime 基本同文件的ctime，其体现的是inode的change time。

补充一点：mount -o noatime(mount -o remount,atime / 可以在线重新挂载根目录) 可以选择不记录文件的atime的改变，
这意味着当你创建了这个文件后这个文件的atime就定格了，除非你用touch或者touch -a强制刷新文件的atime。
这样在可以在一定程度上提升文件系统的读写性能，特别是网站这种系统中在fstab里面加上noatime是个好主意

#-------------------------------------------------------------------
#  使用: spider.sh [-r]开启/结束计划，无需其他任何配置。
#  第一次使用spider.sh前请先执行chmod 777 spider.sh。
#-------------------------------------------------------------------
set -ex   # e: 若指令传回值不等于0,则立即退出shell(默认继续执行后面命令); x:执行指令后,会先显示该指令及所下的参数
file='.task.sh'                #任务名
pro_dir=$(cd `dirname $0`;pwd) #工程目录
plan='0 10,15 * * *'           #计划时间
schedule='/var/spool/cron/root'
re_plan="${plan//\*/\*} `pwd`/${file}"  #替换将$plan下所有的*替换成\*

if [ $# == 0 ];then       #[]和=两边要有空格,不带参数时执行
    # service crond restart &>/dev/null && chkconfig --level 345 crond on
    # [ -d "${pro_dir}../../data/" ] ||  mkdir -p "${pro_dir}../../data/"
    echo 'source /etc/profile' > $file
    echo "cd ${pro_dir}" >> $file
    echo "for i in \``which scrapy` list\` ;do ">>$file
    echo "`which scrapy` crawl \$i">>$file
    echo 'done'>>$file
    chmod 777 $file
    grep "${re_plan}" $schedule &>/dev/null  ||
    echo "${plan} `pwd`/${file}" >> $schedule
    #屏蔽grep回显及$schedule可能不存在带来的错误
    echo '定时任务设置成功!'

elif [ $1 = '-r' ];then  #字符串用=判断
    rm -rf $file
    sed -i "\#${re_plan}#d" $schedule &>/dev/null  #d代表删除，默认以/作为分割符
    echo '已取消定时任务'

else
    echo -e '\nError !\nUse "spider.sh [-r]" instead !\n'  #-e显示转意字符
fi


#   注释
;   间隔各命令按顺序依次执行（dos下用&）
&&  当前一个指令执行成功时,执行后一个指令（与dos一致）
||  当前一个指令执行失败时,执行后一个指令（第一个成功则不执行第二个,与dos一致）
$   变量前需要加的变量值
!   逻辑运算中的"非"(not)
'   单引号,不具有变量置换功能
"   双引号,具有变量置换功能
`   将一个命令的输出作为另一个命令的参数
#-----------------------------------------------------
#
#  功能  : 定时自动爬取。
#  要求 ：系统已安装Crontab且工程(oil)必须放置在pro_dir目录下。
#  使用  : spider.sh [-r|crawl]开启/结束计划，无需其他任何配置。
#  说明  : 该脚本独立于工程，可放置在Linux任意目录;
#            变量pro_dir,plan可按需配置;
#            第一次使用spider.sh前请先执行chmod 777 spider.sh。
#  系统  : CentOS。
#  时间  : 2015-08-06
#-----------------------------------------------------
plan='*/10 * * * *'                                                      #计划时间，可配置
pro_dir='/usr/local/project_scrapy/OP/oil/'      #工程目录，可配置
schedule='/var/spool/cron/root'

case $1 in
'')                                                                                    #不带参数
service crond restart &>/dev/null &&
chkconfig --level 345 crond on
[ -d "${pro_dir}../../data/" ] || mkdir -p "${pro_dir}../../data/"
 grep "${plan//\*/\*} `pwd`/$0 crawl" $schedule &>/dev/null  ||
 #屏蔽grep回显及schedule可能不存在的提示,sed/grep用正则,so将$plan下所有*替换成\*
 echo "${plan} `pwd`/$0 crawl" >> $schedule
 echo '定时任务设置成功!'
 ;;
 '-r')
 sed -i "\#`pwd`/$0 crawl#d" $schedule &>/dev/null   #d代表删除，默认以/为分割符,匹配所有行
 echo '已取消定时任务'
 ;;
 'crawl')
 source /etc/profile    #导入环境变量，默认路径是/usr/bin:/bin
 cd $pro_dir            #* * * * * command，command可以包含空格，出现错误时会在/var/spool/mail/root生成日志
 for i in `/usr/local/bin/scrapy list`;do
 /usr/local/bin/scrapy crawl $i --nolog
 done
 ;;
 *)
 echo -e '\nError !\nUse "spider.sh [-r|crawl]" instead !\n'  #-e显示转意字符
 ;;
 esac


DOS常见命令
attrib——修改文件属性命令
1．功能：修改指定文件的属性。
2．类型：外部命令。
3．格式：attrib[文件名][r][—r][a][—a][h][—h][—s]
4．使用说明：
（1）选用r参数，将指定文件设为只读属性，使得该文件只能读取，无法写入数据或删除；选用—r参数，去除只读属性；
（2）选用a参数，将文件设置为档案属性；选用—a参数，去除档案属性；　
（3）选用h参数，将文件调协为隐含属性；选用—h参数，去隐含属性；
（4）选用s参数，将文件设置为系统属性；选用—s参数，去除系统属性；　
（5）选用/s参数，对当前目录下的所有子目录及作设置。
技巧：将文件属性设为+h +s系统就会理解为受保护的系统文件，默认情况下不予显示
试例：将F:\1下的所有文件设为隐藏属性attrib +h F:\1\* /s
attrib +h F:\1\* /s /d (连同1下的文件夹的属性都一起改变)

shutdown -s -t 7200 表示120分钟后自动关机

copy /b 1.jpg+2.rar 3.jpg  #内涵图制作
注意：
1、“/b”一定要有，代表二进制文件；
2、图片和压缩文件的位置不能对调；
3、要使用时，将文件格式后缀改为“rar”，然后解压；
4、有这种方法还可以将txt格式文件变成jpg格式的图片，只要把命令中的“(y).rar”改为“(y).txt”即可
5、其他格式之间的变换不能用此方法。

1、如何过滤出已知当前目录下ansheng中的所有一级目录(提示:不包含ansheng目录下面目录的子目录及隐藏目录，即只能是一级目录)?
方法1：ls显示长格式，然后再通过sed过滤出以dr开头的行并打印出来
1. [root@ansheng ~]# ls -l ./ansheng | sed -n /^dr/p
2. drwxr-xr-x 2 root root 4096 Apr 9 21:08 asgd
3. drwxr-xr-x 2 root root 4096 Apr 9 21:08 ext
4. drwxr-xr-x 2 root root 4096 Apr 9 21:08 ansheng
5. drwxr-xr-x 2 root root 4096 Apr 9 21:08 test
6. drwxr-xr-x 2 root root 4096 Apr 9 21:08 xings
7. [root@ansheng ~]# ls -lF ./ansheng | sed -n '/\/$/p' ---> 过滤出以/结尾的
8. drwxr-xr-x 2 root root 4096 Apr 9 21:08 asgd/
9. drwxr-xr-x 2 root root 4096 Apr 9 21:08 ext/
10. drwxr-xr-x 2 root root 4096 Apr 9 21:08 ansheng/
11. drwxr-xr-x 2 root root 4096 Apr 9 21:08 test/
12. drwxr-xr-x 2 root root 4096 Apr 9 21:08 xings/

13.已知如下命令及结果：
现在需要从文件中过滤出“ ansheng” 和“ 31333741” 字符串，请给出命令.
解答：
有逗号：I am ansheng, myqq is 31333741
1. [ansheng@ansheng ~]$ awk '{print $3" "$6}' ansheng|sed s/,/" "/g
2. anshengs 31333741
方法4：
1. [ansheng@ansheng ~]$ awk -F '[ ,]' '{print $3" "$6}' ansheng
2. anshengs 31333741
14、如何查看/etc/services 文件内容有多少行？
方法2：
1. [root@ansheng /]# cat -n /etc/services |tail -1
2.  10774 iqobject 48619/udp # iqobject
方法3：
1. [root@ansheng /]# sed -n '$=' /etc/services
2. 10774
15、过滤出/etc/services 文件包含 3306 或 1521 两数据库端口的行的内容。
解答：
1. [root@ansheng /]# grep -E "3306|1521" /etc/services
2. mysql 3306/tcp # MySQL
3. mysql 3306/udp # MySQL
4. ncube-lm 1521/tcp # nCube License Manager
5. ncube-lm 1521/udp # nCube License Manager
3、描述 linux shell 中单引号、双引号及不加引号的简单区别
单引号：
即将单引号内的内容原样输出，或者描述为单引号里面看到的是什么就会输出什么。
双引号：
把双引号内的内容输出出来；如果内容中有命令、变量等，会先把变量、命令解析出结果，然后在输出最终内容来。
不加引号：
不会将含有空格的字符串视为一个整体输出, 如果内容中有命令、变量等，会先把变量、命令解析出结果，然后在输出最终内容来，如果字符串中带有空格等特殊字符，则不能完整的输出，需要改加双引号，一般连续的字符串，数字，路径等可以用。
5、描述 linux 下文件删除的原理
当一个文件的I_link=0且没有进程占用的时候，这个文件就被删除了，还有一种情况就是被进程占用的情况下，当这个文件的I_link和I_count同时为0的时候这个文件才会被真正的删除。
6、如何取得/ansheng 文件的权限对应的数字内容，如-rw-r–r– 为 644， 要求使用命令取得644 这样的数字。
1. [root@ansheng ~]# stat /ansheng |awk -F "[(/]" 'NR==4{print $2}'
2. 0644
7、linux下通过 mkdir 命令创建一个新目录/ansheng/ett，它的硬链接数是多少，为什么？
解答：
1. [root@ansheng ~]# mkdir /ansheng/ett -p
2. [root@ansheng ~]# ll -d /ansheng/ett/
3. drwxr-xr-x. 2 root root 4096 Jan 11 06:02 /ansheng/ett/
它的链接数是2，本身算一个链接，ett目录下的.为ett目录的又一个链接，所以链接数为2
1. [root@ansheng ansheng]# ll -i
2. total 4
3. 1046536 drwxr-xr-x. 2 root root 4096 Jan 11 06:02 ett
4. [root@ansheng ansheng]# ll -di ett/.
5. 1046536 drwxr-xr-x. 2 root root 4096 Jan 11 06:02 ett/.
8、请执行命令取出 linux 中 eth0 的 IP 地址(请用 cut，有能力者也可分别用 awk,sed 命令答)。
解答：
cut方法1：
1. [root@ansheng ~]# ifconfig eth0|sed -n '2p'|cut -d ":" -f2|cut -d " " -f1
2. 192.168.20.130
awk方法2：
1. [root@ansheng ~]# ifconfig eth0|awk 'NR==2'|awk -F ":" '{print $2}'|awk '{print $1}'
2. 192.168.20.130
Awk多分隔符方法3：
1. [root@ansheng ~]# ifconfig eth0|awk 'NR==2'|awk -F "[: ]+" '{print $4}'
2. 192.168.20.130
Sed方法4：
1. [root@ansheng ~]# ifconfig eth0|sed -n '/inet addr/p'|sed -r 's#^.*ddr:(.*)Bc.*$#\1#g'
2. 192.168.20.130
3. [root@ansheng ~]# ifconfig eth0|sed -n '/inet addr/p'|sed 's#^.*ddr:##g'|sed 's#B.*$##g'
4. 192.168.20.130
10、查找当前目录下所有文件，并把文件中的 www.ansheng.me 字符串替换成 www.abc.cc
解答：
1. [root@ansheng ~]# find ./ -type f|xargs sed -i 's#www\.ansheng\.me#www\.abc\.cc#g'


1. 删除Windows字符文件每行结尾的”^M”
2. $ find . -name "*.c" | xargs sed -i -e 's/^M$//'
3. Windows上换行符是”\r\n”，Unix/Linux上是”\n”。所以Windows上的文件在Linux下打开时，每行结尾会显示一个特殊字符”^M”。该命令会将当前目录下所有”.c”文件的每行结尾特殊字符去掉。注：在终端上输入”^M”的方法是先按”Ctrl+V”再按”Ctrl+M”。
另外，如果你在vim编辑器中要删除”^M”，你可以在命令模式下输入：
4. :%s/^M$//g
5. 批量修改后缀名
    * 修改当前目录包括子目录下所有的文件
    * $ find . -name "*.c" -exec echo "mv {} {}" \; | sed -e 's/\.c$/\.cpp/' | sh
    * 将当前目录及其子目录下所有”.c”文件后缀名改为”.cpp”。
    * 只修改当前目录，不包括子目录，命令可以简化为
    * $ rename 's/\.c$/\.cpp/' *.c
    * 把所有文件名改为大写
    * $ rename 'y/a-z/A-Z/' *
    * 批量修改文件名模式
    * $ rename 's/pre_\d{2}(\d{3})\.c$/post_$1\.cpp/' *.c
    * 这条命令会将所有类似于”pre_00123.c”的文件名改为”post_123.cpp”。
1. 删除符合某个条件以外的所有文件
2. $ rm -v !(*.iso|*.zip)

