# 00 环境准备

目标：用 3~7 天搭好后面一年都要用的环境，并确认磁盘规划。本阶段没有任何编程知识，跟着做即可。

## 为什么是 WSL2 而不是传统虚拟机

| 对比项 | WSL2 | VMware/VirtualBox 完整虚拟机 |
| --- | --- | --- |
| 磁盘占用 | 基础 2~4 GB，动态增长 | 25~60 GB 起 |
| 内存 / 启动 | 与 Windows 共享、秒级启动 | 需预先分配，启动慢 |
| 文件互通 | 直接访问 `/mnt/c`、`/mnt/d` | 需共享文件夹或拖拽 |
| 与 VSCode 集成 | 原生（Remote-WSL） | 远程 SSH 或共享目录，体验差 |
| 与本路线 | 完全够用（Shell/Python/C/SSH） | 不需要 |

结论：跟随 `learning guide.md`，使用 **WSL2 + Ubuntu 24.04 LTS**。

## 文件顺序

1. [01-WSL2与Ubuntu安装.md](01-WSL2与Ubuntu安装.md) —— 安装、初始化、`.wslconfig` 资源分配、迁移到 D 盘（可选）。
2. [02-VSCode与WindowsTerminal配置.md](02-VSCode与WindowsTerminal配置.md) —— 把手写命令变成「编辑器 + 终端」工作流。
3. [03-Git与GitHub配置.md](03-Git与GitHub配置.md) —— 身份、SSH Key、仓库位置策略。
4. [04-磁盘评估与外接硬盘建议.md](04-磁盘评估与外接硬盘建议.md) —— 磁盘够不够、要不要买外接 SSD（结论：暂时不用）。

## Windows 侧 Python 现状（保留不动）

- 当前 PowerShell 里 `python` 指向 MSYS2 的 3.14.6；`py -0p` 还能看到 Store 版 3.12。两者都不用动。
- 本学习路线的 Python 一律指 **WSL Ubuntu 里的 `python3`**，与 Windows 侧互不干扰。

## 总验收清单

- [ ] `wsl -l -v` 显示 Ubuntu-24.04，VERSION 为 2
- [ ] Ubuntu 内 `lsb_release -a` 显示 24.04，`free -h` 内存约 12 GB，`nproc` 为 8
- [ ] Windows Terminal 默认配置为 Ubuntu
- [ ] VSCode 成功连接 WSL，能打开 `~/projects` 并在集成终端运行 Python
- [ ] `ssh -T git@github.com` 返回成功认证信息
- [ ] 读完 04 的磁盘评估，确认不需要外接硬盘
