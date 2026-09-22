# 01 WSL2 与 Ubuntu 安装

## 学习目标

- 在 Windows 11 上装好 WSL2 + Ubuntu 24.04 LTS
- 会用 `wsl` 系列命令管理发行版（启动、关闭、查看、更新）
- 通过 `.wslconfig` 给 WSL 分配合适的 CPU / 内存
- 知道发行版磁盘文件在哪里、如何迁移到 D 盘

## 前置知识

- 会用管理员权限打开 PowerShell（开始菜单右键 → 终端(管理员)）
- 知道「虚拟化」是 BIOS 里的一个开关（本机已开启，无需操作）

## 建议用时

1~2 天（含下载时间）

## 1. WSL2 是什么

WSL2（Windows Subsystem for Linux 2）是 Windows 里的轻量 Linux 虚拟机：

- 跑的是**真实 Linux 内核**，Ubuntu 里的命令、编译、系统调用都是原生的；
- 通过 `/mnt/c`、`/mnt/d` 直接读写 Windows 磁盘；
- 磁盘是动态增长的虚拟磁盘文件（ext4.vhdx），用多少涨多少；
- 与 VSCode 深度集成（Remote-WSL），编辑器和终端都在 Linux 里；
- 学 Shell、Git、Python、C、SSH 完全够用，等价于一台小型 Linux 服务器。

## 2. 安装（管理员 PowerShell）

本机现状：Windows 11 build 26200，虚拟化已开启（`HypervisorPresent = True`），WSL 尚未安装。

```powershell
wsl --install -d Ubuntu-24.04
```

说明：

- 该命令会自动启用「适用于 Linux 的 Windows 子系统」与「虚拟机平台」两个功能，安装 WSL2 内核，并注册 Ubuntu 24.04；
- 如果提示需要重启：重启后再次运行同一命令；
- 如果下载失败（网络原因），改用：

```powershell
wsl --install --no-distribution
```

然后从 Microsoft Store 搜索 `Ubuntu 24.04` 安装。

- 如果系统提示功能未启用，可以手动启用后重启：

```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

## 3. 首次启动与初始化

从开始菜单打开 Ubuntu 24.04（或在终端运行 `wsl`），等它完成初始化后：

- 输入 UNIX 用户名：建议全小写英文，如 `bob`（不要中文、不要空格）；
- 输入密码：**输入时不显示**，输两遍。这是 Linux 里的 `sudo` 密码，请记住。

验证：

```bash
whoami           # 显示 bob
lsb_release -a   # 显示 Ubuntu 24.04
```

注意：这个 Linux 用户与 Windows 账户没有关系，只是同名或不同名都可以。

## 4. 更新与基础工具

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential git curl wget tmux htop unzip
```

- `build-essential`：gcc、make 等编译工具（阶段 03 用）；
- `git`：版本控制（阶段 01 学）；
- `curl`/`wget`：下载工具；
- `tmux`：终端复用（阶段 01 学）；
- `htop`：查看进程与资源。

> 如果下载很慢：可以在 Ubuntu 里搜索「Ubuntu 24.04 更换清华 TUNA 镜像源」按教程替换 `/etc/apt/sources.list.d/ubuntu.sources` 后再执行上面的命令。

## 5. 资源限制：.wslconfig

WSL2 默认最多可用一半内存与全部 CPU。本机 24 GB 内存、12 线程，建议在 **Windows** 的 `C:\Users\Bob\.wslconfig` 新建文件并写入：

```ini
[wsl2]
memory=12GB
processors=8
swap=8GB
```

- 留一半内存给 Windows，保证两边都流畅；
- 修改后执行 `wsl --shutdown`，再启动 Ubuntu 生效；
- 验证：

```bash
free -h    # Mem 总量约 12Gi
nproc      # 8
```

如果平时用代理上网，可以在 `[wsl2]` 下再加一行 `autoProxy=true`，让 WSL 自动继承 Windows 代理。

## 6. 发行版磁盘位置与迁移到 D 盘（可选）

默认磁盘位置：`C:\Users\Bob\AppData\Local\Packages\...` 或 `%LOCALAPPDATA%\wsl`，核心文件是 `ext4.vhdx`。

C 盘现有 156.7 GB 空闲，够用（见 [04-磁盘评估与外接硬盘建议.md](04-磁盘评估与外接硬盘建议.md)），**不迁移也可以**。如果希望把数据放到 D 盘，方法如下（新版 WSL）：

```powershell
wsl --shutdown
wsl --manage Ubuntu-24.04 --move D:\WSL\Ubuntu-24.04
```

旧版 WSL 的备选方法（导出再导入）：

```powershell
New-Item -ItemType Directory -Force -Path D:\WSL | Out-Null
wsl --export Ubuntu-24.04 D:\WSL\ubuntu-2404-backup.tar
wsl --unregister Ubuntu-24.04
wsl --import Ubuntu-24.04 D:\WSL\Ubuntu-24.04 D:\WSL\ubuntu-2404-backup.tar --version 2
```

导入后默认用户会变成 `root`，修复方法：在 Ubuntu 里创建 `/etc/wsl.conf`，内容为

```ini
[user]
default=bob
```

然后 `wsl --terminate Ubuntu-24.04` 重启即可。

## 7. 常用互操作

- Windows 磁盘：`/mnt/c`、`/mnt/d`（中文目录也能用，如 `/mnt/d/A王晨暄`）；
- 在 WSL 里打开资源管理器：`explorer.exe .`；
- 在 WSL 里用 VSCode 打开当前目录：`code .`（先完成 [02](02-VSCode与WindowsTerminal配置.md) 的配置）；
- 建议：**代码与项目放 WSL 家目录**（`~/projects`，ext4 性能好）；**大数据与备份放 `/mnt/d`**。

## 8. 常见问题

| 现象                     | 处理                                                      |
| ------------------------ | --------------------------------------------------------- |
| 错误码 0x80370102        | BIOS 未开虚拟化或功能未启用；本机已开虚拟化，一般重启即可 |
| `wsl --install` 下载慢 | 改用 Microsoft Store 安装，或配置代理后重试               |
| 忘记 Linux 密码          | `wsl -u root` 进入后执行 `passwd bob` 重置            |
| WSL 占内存太多           | `wsl --shutdown` 释放；检查 `.wslconfig`              |
| 中文路径显示乱码         | 项目路径尽量用英文；文件名用英文                          |
| vhdx 越来越大            | 见 04 文档的回收方法                                      |

## 9. 自测清单

- [ ] `wsl -l -v` 看到 Ubuntu-24.04，VERSION 为 2
- [ ] `wsl --version` 正常输出版本信息
- [ ] Ubuntu 里 `sudo apt update` 成功
- [ ] `.wslconfig` 生效：`free -h` 约 12 GB、`nproc` 为 8
- [ ] 能说清 `/mnt/d` 与 ext4 家目录各自适合放什么

## 参考资料

- Microsoft Learn：WSL 安装文档 https://learn.microsoft.com/windows/wsl/install
- Microsoft Learn：WSL 高级设置配置 https://learn.microsoft.com/windows/wsl/wsl-config
