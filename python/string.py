首字母变大写:capitalize(self)
name="ansheng"
name.capitalize()   # 'Ansheng'

内容居中,width:字符串的总宽度;fillchar:填充字符,默认填充字符为空格:center(self, width, fillchar=None)
string="hello word"
# 如果设置字符串的总产都为11，那么减去字符串长度10还剩下一个位置，这个位置就会被*所占用
string.center(11,"*") #'*hello word'
# 是从左到右开始填充
string.center(12,"*") #'*hello word*'

统计字符串里某个字符出现的次数,可选参数为在字符串搜索的开始与结束位置:count(self, sub, start=None, end=None)
string="hello word"
# 默认搜索出来的"l"是出现过两次的
string.count("l")  #2
# 如果指定从第三个位置开始搜索，搜索到第六个位置，"l"则出现过一次
string.count("l",3,6) #1

检测字符串中是否包含子字符串str,如果包含子字符串返回开始的索引值,否则返回-1: find(self, sub, start=None, end=None)
string="hello word"
# 返回`o`在当前字符串中的位置，如果找到第一个`o`之后就不会再继续往下面寻找了
string.find("o") #4
# 从第五个位置开始搜索，返回`o`所在的位置
string.find("o",5) #7

检测字符串是否由字母和数字组成,如果string至少有一个字符并且所有字符都是字母或数字则返回True,否则返回False：isalnum(self)
# 如果存在数字或字母就返回`True`，否则返回`False`
"hes2323".isalnum() #True
# 中间有空格返回的就是False了
"hello word".isalnum() #False

检测字符串是否只由字母组成:isalpha(self)
检测字符串是否只由数字组成:isdigit(self)
检测字符串是否只由小写字母组成:islower(self)
检测字符串是否只由空格组成:isspace(self)
检测字符串中所有的字母是否都为大写:isupper(self)

检测字符串中所有的单词拼写首字母是否为大写,且其他字母为小写:istitle(self)
# 如果变量的内容首字母是大写并且其他字母为小写，那么就返回True,否则会返回False
string="Hello Word"
string.istitle() #True
string="Hello word"
string.istitle() #False

返回一个原字符串左对齐,并使用空格填充至指定长度的新字符串.如果指定的长度小于原字符串的长度则返回原字符串:ljust(self, width, fillchar=None)
string="helo word"
# 定义的长度减去字符串的长度,剩下的就开始填充
string.ljust(15,'*') #'helo word******'

转换字符串中所有大写字符为小写:lower/upper(self)  
截掉字符串左边的空格或指定字符:lstrip(self, chars=None)
把字符串中的old(旧字符串)替换成new(新字符串),如果指定第三个参数max,则替换不超过max次:replace(self, old, new, count=None)
string="www.ansheng.me"
string.rsplit(".",1) #['www.ansheng', 'me']
string.rsplit(".",2) #['www', 'ansheng', 'me']

判断字符串是否以指定后缀结尾,如果以指定后缀结尾返回True,否则返回False:endswith(self, suffix, start=None, end=None)
string="hello word"
# 判断字符串中是否已d结尾,如果是则返回True
string.endswith("d") #True
# 判断字符串中是否已t结尾,不是则返回False
string.endswith("t") #False
# 制定搜索的位置,实则就是从字符串位置1到7来进行判断,如果第七个位置是d则返回True,否则返回False
string.endswith("d",1,7) #False

检查字符串是否是以指定子字符串开头,如果是则返回True,否则返回False.如果参数beg和end指定值,则在指定范围内检查:startswith(self, prefix, start=None, end=None)
tring="www.ansheng.me"
string.startswith("www") #True
string.startswith("www",3) #False
