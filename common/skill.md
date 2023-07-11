### Chrome
```
command + option + i   等同于windows的f12

" ("关键词")
把搜索词汇放在双引号中,代表完全匹配搜索,也就是说搜索出来的结果页面都是包含双引号中所出现的所有词汇,连顺序也是完全匹配的.
例如搜索 Joe Bloggs 时,搜索引擎会返回同时跟 Joe 和 Bloggs 相关的结果,而搜索 "Joe Bloggs" 时,搜索引擎只返回跟 "Joe Bloggs" 相关的结果.
百度和Google都是支持这个指令的.


- (关键词 -不需要的关键词)
减号代表搜索引擎显示不包括减号后面词汇的页面.使用这个指令时减号前面必须是空格,减号后面没有空格,要紧跟着需要排除的词.
Google和百度都支持这个指令.使用减号高级指令可以更加准确的找到需要的文件,尤其是某些词语有多重意义的时候.


site (site: 网站 关键词)
很多网站缺乏搜索功能,但你可以通过谷歌等搜索引擎对站内进行搜索.
在搜索引擎上输入 site:theguardian.com 和搜索关键字,搜索引擎会返回网站 theguardian.com 内和关键词相关的信息.
比如搜索"site:www.zhihu.com",出现的就是 www.zhihu.com 这个域名下面的所有页面,可以说这个高级指令是查询网站收入页面数量最直接的方法.


* (akat*i)
星号是常用的通配符,也可以使用在搜索引擎中.
比如在Google中搜索“ 搜索*擎”,其中*代表任何文字、出现的结果就不仅仅是包含“搜索引擎”的页面了.


intitle/inurl/intext (intitle: 关键词)
你只想找出所有和关键词相关的网页链接、网页主体(内容)和标题,这时就可以使用对应的限定词：inurl: 、intext 和 intitle.
例如在搜索引擎中输入 intitle: 评测 会得到所有和关键词 评测 相关的网页标题.
title是目前页面优化最重要的因素.无论是什么网站,基本都会把关键词放入title中.


filetype (filetype:pdf 关键词)
例如 filetype:pdf 视频教程,显示的是包含“视频教程”的所有PDF文件.
filetype指令可以用来搜索特定的资源,比如PDF电子书、Word文件等.Google和百度都是支持filetype


利用浏览器解码
中文的gbk(GB2312)编码
如果是中文的gbk(GB2312)编码,那么它的形式应该是一个汉字对应%xx%xx
比如http://www.baidu.com/baidu?tn=baidu&word=%D6%D0%B9%FA ,百度是使用GB2312编码的
其中前面的“%D6%D0”就对应中文汉字“中”字,后面的“%B9%FA”就对应中国汉字“国”字.
中文的UTF-8编码
如果是中文的UTF-8编码,那么它的形式应该是一个汉字对应%xx%xx%xx
比如http://www.icpoline.com/tag/%e7%bd%91%e6%b0%91,IcpOline使用的是UTF-8编码
这个网址中“%e7%bd%91”对应汉字“网”,“%e6%b0%91”对应中文汉字“民”.
利用百度进行URL编码解码
http://www.baidu.com/s?wd=%BA%BA%D7%D6
http://www.baidu.com/s?wd=%E6%B1%89%E5%AD%97


SafeSearch filters
https://www.google.com/preferences
SafeSearch can help you block inappropriate or explicit images from your Google Search results.
The SafeSearch filter isn’t 100% accurate, but it helps you avoid most violent and adult content.
解决办法:F12审查元素,将 <input value="on" name="safeui" type="hidden"> 的value值改成off即可,然后点右下角save按钮
```

### vim
```
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
:set nonu  取消行号(默认)
:set ic  搜索时忽略大小写
:set noic  严格区分大小写(默认)
:#   #代表数字,表示跳到第几行
注意:r可配合:!Command使用  如 :r !date
在/etc/vim/vimrc下对vim的修改对所有用户永久有效
在~/.vimrc下对vim的修改仅对当前用户永久有效
可以设置一些:set nu   :set ic
```

### Pycharm/Idea
```
option + command + L  格式化代码
Ctrl E        打开最近访问过的文件
Ctrl Shift E  打开最近编辑过的文件
Ctrl F        查找
Ctrl Shift F  全局查找
Ctrl R        replace
Ctrl Shift R  全局替换
Ctrl Z        Undo
Ctrl Shift Z  Redo
Ctrl Shift +  展开所有的代码块
Ctrl Shift -  收缩所有的代码块
F3            下一个高亮处
Shift F3      前一个高亮处
Ctrl Shift V  访问历史粘贴板
Ctrl Shift N  按文件名查找
Ctrl Alt L    格式化代码,可以对当前文件和整个包目录使用
Ctrl Alt O    优化导入的类,可以对当前文件和整个包目录使用
CTRL /        comment/uncomment
Alt F7        列出变量/函数在哪些地方被使用
Ctrl Shift F7 高亮某个变量,而且随着鼠标的移动高亮不会消失
右击选项卡标题区域 -> Split Vertically 即可同时展现多个窗口
连续按两下Shitf键可以搜索文件名/类名/方法名/目录名,搜索目录的技巧是在在关键字前面加斜杠
文件 -> locate history 可以查到误删文件
IDE前进后退键： settings -> Appearance & Behavior -> Menus and Toolbars -> Navigation Bar Toolbar -> Toolbar Run Actions -> +号(add action) -> back+forward
要ctrl + s保存代码（触发格式化）  file =》settings =》 file Watchers =》goimports 和 golangci-lint  # 不同项目需要单独设置
只有实现了go接口的所有方法,才算实现了接口,ide才会出现i标记
```

### Sublime
```
Shift + 鼠标右键   纵向选择
shift+↑ 向上选中多行
shift+↓ 向下选中多行
Shift+← 向左选中文本
Shift+→ 向右选中文本
Ctrl+Alt+↑ 向上添加多行光标,可同时编辑多行
Ctrl+Alt+↓ 向下添加多行光标,可同时编辑多行
Ctrl+J 合并选中的多行代码为一行.举个栗子:将多行格式的CSS属性合并为一行
Ctrl+/ 注释
Ctrl+k+u 转大写
Ctrl+k+l 转小写
Ctrl+F 打开底部搜索框,查找关键字(苹果电脑上 option + command + f)
Ctrl+shift+F 在文件夹内查找,与普通编辑器不同的地方是sublime允许添加多个文件夹进行查找
Ctrl+P 打开搜索框.举个栗子:1、输入当前项目中的文件名,快速搜索文件,2、输入@和关键字，查找文件中函数名,3、输入:和数字,跳转到文件中该行代码,4、输入#和关键字,查找变量名
Ctrl+G 打开搜索框,自动带:,输入数字跳转到该行代码.举个栗子:在页面代码比较长的文件中快速定位
Ctrl+R 打开搜索框,自动带@,输入关键字,查找文件中的函数名.举个栗子:在函数较多的页面快速查找某个函数
Ctrl+: 打开搜索框,自动带#,输入关键字,查找文件中的变量名、属性名等
Ctrl+Shift+P 打开命令框.场景栗子:打开命名框,输入关键字,调用sublime text或插件的功能,例如使用package安装插件
Alt+Shift+1 窗口分屏,恢复默认1屏(非小键盘的数字)
Alt+Shift+2 左右分屏-2列
Alt+Shift+3 左右分屏-3列
Alt+Shift+4 左右分屏-4列
Alt+Shift+5 等分4屏
Alt+Shift+8 垂直分屏-2屏
Alt+Shift+9 垂直分屏-3屏
```

### Notepad++
```
小写转换大写:Ctrl + shift + U
大写转换小写:Ctrl + U
视图 => 显示符号 => 显示空格与制表符
```

