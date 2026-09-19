# 03-Git版本控制

## 学习目标

- 理解为什么要用 Git：可回溯、可协作、可实验
- 理解工作区、暂存区、仓库三个区域
- 熟练使用 init / add / commit / status / log / diff
- 会安全地撤销修改：restore、reset --soft/--mixed、revert
- 会写 .gitignore，知道哪些文件不该进仓库
- 会创建分支、切换、合并，并独立解决一次冲突
- 会把本地仓库推送到 GitHub，会 clone 与 pull
- 会打 tag、查看历史

## 前置知识

- 01、02 课：会使用终端与基本命令
- 阶段 00 已安装 Git 并生成过 SSH 密钥（第四课会讲密钥原理，本课直接用）
- 有一个 GitHub 账号（没有就在官网注册）

## 建议用时

6~10 小时。重点是「把练习代码全部纳入版本控制」这件事本身。

## 正文

### 1. 为什么用 Git

想象三种常见事故：

- `analysis_v2_final_最终版_改.py` 堆了十几个版本，不知道哪个是对的
- 改错了一段代码，想回到上周五能跑的状态，但已经覆盖保存
- 想试试新方案，又怕弄坏现有代码，只能复制整个目录

Git 用一条「提交历史」解决这些问题：每次提交是一个完整快照，可以随时查看、对比、回退；
分支让你在不影响主线的情况下做实验；远程仓库让代码有备份、能多机同步。

常见错误：

- 把 Git 当成网盘，只在「写完一个完整功能」时才提交一次，历史失去意义
- 目录里同时放 `_备份`、`_v2` 副本和 Git 仓库，两套机制互相干扰（用了 Git 就不要手工复制版本）

### 2. 三个区域：工作区、暂存区、仓库

| 区域 | 含义 | 典型命令 |
| --- | --- | --- |
| 工作区 | 你正在编辑的文件 | 直接改文件 |
| 暂存区 | 准备写进下一次提交的内容清单 | `git add` |
| 仓库 | 一条条提交组成的历史 | `git commit` |

`git status` 会明确告诉你每个文件处在哪个状态：未跟踪（untracked）、已修改未暂存、
已暂存待提交（staged）。建议每执行两三步就看一次 `git status`。

常见错误：

- 改了文件直接 `git commit`，忘了先 `git add`，结果提交是空的
- 以为 `git add` 是「保存」，其实它只是把当前内容放进暂存区快照

### 3. 初次配置与创建仓库

```bash
git config --global user.name "Wang Chenxuan"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --global core.editor "nano"     # 需要写提交说明时用
git config --list                           # 查看当前配置

mkdir -p ~/projects/data-organizer
cd ~/projects/data-organizer
git init -b main
# 输出: Initialized empty Git repository in /home/you/projects/data-organizer/.git/
```

仓库根目录下会出现隐藏目录 `.git`，所有历史都保存在那里，不要手动改动它。

常见错误：

- 在家目录或整个 Windows 盘符根目录 `git init`，跟踪了几十万个无关文件
- user.name/user.email 不配置，提交时被拒或作者信息是默认值
- 需要区分机器时用 `--local` 覆盖全局配置

### 4. 日常流程：add / commit / status / log / diff

```bash
echo "# 数据整理工具" > README.md
git status                       # README.md 处于 untracked
git add README.md
git status                       # 变为 staged
git commit -m "添加项目说明"
git log --oneline                # 输出: 8f3a1c2 添加项目说明

# 继续修改并提交
echo "运行: python organizer.py --source data" >> README.md
git diff                         # 工作区 vs 暂存区：这次改了什么
git add README.md
git diff --staged                # 暂存区 vs 最近一次提交：将要提交什么
git commit -m "补充运行说明"
```

提交信息写法：第一行用动词开头的短句（「修复 CSV 空行解析」「添加按日期归档」），
一行说清「做了什么」；复杂改动在空行后补充原因。

```bash
git log --oneline --graph --all  # 分支与合并的图形化历史
git log --stat                   # 每次提交涉及哪些文件
git show 8f3a1c2                 # 某次提交的完整改动
```

常见错误：

- `git commit -m "改了一下"` 这类信息，三个月后自己都看不懂
- 用 `git add .` 前不 `git status`，把日志、数据、虚拟环境一起提交进去
- 提交了密钥、密码等敏感文件后再删除也没用，历史里还在，要尽早用 .gitignore 挡住

### 5. 撤销与恢复

先分清三种场景：

```bash
# 场景一：改了文件但还没 add，想回到上次提交的样子
git restore analysis.py

# 场景二：已经 add 进暂存区，想撤出但不丢改动
git restore --staged analysis.py      # 只撤出暂存区，文件内容不动

# 场景三：已经 commit，想撤销这次提交但保留改动
git reset --soft HEAD~1               # 提交消失，改动留在暂存区
git reset HEAD~1                      # 等价于 --mixed：改动留在工作区
```

`git reset --hard HEAD~1` 会连同改动一起丢弃，非常危险，除非确认不要这些改动，否则别用。

如果提交已经推送到远程（别人可能已经拉取），不要用 `reset` 改写历史，用 `revert`——
它创建一个「反向提交」来抵消原提交，历史保持完整：

```bash
git revert 8f3a1c2        # 生成一个新提交，内容与原提交相反
```

常见错误：

- `git restore` 与 `git restore --staged` 搞混：前者丢改动，后者只撤暂存
- 在共享分支上用 `reset --hard` 强推，把别人的提交冲掉
- 回退前不 `git status`、不 `git log --oneline` 确认自己在哪一步

### 6. .gitignore

项目根目录建 `.gitignore`，声明「不需要版本控制」的路径：

```gitignore
# 虚拟环境
.venv/
venv/

# Python 缓存
__pycache__/
*.pyc

# 日志与报告
*.log
report/

# 本地测试数据（体积大、可重新生成）
sample-data/
organized/

# 系统文件
.DS_Store
```

注意：`.gitignore` 只对「未跟踪」的文件生效。已经提交过的文件要先 `git rm --cached 文件` 再忽略。
被忽略的目录若想保留占位，可放一个空的 `.gitkeep` 并单独 `git add -f`。

常见错误：

- 在子目录写 `.gitignore` 却以为全局生效（它会作用于所在目录及子目录，作用范围要想清楚）
- 先 `git add .` 再写 .gitignore，导致大量文件已入库
- 把 `*.csv` 一刀切忽略，结果重要的小样本数据也进不了库；按目录忽略更精准

### 7. 分支与合并

分支让你在独立线上开发，不影响 main：

```bash
git switch -c feature/scan          # 创建并切换到新分支
# ... 编辑文件、git add、git commit ...
git switch main                     # 回到 main
git merge feature/scan              # 把 feature/scan 合并进 main

git branch                          # 查看本地分支，* 标记当前分支
git branch -d feature/scan          # 合并完成后删除已合并分支
```

两种合并结果：

- 快进（fast-forward）：main 没有新提交，main 直接指向 feature 的最新提交，历史是一条直线
- 三方合并：两边都有新提交，Git 自动生成一个合并提交；有冲突时要手动解决

常见错误：

- 长期不合并、分支越开越多，最后冲突巨大；小步提交、尽快合并
- 在 main 上直接做大改动然后又开分支，两边都改同一块代码
- 删除分支用 `-D` 强删，丢失未合并的工作

### 8. 冲突解决流程

制造一个冲突并解决它（强烈建议亲手做一次）：

```bash
# 在 main 上改动 README.md 第一行并提交
git switch main
# 在 feature 分支上也改同一行并提交
git switch -c feature/conflict-demo
# ... 改同一行，add 并 commit ...
git switch main
git merge feature/conflict-demo
# 输出: CONFLICT (content): Merge conflict in README.md
```

打开冲突文件，会看到标记：

```text
<<<<<<< HEAD
main 分支上的内容
=======
feature 分支上的内容
>>>>>>> feature/conflict-demo
```

解决步骤：

1. 编辑文件，保留想要的内容，删掉 `<<<<<<<`、`=======`、`>>>>>>>` 三行标记
2. `git add README.md`（告诉 Git 冲突已解决）
3. `git commit`（Git 会给出合并提交的默认信息，可修改）
4. 反悔就用 `git merge --abort` 回到合并前

常见错误：

- 把冲突标记原样提交进去，代码里出现 `<<<<<<<`
- 只删标记没想清楚留哪版内容
- 不沟通就强行覆盖队友的修改；冲突解决的本质是「决定代码最终长什么样」

### 9. 远程仓库：GitHub

先在 GitHub 网站新建一个空仓库（不要勾选初始化 README），然后：

```bash
git remote add origin git@github.com:你的用户名/data-organizer.git
git remote -v                        # 查看远程地址，应显示 git@github.com:...
git push -u origin main              # 首次推送并建立跟踪关系
git push                             # 之后直接 push
```

密钥登录在阶段 00 已配好，`git@github.com` 走 SSH 协议就不需要每次输密码。

```bash
# 另一台机器或另一个目录上同步代码
git clone git@github.com:你的用户名/data-organizer.git
git pull                             # 拉取远程更新并合并进本地
```

`pull` = `fetch`（下载）+ `merge`（合并）。推荐习惯：动手写代码前先 `git pull`。

常见错误：

- 远程仓库初始化时勾了 README，本地 push 被拒（提示 non-fast-forward）；先 `git pull --rebase` 或 `git pull` 再推
- 用 HTTPS 地址又没配凭据，每次都要输密码；换成 SSH 地址
- 在错误的分支上 push，把实验代码推成主线

### 10. tag 与查看历史

tag 给重要节点起名字，例如「交作业的版本」「跑出论文数据的版本」：

```bash
git tag -a v0.1.0 -m "实验数据整理 CLI MVP"
git tag                              # 列出所有 tag
git show v0.1.0                      # 查看 tag 指向的提交
git push origin v0.1.0               # 推送单个 tag
git push --tags                      # 推送所有 tag
```

更多查看历史的方式：

```bash
git log --oneline --since="2 weeks ago"
git log --author="Wang"
git log -p analysis.py               # 只看某文件的历史改动
git blame analysis.py                # 每一行最后是谁在哪个提交改的
```

常见错误：

- 改动源码后不更新 tag，导致 v0.1.0 指向的代码与手头不符；要么不改，要么打新 tag
- 用 tag 名当分支名（如 `git switch v0.1.0`），应理解 tag 是历史标记，不适合继续开发

## 练习

1. 基础：在 `~/projects/data-organizer` 初始化仓库，创建 README.md 与一个 Python 文件，
   分两次提交，每次提交后用 `git status`、`git log --oneline`、`git show` 检查。
   提示：`git init -b main`、`git add`、`git commit -m`。
   验收：`git log --oneline` 有两条且信息清晰，`git status` 显示 working tree clean。

2. gitignore：创建 `.venv` 目录、`__pycache__` 目录、`run.log` 文件，写 `.gitignore`
   让它们都不被跟踪；确认 `git status` 干净。
   提示：忽略目录加 `/` 结尾；已跟踪文件需先 `git rm --cached`。
   验收：新建这些文件后 `git status` 不显示它们。

3. 分支：新建 `feature/report` 分支，添加一个输出 CSV 报告的函数并提交；
   切回 main 合并；再故意在两边改同一行制造冲突并解决。
   提示：`git switch -c`、`git merge`、`git merge --abort` 可反悔。
   验收：`git log --oneline --graph` 能看到分支与合并结构，冲突标记已清理干净。

4. 撤销：练习三个场景：丢弃未暂存修改、撤出暂存区、撤销最近一次提交（保留改动），
   再用 `git revert` 撤销一个已推送过的提交。
   提示：`git restore`、`git restore --staged`、`git reset --soft HEAD~1`、`git revert <hash>`。
   验收：每一步都能用 `git status`/`git log` 解释当前状态。

5. 远程：在 GitHub 创建空仓库，推送本地 main，打 tag `v0.1.0` 并推送；
   然后在另一个目录 `git clone`，修改后 push，原目录 `git pull` 验证同步。
   提示：`git remote add origin`、`git push -u`、`git push origin v0.1.0`。
   验收：GitHub 网页上能看到提交、tag 与最新改动。

## 自测清单

- [ ] 我能用自己的话解释工作区、暂存区、仓库的区别
- [ ] 我提交前会先看 `git status` 和 `git diff --staged`
- [ ] 我的提交信息能让人看懂做了什么
- [ ] 我会用 `git restore` 与 `git restore --staged` 撤销，不乱用 `reset --hard`
- [ ] 我理解 `reset --soft/--mixed` 与 `revert` 的适用场景
- [ ] 我会写 .gitignore 并知道它为什么挡不住已提交文件
- [ ] 我会创建分支、合并、删除分支，做过一次冲突解决
- [ ] 我会配置 remote，用 SSH 推送到 GitHub，会 clone 与 pull
- [ ] 我会给重要版本打 tag 并推送
- [ ] 我能用 `git log` 的常用参数快速找到历史改动

## 参考资料

- Pro Git 官方中文书（免费）：https://git-scm.com/book/zh/v2
- Git 官方文档与参考：https://git-scm.com/doc
- GitHub 官方入门文档：https://docs.github.com/zh/get-started
