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
pip show flask  # 查看库安装信息(路径等)
python -m pip install redis  # 在当前python环境下执行pip
pip -V # 获取当前pip绑定的python, pip 23.3.1 from D:/python/Lib/site-packages/pip (python 3.12)
pip list --format=freeze > requirements.txt
pip install -r requirements.txt
pip install --proxy=http://127.0.0.1:8118 scrapy==1.4.0
pip install --proxy=socks5://127.0.0.1:1080 scrapy==1.4.0
pip install redis -i http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com  # -i指定库的安装源
pip uninstall
pip config edit --editor vim  # 手动编辑配置文件

uv pip: 在uv管理下的虚拟环境中使用pip,可以提供诸如show,list等功能
uv python list: View available Python versions.
uv --directory /root run example.py
# 在uv管理的环境中运行命令, 会根据pyproject.toml文件自动安装缺少的依赖
# 创建子进程,然后执行/root/.venv/bin/python3 example.py, 因此无需source .venv/bin/activate切换环境,deactivate用于退出虚拟环境
uv init proj [--name audio]: 新建uv项目,name指定虚拟环境的名字,也可以时候更改pyproject.toml和uv.lock文件的name变量实现(需删除.venv再重建)
uv init --package -p 3.1.12: 将当前目录初始化为一个包(可用于上传至pypi),并使用python 3.1.12
uv add: Add a dependency to the project.类似于pip install <package> + 写入pyproject.toml,如果虚拟环境未创建,会先执行uv venv
uv remove: Remove a dependency from the project.
uv sync: Sync the project's dependencies with the environment.根据pyproject.toml安装或更新项目依赖
uv lock --upgrade && uv sync  # 更新版本
uv tree: View the dependency tree for the project.
uv build: Build the project into distribution archives.
uv publish: Publish the project to a package index.
uvx [--python 3.8] scrapy version: 临时安装Python包并执行包中的命令行工具,执行完毕后清理环境,等价于uv tool run
pyproject.toml: 项目的元数据和项目依赖,由开发者手动维护.
uv.lock: 所有直接依赖和它们的子依赖具体版本、下载地址和校验哈希等,保证项目环境的一致性（可复现部署）,自动生成.
.python-version: 控制项目虚拟环境的python版本,但必须满足pyproject.toml.requires-python要求
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
awk -F '|' 'BEGIN{ } // {comand1;comand2} END{ }' file
-F 定义列分隔符
' ' 引用代码块,awk执行语句必须包含在内,注意必须是单引号
BEGIN{} 在对每一行进行处理之前,初始化代码,主要是引用全局变量,设置FS分隔符,BEGIN和END必须大写
// 用来定义需要匹配的模式(字符串或正则表达式)
{} 命令代码块,包含一条或多条命令,处理每一行时要执行的语句,命令之间用;间隔
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
rsync -av --progress 源文件 user@目标IP:路径 # -a表示递归方式传输文件,并保持所有文件属性,rsync默认只对差异文件做更新,也可以全量(优于scp),使用时需要目标服务器开启sshd
1. apt install openssh-server
2. /etc/init.d/ssh start
------------------------------------------------------------------------------------------------------------------------
~/.bash_history  #记录用户的历史命令,当用户logout时才会将本次历史缓存写入其中,history -c与echo>~/.bash_history同时使用才能彻底删除历史记录
~/.profile # 作用于当前用户,该文件还可以定义别名
/etc/profile # 作用于所有用户,写错后可能导致系统登不进去,该文件还可以定义别名
/etc/hosts # 作用与windows的hosts文件相同

vim ~/.bashrc
REDIS=/root/redis/bin
PYCHARM=/root/pycharm/bin
CONDA=/root/miniconda3/bin
export PATH=$PATH:$REDIS:$PYCHARM:$CONDA

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
本地端口转发(从连接方主动出击)
ssh -fgNL 12450:10.1.138.93:3306 coolshot@10.1.138.64 # 跳板机(10.16.2.46)中执行
假设跳板机能访问10.1.138.64,10.1.138.64能访问10.1.138.93,但跳板机不能直接访问10.1.138.93,就需要本地端口转发
12450                                       # 跳板机中监听的端口
10.1.138.93:3306                            # mysql服务
coolshot@10.1.138.64                        # 作为跳板机的代理访问mysql服务
mysql -uu_coolshot -P12450 -h10.16.2.46 -p  # 连接mysql

远程端口转发(从被连接方主动出击)
ssh -fgNR 6000:1.1.1.1:6379 zh@2.2.2.2
假设2.2.2.2不能直接访问1.1.1.1,跳板机可以访问2.2.2.2和1.1.1.1,但跳板机不能被他俩访问
1. 如果1.1.1.1可以通过ssh访问2.2.2.2,直接在1.1.1.1上执行
2. 如果1.1.1.1不能访问2.2.2.2,可以在跳板机上执行
此时会在在2.2.2.2机器上监听6000端口,可以在2.2.2.2上通过6000端口访问1.1.1.1的redis服务
------------------------------------------------------------------------------------------------------------------------
ps & netstat
ps -ef | grep httpd # 查看httpd进程,第二列显示的是进程ID,可配合kill命令来关闭进程,dos下用tasklist | findstr httpd.exe
常用参数:
-ef: 标准格式输出,注意"-"不能省
aux: BSD格式输出
netstat -apn | grep 27017 # 查看27017端口使用情况(包括进程名,pid,port等信息),dos下用-abn
ps -efL|grep pid # 查看某个进程下的所有线程,用LWP表示
pstree -p pid    # 查看某个进程下的所有线程
ps -efj          # j获取进程的PPID, PID, PGID and SID(会话ID)

htop: 跟top类似,有颜色
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
top -p pid       # 然后按H,查看某个进程下的所有线程

top - 17:52:14 up 441 days, 51 min, 11 users,  load average: 2.04, 2.71, 3.02
任务: 1118 total,   1 running, 1115 sleeping,   1 stopped,   1 zombie
%Cpu(s):  4.2 us,  1.1 sy,  0.0 ni, 94.5 id,  0.0 wa,  0.0 hi,  0.1 si,  0.0 st
MiB Mem : 386344.5 total,  17770.6 free,  60546.0 used, 308028.0 buff/cache
MiB Swap:   2048.0 total,      0.0 free,   2048.0 used. 312097.3 avail Mem

 进程号 USER      PR  NI    VIRT    RES    SHR    %CPU  %MEM     TIME+ COMMAND
1740875 yiyangz+  20   0   59.9g  15.8g   6.7g S 150.8   4.2   2118:40 python
 817782 zhouguo+  20   0 1330528  19204   5364 S   8.9   0.0 131:53.93 redis-server
 821136 zhouguo+  20   0   49.1g   2.5g 565196 S   5.9   0.7  85:05.06 python3
   1678 root      20   0       0      0      0 S   5.6   0.0  13597:43 nv_queue

已知服务器有2个CPU,一共24个物理核心,48个逻辑核心
load average: 2.04, 2.71, 3.02
              ↑     ↑     ↑
           1分钟  5分钟  15分钟 的平均值
load average = 正在运行 + 等待运行的进程数平均值,必须对比核心数才有意义
load = 2.04 表示：过去1分钟内，平均有2.04个进程

%Cpu(s):  4.2 us, 94.5 id
%Cpu(s)指标代表所有cpu的平均值,s是summary的缩写
94.5 id : 48个核心的idle加起来 ÷ 48 ≈ 94.7%
4.2 us :  用户程序占用了4.2%

MiB Mem : 386344.5 total,  17770.6 free,  60546.0 used, 308028.0 buff/cache
MiB = Mebibyte,是二进制单位,1 MiB = 1024 × 1024 = 1,048,576 字节
total: 386GB物理内存总量
free: 17.4GB完全空闲、未被使用的物理内存
used: 59.1GB进程实际占用的物理内存
buff/cache: 300.8GB被内核用作缓冲区(buffer)和缓存(cache)的物理内存,这部分内存在系统需要时可以立即释放给应用程序使用
avail Mem: 304.8GB实际可用物理内存（约等于free + 可回收的 buff/cache）,他是MiB Mem的指标

VIRT : 虚拟内存（申请的）
RES : 实际物理内存（真正占用的）,最重要
SHR : 共享内存
S: 进程状态  R=>运行 S=>睡眠  Z=>僵尸进程
%CPU : CPU所有核使用率, 单核最大100%,150.8% = 用了约 1.5 个核心
%MEM : 进程使用物理内存百分比
TIME+ : 累计 CPU 时间 2118:40,2118 分钟 40 秒 = 35.3 小时,表示这个进程总共消耗了 35 小时的 CPU 计算时间（不是运行时长）
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
nvidia-smi  # 查看GPU信息
nvitop # 查看GPU信息,带颜色
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
sudo tcpdump -XvvennSs 0 -i eth0  -w ./http.cap
单引号: 完全禁止解释,所有内容都按原样保留,不会进行变量替换、命令替换、转义字符处理
双引号: 会进行变量替换,注意没有引号时,如果变量是空的或含空格,会产生参数拆分问题
;   间隔各命令按顺序依次执行（dos下用&）
&&  当前一个指令执行成功时,执行后一个指令（与dos一致）
||  当前一个指令执行失败时,执行后一个指令（第一个成功则不执行第二个,与dos一致）
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
# 文件以.sh为后缀,需要给可执行权限
#! /usr/bin/expect
spawn ssh -p 32200 ccktv@10.1.169.215
expect "*password:"
# 注意要加\r
send "ccktv@123\r"   
interact
-----------------------------------------------------------------------------------------------
