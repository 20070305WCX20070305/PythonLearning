# 02 VSCode 与 Windows Terminal 配置

## 学习目标

- 把 `code` 命令加入 Windows PATH，并安装 WSL / Python / C 扩展
- 掌握「VSCode + WSL」工作流：在编辑器里写代码，在 Linux 里运行
- 配好 Windows Terminal 的默认配置与常用快捷键

## 前置知识

- 完成 [01-WSL2与Ubuntu安装.md](01-WSL2与Ubuntu安装.md)（Ubuntu 已可用）
- 会基本的窗口与文件操作

## 建议用时

半天

## 1. 现状

- VSCode 已安装在 `D:\Microsoft VS Code`（`Code.exe` 在根目录）；
- 但 `code` 命令目前**不在 PATH**（在 PowerShell 里运行 `code --version` 会提示「无法识别」）。

## 2. 把 code 命令加入 PATH（Windows 侧）

1. 开始菜单搜索「环境变量」→ 打开「编辑系统环境变量」→ 点「环境变量」；
2. 在上方「用户变量」中选中 `Path` → 编辑 → 新建 → 填入：

```
D:\Microsoft VS Code\bin
```

3. 一路「确定」，重开 PowerShell / Windows Terminal，验证：

```powershell
code --version
```

> 如果 `D:\Microsoft VS Code\bin` 不存在，也可直接填 `D:\Microsoft VS Code`。

## 3. 安装扩展

| 扩展 | ID | 用途 |
| --- | --- | --- |
| WSL | `ms-vscode-remote.remote-wsl` | 连接 WSL，必装 |
| Python | `ms-python.python` | 语法、运行、调试 |
| Pylance | `ms-python.vscode-pylance` | 类型提示（装 Python 扩展时通常自动装） |
| C/C++ | `ms-vscode.cpptools` | 阶段 03 用 |
| ShellCheck | `timonwong.shellcheck` | Shell 脚本静态检查（可选） |
| Even Better TOML | `tamasfe.even-better-toml` | 编辑 `pyproject.toml`（可选） |
| GitLens | `eamodio.gitlens` | Git 增强（可选） |

命令行安装（PowerShell，需先完成第 2 步）：

```powershell
code --install-extension ms-vscode-remote.remote-wsl
code --install-extension ms-python.python
code --install-extension ms-vscode.cpptools
```

## 4. 连接 WSL

- 方式 A：VSCode 左下角绿色 `><` 图标 → `Connect to WSL`；
- 方式 B：Ubuntu 终端进入目录后执行 `code .`。

首次连接会在 WSL 内自动下载 VS Code Server（几百 MB），稍等几分钟。

在 WSL 里准备项目目录：

```bash
mkdir -p ~/projects
cd ~/projects
code .
```

## 5. 推荐设置

打开命令面板 `Ctrl+Shift+P` → 输入 `Preferences: Open User Settings (JSON)`：

```json
{
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000,
  "editor.formatOnSave": true,
  "files.eol": "\n",
  "terminal.integrated.defaultProfile.linux": "bash",
  "editor.fontFamily": "Consolas, 'Cascadia Code', monospace"
}
```

其中 `"files.eol": "\n"` 强制使用 LF 换行，避免 Windows / Linux 混用时的换行符问题。

## 6. Windows Terminal

已安装 1.24，设置 → 启动 → 默认配置文件选 `Ubuntu-24.04`。

常用快捷键：

| 快捷键 | 功能 |
| --- | --- |
| `Ctrl+Shift+T` | 新标签 |
| `Ctrl+Shift+W` | 关闭标签 |
| `Alt+Shift+D` | 垂直分屏 |
| `Alt+Shift+加号` | 水平分屏 |
| `Ctrl+Shift+P` | 命令面板 |
| `Ctrl+Shift+空格` | 打开默认配置文件 |

## 7. 工作流小结

- 写代码：VSCode（Remote-WSL，窗口左下角显示 `WSL: Ubuntu-24.04`）；
- 跑命令：VSCode 集成终端或 Windows Terminal，都在 Ubuntu 里；
- 文件：项目放 `~/projects`；在 Windows 资源管理器地址栏输入 `\\wsl$\Ubuntu-24.04\home\<用户名>\projects` 也能访问。

## 8. 自测清单

- [ ] PowerShell 里 `code --version` 有输出
- [ ] VSCode 左下角显示 `WSL: Ubuntu-24.04`
- [ ] 在 `~/projects` 下新建 `hello.py`，用集成终端 `python3 hello.py` 运行成功
- [ ] Windows Terminal 默认打开 Ubuntu-24.04
- [ ] 能说出 `files.eol` 设置的作用

## 参考资料

- VS Code Remote-WSL 文档 https://code.visualstudio.com/docs/remote/wsl
- Windows Terminal 文档 https://learn.microsoft.com/windows/terminal/
