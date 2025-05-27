#常见git指令




git下载
https://git-scm.com/downloads

初始化本地库
git init

远程库下载到本地库
git clone https://github.com/yuyuerer/Python.git

$ git clone -b <branch> <url>  # 将远程仓库的一个分支克隆到本地

查看本地库状态
git status

保存修改到本地库
git add README.md
或者 git add .
git commit -m "第一次修改readme"

推送到远程仓库
git remote -v
git push

分支
git branch
git branch -a
创建/切换分支
git checkout -b origin/dev
上传到指定分支
git push --set-upstream origin dev

修改后leader同步
git pull

日志
git log
git log --oneline

新建本地库上传到远程库
git status
git init
git add .
git commit -m "新建项目"
git remote add origin https://github.com/yuyuerer/git_test3.git
git branch -M main
git push -u origin main

-b dev

添加多用户
git config -h
git config --local user.name 'abc'
git config --local user.email 'abc@xxx.com'

从版本库中恢复文件
修改后：
1、未add                 
git status
git checkout a.txt

2、已add未commit
git status
git log
git checkout <commit id> a.txt

3、已add已commit
git status
git log
git checkout <commit id> a.txt

多用户修改后与库版本不一致
1、能自动合并的冲突
git pull
git push
 
2、需要手动合并的冲突
git push报错后
git status查看问题文件
git diff abc.txt  查看何处变动
git pull  变为合并中merging状态后 手动合并
git status
git diff abc.txt
git log
git add .
git commit -m "修改信息"  此时merging状态结束
git log
git push
