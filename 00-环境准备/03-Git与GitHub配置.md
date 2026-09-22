# 03 Git 与 GitHub 配置

## 学习目标

- 在两套环境（Windows / WSL）里分别配置 Git 身份
- 生成 SSH Key 并接入 GitHub，实现免密推送
- 规划好「仓库放哪、数据放哪」
- 理解 Windows 与 Linux 混用仓库时的换行符问题

## 前置知识

- 完成 01、02
- 有 GitHub 账号（没有就注册：https://github.com/signup）

## 建议用时

半天

## 1. 现状

- Windows 已装 Git 2.55.0（`git --version` 有输出）；
- WSL Ubuntu 在 01 中已执行 `apt install git`，但还没有配置身份。

## 2. 安装与身份配置（两套环境都要做）

WSL（Ubuntu 终端）：

```bash
sudo apt install -y git
git config --global user.name "你的名字"
git config --global user.email "2500011544@stu.pku.edu.cn"
git config --global init.defaultBranch main
git config --global core.autocrlf input
git config --global pull.rebase false
git config --global alias.st status
git config --global alias.lg "log --oneline --graph --decorate --all"
```

Windows（PowerShell）：

```powershell
git config --global user.name "你的名字"
git config --global user.email "2500011544@stu.pku.edu.cn"
git config --global init.defaultBranch main
git config --global core.autocrlf input
```

查看配置：

```bash
git config --global --list
```

说明：两边配置互不影响，名字/邮箱保持一致即可（邮箱最好与 GitHub 注册邮箱一致，这样提交记录才会关联到你的账号）。

## 3. SSH Key（在 WSL 内生成）

```bash
ssh-keygen -t ed25519 -C "2500011544@stu.pku.edu.cn"
# 一路回车：默认保存到 ~/.ssh/id_ed25519，可设置 passphrase（也可留空）
cat ~/.ssh/id_ed25519.pub
```

复制输出的整行内容（以 `ssh-ed25519` 开头）→ GitHub → 头像 → `Settings` → `SSH and GPG keys` → `New SSH key` → 粘贴保存。

测试：

```bash
ssh -T git@github.com
# 首次会问 yes/no，输入 yes
# 成功显示：Hi <用户名>! You've successfully authenticated...
```

Windows 侧如也想用 SSH，可在 PowerShell 里重复 `ssh-keygen` 生成第二把 key 并添加到 GitHub。

## 4. 仓库位置策略

| 位置               | 路径                                  | 适合                                                |
| ------------------ | ------------------------------------- | --------------------------------------------------- |
| WSL 家目录（推荐） | `~/projects/xxx`                    | 日常代码：ext4 性能好，权限、符号链接正常           |
| Windows D 盘       | `/mnt/d/A王晨暄/...`                | 已有仓库（如本仓库）、需要 Windows 侧直接访问的资料 |
| Windows 侧访问 WSL | `\\wsl$\Ubuntu-24.04\home\<用户名>` | 备份、查看                                          |

`/mnt/d` 的限制：批量小文件操作慢；`chmod` 不生效；换行符容易混乱。**大项目请放 `~/projects`。**

## 5. 已有仓库怎么办（本仓库位于 `D:\A王晨暄\PythonLearning`）

- 继续在 Windows 侧提交：用现在的 Git 即可；
- 在 WSL 里操作：直接 `cd "/mnt/d/A王晨暄/PythonLearning"`（能被识别为仓库），或克隆到 `~/projects/PythonLearning`；
- 建议：学习资料（本仓库）留在 D 盘；**从阶段 01 开始的项目代码独立建仓到 `~/projects` 并推送到 GitHub**。

## 6. .gitignore 与换行符

Python 通用最小 `.gitignore`：

```gitignore
__pycache__/
*.pyc
.venv/
.vscode/
*.log
*.h5
*.sqlite
data/
```

换行符：WSL 侧 `core.autocrlf input`；多设备协作时再加 `.gitattributes`：

```gitattributes
* text=auto eol=lf
*.png binary
```

## 7. 自测清单

- [X] 两套环境 `git config --global --list` 都有正确身份
- [X] `ssh -T git@github.com` 成功
- [X] 能说清 `~/projects` 与 `/mnt/d` 的取舍
- [X] 知道 `.gitignore` 该写什么（虚拟环境、缓存、数据、日志）

## 参考资料

- Pro Git 中文版 https://git-scm.com/book/zh/v2
- GitHub SSH 配置文档 https://docs.github.com/en/authentication/connecting-to-github-with-ssh
