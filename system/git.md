```
git cherry-pick commitID  # 将某个分支的某次提交合并到当前分支
git remote -v  #显示需要读写远程仓库的简写与其对应的URL
origin    https://github.com/xxoome/Spiders.git (fetch)
origin    https://github.com/xxoome/Spiders.git (push)
vim .git/config 修改[remote "origin"]下面的url即可更改项目远程仓库路径
git diff              #比较工作区与暂存区
git diff --staged     #比较暂存区跟已提交的文件
git tag # 在控制台打印出当前仓库的所有tag
git tag name  # 创建轻量标签
git tag -d v1.0
git blame filename    #显示文件中每一行的作者,最后一次改动后进行的提交(commit)以及该次提交的时间戳
git init
git submodule add https://github.com/forthcoming/qrcode  # 需要在git项目目录执行,qrcode则会作为一个子模块，当你不在那个目录中时，Git并不会跟踪它的内容，而是将它看作子模块仓库中的某个具体的提交
git submodule foreach git pull   # 需要在git项目目录执行，更新公共库代码
git pull=git fetch+git merge
git stash list   # stash是本地的,不会通过git push命令上传到git server
git stash -m"test-stash"  # 将工作区和暂存区的文件缓存(不缓存未追踪文件)
git stash pop stash@{id}
git add -A
git log  #查看提交历史
git log  --oneline   #查看提交历史(一行显示)
git log -p  #查看提交历史,显示每次提交的内容差异
git log --oneline --decorate --graph --all  #输出你的提交历史、各个分支的指向以及项目的分支分叉情况
git reflog    #显示所有分支的所有操作包含提交历史,分支切换,pull,reset等操作,只要HEAD发生变化就会产生一条记录
git merge dev #合并dev分支到当前分支,优先使用Fast-forward模式(直接把当前分支指向dev的当前提交,如果当前分支和dev各自都有新提交,则无法使用该模式)
git merge --no-ff -m'--no-ff' dev #合并dev分支到当前分支,--no-ff表示禁用Fast-forward模式,合并后的历史有(合并的最后多了一条汇总)
git merge --abort  #取消某次合并
git revert commit_id  #逆操作之前的某个操作(历史记录仍然在,版本向前推进,有坑,需要重新构建分支才能再次合并)
git reset HEAD filename  #git add的反向操作,使其从Changes to be committed 到 Changes not staged for commit
git reset 47902f         #回到之前某次提交状态,保留工作目录,47902f之后的提交记录都会消失(能通过git reflog查看版本号再恢复)
git reset --hard 47902f  #回到之前某次提交状态,不保留工作目录(使用前先确认所有提交已推送到远程,否则这些提交将会丢失)
git reset -–hard HEAD^   #回到上次提交状态
git reset -–hard HEAD^^  #回到上上次提交状态,HEAD^^等价于HEAD~2
git push --force  #如果远程主机版本比本地更新,推送时会报错,可以使用--force强制推送,结果导致远程主机上更新的版本被覆盖(慎用)
git push [remote-name] [branch-name]   # 将master分支推送到origin服务器(git clone时通常会自动帮你设置好那两个名字)
git rebase -i 075bf67   # s合并历史提交记录,r更改历史提交说明,git reset + git push 也能实现提交历史合并
'''
pick d7acd15 222
pick 14de029 333
pick 172536b 444
# 顺序与通过git log命令看到的相反
# Rebase 075bf67..172536b onto 075bf67 (3 commands)
# Commands:
# p, pick <commit> = use commit
# r, reword <commit> = use commit, but edit the commit message
# s, squash <commit> = use commit, but meld into previous commit
# If you remove a line here THAT COMMIT WILL BE LOST.
'''
git clone -b gh-pages https://github.com/xxoome/collector.git  #克隆指定分支,默认为master分支
git clone -c http.proxy=socks5://127.0.0.1:1080 https://chromium.googlesource.com/chromium/tools/depot_tools
git branch    #列出本地分支,分支前的 * 字符代表当前所在分支(HEAD指针所指向的分支)
git branch -a #列出本地分支和远程分支(远程分支用红色表示)
git branch branchname   #在当前提交分支上创建分支
git branch -d iss53   #删除本地分支
git push origin --delete test #删除远程分支test 
git push --tags #一次推送所有本地新增的标签,标签对应的版本如果未push到origin,则会连同标签一起被push,其他分支和标签仍看不到该版本
git checkout branchname  #切换分支,对应的工作目录也切换了
git checkout -b iss53   #等价于git branch iss53 && git checkout iss53
git checkout -- <file>   #把file在工作区的修改全部撤销
1. file自动修改后,还没有放到暂存区,使用撤销修改就回到和版本库一模一样的状态
2. file已经放入暂存区了,接着又作了修改,撤销修改就回到添加暂存区后的状态
注意:—很重要,如果没有 — 的话,那么命令变成创建分支
git commit -m'comments' # 将暂存区(add提交)提交到本地版本库,同个文件add多次后再次被更改,则提交以最后一次add为准

删除README.md文件及其历史提交记录
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch README.md' --prune-empty --tag-name-filter cat -- --all
git push origin --force --all
```

```
[root@local github]# git status  # 可以标记冲突文件
# On branch master
#
# Initial commit
#
# Changes to be committed:
#   (use "git rm --cached <file>..." to unstage)
#
#    new file:   README
#
# Changes not staged for commit:
#   (use "git add <file>..." to update what will be committed)
#   (use "git checkout -- <file>..." to discard changes in working directory)
#
#    modified:   README

On branch master:
代表位于主分支上
Untracked files:
未跟踪的文件,意味着Git在之前的快照(提交)中没有这些文件;Git 不会自动将之纳入跟踪范围,使用git add开始跟踪一个文件
Changes to be committed:
说明是已暂存状态,已被跟踪
Changes not staged for commit:
跟踪文件的内容发生了变化,但还没有放到暂存区
注意: 
要暂存这次更新,需要运行git add命令
这是个多功能命令: 可以用它开始跟踪新文件,或者把已跟踪的文件放到暂存区,还能用于合并时把有冲突的文件标记为已解决状态等
将这个命令理解为"添加内容到下一次提交中"而不是"将一个文件添加到项目中"要更加合适
```

```
merge冲突时git用<<<<<<<,=======,>>>>>>>标记出不同分支的内容,解决冲突就是把git合并失败的文件手动编辑为我们希望的内容,再提交
merge时含有大量的未commit文件将使你在冲突中难以回退
建议使用stash命令将这些未commit文件暂存起来,并在解决冲突以后使用git stash pop把这些未commit文件还原出来

conda install git  #推荐,版本更新
github网页上按t即可按关键字查找文件,可以配置ssh免密码登录
fork + pull requests用以贡献开源代码

git配置文件如下,每一个级别覆盖上一级别的配置
/root/miniconda3/etc/gitconfig   git config --system读写该配置,作用域全局(yum安装对应/etc/gitconfig)
~/.gitconfig        git config --global读写该配置,只针对当前用户
.git/config         只针对当前仓库有效

.gitignore     让git忽略末某些文件无需纳入git的管理,也不希望它们总出现在未跟踪文件列表
# no .a files
*.a
# but do track lib.a, even though you're ignoring .a files above
!lib.a
# only ignore the TODO file in the current directory, not subdir/TODO
/TODO
# ignore all files in the build/ directory
build/
# ignore doc/notes.txt, but not doc/server/arch.txt
doc/*.txt
# ignore all .pdf files in the doc/ directory
doc/**/*.pdf
```
