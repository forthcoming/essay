lsof(list open files)
lsof file_name              # 查看哪些进程正在使用这个文件
lsof -t -u user_name        # 查看某个用户打开的文件,-t选项只返回PID
lsof | grep mysql           # 列出某个进程打开的文件
lsof -p 12,34               # 列出多个进程号打开的文件
lsof -i :3306               # 列出使用某个端口的进程信息
kill -9 `lsof -t -u daniel` # 杀死某个用户运行的所有进程
---------------------------------------------------------------------------------------------------------------------------------
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
find /mnt -name '*.conf' -exec rm -rf {} +      # 删除/mnt名称中带有.conf的文件,每条命令以+分隔,{}代表find的结果
如何删除形如"-a","a b"等文件?
touch -- -a "a b"
ls -i   
find -inum 节点数 -exec rm -rf {} +
---------------------------------------------------------------------------------------------------------------------------------
正则表达式 & 通配符
正则表达式: 用于文本内容字符串的搜索和替换
通配符: 用来匹配文件名
*      匹配任意多个字符
?      匹配任意单个字符
[...]  匹配括号内出现的任意一个字符
[!...] 不匹配括号内出现的任意一个字符
---------------------------------------------------------------------------------------------------------------------------------
Hard Link & Symbolic Link
默认不带参数情况下,ln命令创建的是硬链接
硬链接文件与源文件的inode节点号相同,他们是完全平等关系,是同一个文件,硬链接不占用源文件大小空间
软链接文件(可理解为快捷方式)的inode节点号与源文件不同,他们是两个不同的文件
不能对目录/跨文件系统创建硬链接,创建软链接则没有限制
删除软链接文件,对源文件及硬链接文件无任何影响
删除文件的硬链接文件,对源文件及软链接文件无任何影响
删除链接文件的原文件,对硬链接文件无影响,会导致其软链接失效(红底白字闪烁状)
同时删除原文件及其硬链接文件,整个文件才会被真正的删除
---------------------------------------------------------------------------------------------------------------------------------
`` & | & xargs & exec
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
---------------------------------------------------------------------------------------------------------------------------------
awk -F|-v 'BEGIN{ } // {comand1;comand2} END{ }' file
-F 定义列分隔符
-v 定义变量
' ' 引用代码块,awk执行语句必须包含在内
BEGIN{} 在对每一行进行处理之前,初始化代码,主要是引用全局变量,设置FS分隔符
{} 命令代码块,包含一条或多条命令,处理每一行时要执行的语句
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

计算所有的.conf和.aof文件总大小
ls -l *.conf *.aof | awk 'BEGIN{sum=0} {sum+=$5} END {print sum}'
69860

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
cat webapi.log | grep 'send_msg' | awk -F "\t" '{ if($8>5)  print $0  }' 
---------------------------------------------------------------------------------------------------------------------------------
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
---------------------------------------------------------------------------------------------------------------------------------                    
download & upload
ssh -p port user@ip     # 远程连接
scp file1 user@ip:file2 # 上传or下载文件(file1 -> file2),文件夹需要在scp后加-r参数
rz -y # 上传文件,y代表覆(默认不覆盖)
sz filename  # 下载文件
rsync -a 源文件 user@目标IP:路径 # -a表示递归方式传输文件,并保持所有文件属性,rsync默认只对差异文件做更新,也可以全量(优于scp),使用时需要目标服务器开启sshd
1. apt install openssh-server
2. /etc/init.d/ssh start
---------------------------------------------------------------------------------------------------------------------------------
pip
pip show flask  # 查看库安装信息(路径等)
pip freeze > requirements.txt
pip install -r requirements.txt
pip install --proxy=http://127.0.0.1:8118 scrapy==1.4.0
pip install --proxy=socks5://127.0.0.1:1080 scrapy==1.4.0
pip uninstall
---------------------------------------------------------------------------------------------------------------------------------
conda
conda list  # 列出当前虚拟环境的所有安装包(包括conda和pip安装的包,这两个命令install作用差不多)
conda create -n scrapy # 创建虚拟环境
conda env list
conda activate scrapy #激活
# 进入到虚拟环境后,如果该环境没有python2,pip等之类包的话会自动识别到base虚拟环境中的包
# 建议进入到新的虚拟环境后首先conda install python=2.7,或者直接在本环境下通过conda install安装python包
conda deactivate #停用
conda install -n scrapy python=3.6  # 也可以先进到对应虚拟环境,再conda install python=3.6
conda install /root/Desktop/软件名
conda remove -n scrapy --all
---------------------------------------------------------------------------------------------------------------------------------
环境变量(~/.bashrc作用于当前用户,/etc/profile作用于所有用户,写错后可能导致系统登不进去)
REDIS=/root/redis/bin
PYCHARM=/root/pycharm/bin
CONDA=/root/miniconda3/bin
export PATH=$PATH:$REDIS:$PYCHARM:$CONDA
export PYSPARK_PYTHON=/usr/local/bin/python3
---------------------------------------------------------------------------------------------------------------------------------
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
---------------------------------------------------------------------------------------------------------------------------------
alias #列出所有别名
alias avatar='ls -al /home' #给命令起别名(命令带参数时要加引号)
unalias [-a][别名] #删除别名,-a代表全部
---------------------------------------------------------------------------------------------------------------------------------
kill
kill -9 pid  #强行关闭进程
kill -1 pid  #重启进程(重新读取配置,也可写为kill -HUP)
pkill httpd  #杀掉进程及其子进程 
---------------------------------------------------------------------------------------------------------------------------------
init [0~6] #切换运行级别,必须是root用户
0: 系统关机
1: 单用户状态(用于维护)
2: 多用户模式,没有网络模式
3: 多用户模式,有网络模式
4: 系统未使用,留给用户自定义
5: 多用户模式&运行Xwindow
6: 重新启动
---------------------------------------------------------------------------------------------------------------------------------
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
---------------------------------------------------------------------------------------------------------------------------------
df & du & fdisk
df -h  # 查看磁盘使用状态
du -ah /home/user  # 显示所有文件大小信息(显示文件所占用的block大小,默认linux系统分区的block size是4k,即使文件只有1个字节也会占用4k)
du -sh /home/user  # 显示指定目录占有空间总和,不循环显示子目录
fdisk -l  # 查看磁盘分区信息
---------------------------------------------------------------------------------------------------------------------------------
快捷键
ctrl C 终止当前命令
ctrl Z 挂起当前命令(暂停),jobs查看被挂起的进程
ctrl U 在提示符下,将整行命令删除
ctrl R 在history中搜索匹配命令
ctrl L 等价于clear
ctrl insert 复制
shift insert 粘贴
ctrl shift T   打开一个新的终端窗口
---------------------------------------------------------------------------------------------------------------------------------
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
---------------------------------------------------------------------------------------------------------------------------------
ps & netstat
ps -ef | grep httpd # 查看httpd进程,第二列显示的是进程ID,可配合kill命令来关闭进程,dos下用tasklist | findstr httpd.exe
常用参数:
-ef: 标准格式输出,注意"-"不能省
aux: BSD格式输出
netstat -apn | grep 27017 # 查看27017端口使用情况(包括进程名,pid,port等信息),dos下用-abn
ps -efL|grep pid # 查看某个进程下的所有线程,用LWP表示
pstree -p pid    # 查看某个进程下的所有线程
top -p pid       # 然后按H,查看某个进程下的所有线程

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
---------------------------------------------------------------------------------------------------------------------------------
nohup &
&: 后台运行,即使你用ctrl C,进程照样运行,因为对SIGINT信号免疫.但如果你直接关掉shell,进程同样消失.可见&对SIGHUP信号不免疫
nohup: 忽略SIGHUP信号,关闭shell,进程还是存在的.但如果你直接在shell中用Ctrl C,进程也会消失,因为对SIGINT信号不免疫
所以要让进程真正不受Ctrl C和shell关闭的影响,就同时用nohup processname &,nohup命令使标准输出和标准错误默认重定向到nohup.out文件
nohup java -jar monitor.jar > /home/java.log &
---------------------------------------------------------------------------------------------------------------------------------
合并文件(uniq命令可以去除排序过的文件中的重复行,也就是说为了使uniq起作用,所有的重复行必须是相邻的)
取出两个文件行的并集(重复的行只保留一份),结果按行排序
cat file1 file2 | sort | uniq
取出两个文件行的交集(只留下同时存在于两个文件的行),结果按行排序
cat file1 file2 | sort | uniq -d
合并两个文件,删除行交集,留下其他的行,结果按行排序
cat file1 file2 | sort | uniq -u
---------------------------------------------------------------------------------------------------------------------------------
date
[root@local ~]# date
Thu Dec 15 16:55:22 CST 2016
[root@local ~]# date -d yesterday +%Y-%m-%d
2016-12-14
---------------------------------------------------------------------------------------------------------------------------------
common
zcat app.[0-9].log.gz|grep '1514806437'  # 查看app.0.log.gz到app.9.log.gz压缩文件的内容并过滤
watch -n 1 -d netstat -ant  # 每隔1s高亮显示网络链接数变化情况
iostat -x 1  # 实时查看磁盘IO使用情况
du -s * | sort -n | tail  # 列出当前目录里最大的10个文件
ps aux | sort -nk +4 | tail  #  列出头十个最耗内存的进程
tail -f file.log | sed '/^Finished: SUCCESS$/ q'  # 当file.log里出现Finished: SUCCESS时候就退出tail,用于实时监控并过滤log是否出现了某条记录
history | awk '{CMD[$2]++;count++;} END { for (a in CMD )print CMD[a] " " CMD[a]/count*100 "% " a }' | grep -v "./" | column -c3 -s " " -t | sort -nr | nl | head -n10  # 输出最常用的十条命令
uname -a     #  -n: 显示主机名 -r: 显示内核版本 -a: 显示所有信息
touch file.txt    # 创建一个空文件
uptime    # 统计系统从启动到现在运行了多久
ls -lrt   # 最近访问的文件会出现在最下方
mv #移动文件(夹)or改文件(夹)名,不需用-r
cp -a #复制整个文件夹/目录,并保持属性不变,相当于cp -pdr
cd - #返回到上个目录
wc a.txt  #行数  单词数  字节数  文件名, ls | wc -l
last -n   # 显示最近n次用户登录信息
如果shell脚本出现找不到路径或其他莫名错误,先用vim打开脚本,:set ff查看文件格式,如果是dos,应该为:set ff=unix
curl ifconfig.me # 查看服务器公网IP,还可以通过curl cip.cc,ifconfig等方式获取
chmod -R 777   /data2      # R代表递归下面所有目录
chown -R root:ccktv /data2 # 改变文件所属的[用户]:[组信息]
ln 源 目标    # 建立硬链接文件
ln -s 源 目标 # 建立软链接文件(源文件必须写成绝对路径)
ls -l `which touch` # 命令替换,注意与管道的区别
time find . -name "*.c"  # 执行命令并计算执行时间
mkdir -p project/{lib/ext,bin,src/com/bjhee/{web,dao,service},test}
mkdir -p /1/2 # 创建目录树
grep -v -n "^$" test.txt  # 匹配test文件中的非空行,v意思是反向查找,n意思是显示字符串在文件中出现的行号
sudo su ccktv  # 输入的密码是执行sudo命令的用户密码,环境变量会一起被切换
sudo -s ccktv  # 输入的密码是执行sudo命令的用户密码,不切换环境变量
---------------------------------------------------------------------------------------------------------------------------------
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
---------------------------------------------------------------------------------------------------------------------------------
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
Depends: gconf-service, libasound2 (>= 1.0.16), libatk1.0-0 (>= 1.12.4), libc6 (>= 2.15), libcairo2 (>= 1.6.0), libcups2 (>= 1.4.0), libdbus-1-3 (>= 1.1.4), libexpat1 (>= 2.0.1), libfontconfig1 (>= 2.11), libfreetype6 (>= 2.3.9), libgcc1 (>= 1:4.1.1), libgconf-2-4 (>= 3.2.5), libgdk-pixbuf2.0-0 (>= 2.22.0), libglib2.0-0 (>= 2.28.0), libgtk-3-0 (>= 3.3.16), libnspr4 (>= 2:4.9-2~), libpango-1.0-0 (>= 1.14.0), libpangocairo-1.0-0 (>= 1.14.0), libstdc++6 (>= 4.8.1), libx11-6 (>= 2:1.4.99.1), libx11-xcb1, libxcb1 (>= 1.6), libxcomposite1 (>= 1:0.3-1), libxcursor1 (>> 1.1.2), libxdamage1 (>= 1:1.1), libxext6, libxfixes3, libxi6 (>= 2:1.2.99.4), libxrandr2 (>= 2:1.2.99.3), libxrender1, libxss1, libxtst6, ca-certificates, fonts-liberation, libappindicator1, libnss3 (>= 3.17.2), lsb-base (>= 4.1), xdg-utils (>= 1.0.2), wget
Pre-Depends: dpkg (>= 1.14.0)
Description: The web browser from Google.
--------------------------------------------------------------------------------------------------------------------------------
apt install <package>
apt remove <package>  #remove packages
apt purge <package>   #remove packages and configs
apt upgrade
--------------------------------------------------------------------------------------------------------------------------------
ufw enable   #开启防火墙
ufw disable  #关闭防火墙
ufw status

