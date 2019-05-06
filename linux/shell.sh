环境变量(~/.bashrc作用于当前用户,/etc/profile作用于所有用户,写错后可能导致系统登不进去)
REDIS=/root/redis/bin
PYCHARM=/root/pycharm/bin
CONDA=/root/miniconda3/bin
export PATH=$PATH:$REDIS:$PYCHARM:$CONDA
export PYSPARK_PYTHON=/usr/local/bin/python3

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

alias #列出所有别名
alias avatar='ls -al /home' #给命令起别名(命令带参数时要加引号)
unalias [-a][别名] #删除别名,-a代表全部

kill
kill -9 pid  #强行关闭进程
kill -1 pid  #重启进程(重新读取配置,也可写为kill -HUP)
pkill httpd  #杀掉进程及其子进程 

init [0~6] #切换运行级别,必须是root用户
0: 系统关机
1: 单用户状态(用于维护)
2: 多用户模式,没有网络模式
3: 多用户模式,有网络模式
4: 系统未使用,留给用户自定义
5: 多用户模式&运行Xwindow
6: 重新启动

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

df & du & fdisk
df -h  # 查看磁盘使用状态
du -ah /home/user  # 显示所有文件大小信息(显示文件所占用的block大小,默认linux系统分区的block size是4k,即使文件只有1个字节也会占用4k)
du -sh /home/user  # 显示指定目录占有空间总和,不循环显示子目录
fdisk -l  # 查看磁盘分区信息

快捷键
ctrl C 终止当前命令
ctrl Z 挂起当前命令(暂停),jobs查看被挂起的进程
ctrl U 在提示符下,将整行命令删除
ctrl R 在history中搜索匹配命令
ctrl L 等价于clear
ctrl insert 复制
shift insert 粘贴
ctrl shift T   打开一个新的终端窗口

tar(打包压缩目录或文件,压缩后文件格式为*.tar.gz)
tar czf new.tar.gz old1 old2 #压缩文件夹生成new.tar.gz
tar xzf new.tar.gz #解压缩*.tar.gz格式的文件

ssh & scp
ssh -p port user@ip     远程连接
scp file1 user@ip:file2  上传or下载文件(file1 -> file2),文件夹需要在scp后加-r参数
-----------------------------------------------------------------------------------------------------------------------
ssh -C -f -N -g -L 12450:10.1.138.93:3306 coolshot@10.1.138.64     # 端口转发
该命令一般在跳板机(10.16.2.46)中执行
12450                                       # 跳板机中监听的端口
10.1.138.93:3306                            # 需要连接的mysql
coolshot@10.1.138.64                        # 最终连接mysql的主机
mysql -uu_coolshot -P12450 -h10.16.2.46 -p  # 外部连接mysql

ps & netstat
ps -ef | grep httpd # 查看httpd进程,第二列显示的是进程ID,可配合kill命令来关闭进程,dos下用tasklist | findstr httpd.exe
常用参数:
-ef: 标准格式输出,注意"-"不能省
aux: BSD格式输出
netstat -apn | grep 27017 # 查看27017端口使用情况(包括进程名,pid,port等信息),dos下用-abn
ps -efL: 查看线程,用LWP表示

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

nohup &
&: 后台运行,即使你用ctrl C,进程照样运行,因为对SIGINT信号免疫.但如果你直接关掉shell,进程同样消失.可见&对SIGHUP信号不免疫
nohup: 忽略SIGHUP信号,关闭shell,进程还是存在的.但如果你直接在shell中用Ctrl C,进程也会消失,因为对SIGINT信号不免疫
所以要让进程真正不受Ctrl C和shell关闭的影响,就同时用nohup processname &,nohup命令使标准输出和标准错误默认重定向到nohup.out文件
nohup java -jar monitor.jar > /home/java.log &

合并文件(uniq命令可以去除排序过的文件中的重复行,也就是说为了使uniq起作用,所有的重复行必须是相邻的)
取出两个文件行的并集(重复的行只保留一份),结果按行排序
cat file1 file2 | sort | uniq
取出两个文件行的交集(只留下同时存在于两个文件的行),结果按行排序
cat file1 file2 | sort | uniq -d
合并两个文件,删除行交集,留下其他的行,结果按行排序
cat file1 file2 | sort | uniq -u

date
[root@local ~]# date
Thu Dec 15 16:55:22 CST 2016
[root@local ~]# date -d yesterday +%Y-%m-%d
2016-12-14

common
watch -n 1 -d netstat -ant  # 每隔1s高亮显示网络链接数变化情况
pip show flask  # 查看库安装信息(路径等)
iostat -x 1  # 实时查看磁盘IO使用情况
du -s * | sort -n | tail  # 列出当前目录里最大的10个文件
ps aux | sort -nk +4 | tail  #  列出头十个最耗内存的进程
tail -f file.log | sed '/^Finished: SUCCESS$/ q'  # 当file.log里出现Finished: SUCCESS时候就退出tail,用于实时监控并过滤log是否出现了某条记录
history | awk '{CMD[$2]++;count++;} END { for (a in CMD )print CMD[a] " " CMD[a]/count*100 "% " a }' | grep -v "./" | column -c3 -s " " -t | sort -nr | nl | head -n10  # 输出最常用的十条命令
lsof -i:80   #  列出80端口现在运行什么程序
uname -a     #  -n: 显示主机名 -r: 显示内核版本 -a: 显示所有信息
touch file.txt    # 创建一个空文件
uptime    # 统计系统从启动到现在运行了多久
ls -lrt   # 最近访问的文件会出现在最下方
rz -y # 上传文件,y代表覆(默认不覆盖)
sz filename  # 下载文件
mv #移动文件(夹)or改文件(夹)名,不需用-r
cp -a #复制整个文件夹/目录,并保持属性不变,相当于cp -pdr
cd - #返回到上个目录
wc a.txt  #行数  单词数  字节数  文件名, ls | wc  
last -n   # 显示最近n次用户登录信息
如果shell脚本出现找不到路径或其他莫名错误,先用vim打开脚本,:set ff查看文件格式,如果是dos,应该为:set ff=unix
curl ifconfig.me # 查看服务器公网IP,还可以通过curl cip.cc,ifconfig等方式获取
chmod -R 777   /data2      # R代表递归下面所有目录
chown -R root:ccktv /data2 # 改变文件所属的[用户]:[组信息]
cat webapi.log | grep 'send_msg' | awk -F "\t" '{ if($8>5)  print $0  }'  # $0代表整行,$8代表分割后的第8列,$(NF-2)代表分割后的倒数第2列
ln 源 目标    # 建立硬链接文件
ln -s 源 目标 # 建立软链接文件(源文件必须写成绝对路径)
ls -l `which touch` # 命令替换,注意与管道的区别
time find . -name "*.c"  # 执行命令并计算执行时间
mkdir -p project/{lib/ext,bin,src/com/bjhee/{web,dao,service},test}
mkdir -p /1/2 # 创建目录树
grep -v "^$" test.txt  # 匹配test文件中的非空行,v意思是反向查找
sudo su - ccktv  # 输入的密码是执行sudo命令的用户密码
su – [root]	     # 用户切换命令(默认切换到root),输入的是root的密码,该命令是通过sudo权限进行角色切换

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

