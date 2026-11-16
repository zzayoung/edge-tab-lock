# Edge Tab Lock · 复活 Microsoft Edge 的标签锁定功能

Edge Tab Lock 把「右键锁定标签页」带回 Windows 版 Microsoft Edge。锁定后，扩展与本机辅助程序协作，拦截误按 **Ctrl+W** 和误用**鼠标中键点击标签栏**导致的关闭。选择「锁定并固定标签」还能隐藏标签上的 **×**。

[English](README.md) · [下载最新版本](https://github.com/zzayoung/edge-tab-lock/releases/latest)

| 右键菜单 | 效果 |
| --- | --- |
| **锁定标签，保留标题** | 防止 Ctrl+W 和中键误关闭。保留标签标题和 ×。 |
| **锁定并固定标签，隐藏 ×** | 同样防止 Ctrl+W 和中键误关闭。Edge 会把固定标签缩成图标并隐藏 ×。 |
| **解除标签锁定** | 取消保护。如果标签由扩展在本次会话中固定，也会取消固定。 |

## 安装到日常使用的 Edge

需要 64 位 Windows、桌面版 Microsoft Edge 和 64 位 Python 3。辅助程序安装在当前 Windows 用户下，无需管理员权限或额外的 Python 包。

1. 下载发布页的 **edge-tab-lock-v0.2.0.zip**，解压到可以长期保留的目录。
2. 在解压目录打开 PowerShell，运行 `./install.ps1`。如果找不到 Python，可以运行 `./install.ps1 -PythonExe 'C:\path\to\python.exe'`。Python 和辅助程序安装路径须使用 ASCII 字符。如果 Windows 用户目录含中文，用 `-InstallDirectory` 指定可写的英文路径。
3. 在日常使用的 Edge 配置中打开 `edge://extensions/`，开启「开发人员模式」，点击「加载解压缩的扩展」，选择解压出来的 **extension** 文件夹。已安装的用户在安装辅助程序后可到扩展卡片重新加载。如果目录变了，选择新目录加载。
4. 在标签上右键选择锁定方式。可把扩展固定到工具栏，选中已锁定的标签时会显示 **🔒**。若显示 **!**，说明辅助程序未连接。

## 常见问题

**这是恢复了 Edge 原来的开关吗？** 这个项目用独立扩展和 Windows 辅助程序复刻原来的右键锁定、解锁体验，无需修改 Edge 本体。

**哪些关闭方式受保护？** 当前版本覆盖选中锁定标签时的 Ctrl+W，以及辅助程序能识别目标标签时的中键点击。固定模式另外隐藏 ×。关闭整个窗口、菜单里的「关闭其他标签页」等方式不在当前保护范围。重启 Edge 或重新加载扩展后需要重新锁定，Edge 自身可能保留固定状态。

**为什么需要辅助程序和标签标题权限？** 扩展通过浏览器的本机通信接口，把当前窗口的标签标题和锁定标记交给同一台电脑上的辅助程序。它通过 Windows 的输入和界面识别接口拦截受支持的操作，不联网，也不保存浏览历史。

**怎么卸载？** 在 `edge://extensions/` 中移除扩展。如果当前用户的 `HKCU\Software\Microsoft\Edge\NativeMessagingHosts\local.tab_guard` 注册项指向这套程序，可删除该项，再删除辅助程序目录（默认是 `%LOCALAPPDATA%\EdgeTabLock`）。
