# Edge Tab Lock — bring back tab locking in Microsoft Edge

**Edge Tab Lock brings back right-click tab locking in Microsoft Edge on Windows.** Protect selected tabs from accidental closure by **Ctrl+W** or a **middle-click on the tab bar**. Choose **Lock and pin tab (hide ×)** to also hide the close button.

[简体中文](README.zh-CN.md) · [Download the latest release](https://github.com/zzayoung/edge-tab-lock/releases/latest)

| Right-click a tab and choose | Result |
| --- | --- |
| **Lock tab and keep title** | Protects against Ctrl+W and middle-click. Edge still displays the title and its usual close button. |
| **Lock and pin tab (hide ×)** | Adds the same protection and uses Edge's pinned-tab layout to hide × and collapse the title to an icon. |
| **Unlock tab** | Removes protection and undoes any pin applied by Edge Tab Lock during this session. |

## Install on Windows

Requires desktop Microsoft Edge on **64-bit Windows** and **64-bit Python 3**. The helper runs under your Windows account, with no administrator install or Python packages needed.

1. Download **edge-tab-lock-v0.2.4.zip** from Releases and extract it to a folder you can keep.
2. Open PowerShell in the extracted folder and run `./install.ps1`. This installs and registers the local helper for your Windows account. If Python isn't found, use `./install.ps1 -PythonExe 'C:\path\to\python.exe'`. The Python and helper installation paths must use ASCII characters. If your Windows user folder contains non-ASCII characters, pass a writable ASCII path with `-InstallDirectory`.
3. In your everyday Edge profile, open `edge://extensions/`, enable **Developer mode**, and use **Load unpacked** to select the extracted **extension** folder. If upgrading an existing installation, reload the extension from its card after installing the helper, or load the new folder if its location changed.
4. Right-click a tab and choose a lock action. Click **Edge Tab Lock** in the Extensions menu to see which tabs in the current window are locked, pinned, or both. Pin the extension to the toolbar to see a **🔒** badge on the active locked tab. A **!** badge means the helper is disconnected.

## Frequently asked questions

**Does it bring back the old Microsoft Edge lock-tab feature?** It recreates the right-click lock and unlock workflow as an independent extension with a Windows helper. It is not an official Microsoft extension or a patch to Edge.

**Which close actions does it cover?** Ctrl+W for the active locked tab and middle-click on a locked tab when the helper can match the tab bar it sees to Edge's tab list. The pin option also hides ×. Closing the entire window, menu commands such as **Close other tabs**, and other close paths are outside this release. The lock is session-only and must be set again after restarting Edge or reloading the extension. Edge may retain the pin separately.

**Why does it need a helper and access to tab titles?** The extension sends current tab titles and lock flags to a same-PC helper through Native Messaging. The helper uses Windows input hooks and UI Automation to identify the tab under the pointer and intercept supported close actions. It makes no network requests and does not store browsing history. The toolbar lock marks the active tab.

**How do I remove it?** Remove Edge Tab Lock from `edge://extensions/`, remove its current-user registration at `HKCU\Software\Microsoft\Edge\NativeMessagingHosts\local.tab_guard` if it points to this installation, and then delete the helper folder (by default, `%LOCALAPPDATA%\EdgeTabLock`).
