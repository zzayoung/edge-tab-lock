async function showTabs() {
  const notice = document.getElementById('notice');
  const list = document.getElementById('tabs');
  const chinese = chrome.i18n.getUILanguage().startsWith('zh');

  if (chinese) {
    document.documentElement.lang = 'zh-CN';
    document.title = '标签保护';
    document.querySelector('h1').textContent = '当前窗口的标签';
    notice.textContent = '正在读取标签状态…';
    list.setAttribute('aria-label', '标签列表');
  }

  try {
    const [tabs, status] = await Promise.all([
      chrome.tabs.query({ currentWindow: true }),
      chrome.runtime.sendMessage('tab-protection-status'),
    ]);
    const locked = new Set(status.locked);
    const protectedCount = tabs.filter(tab => locked.has(tab.id)).length;
    notice.textContent = status.ready
      ? (chinese
        ? (protectedCount ? `${protectedCount} 个标签已锁定` : '当前窗口没有锁定标签')
        : (protectedCount === 1 ? '1 locked tab' : `${protectedCount} locked tabs`))
      : (chinese ? '辅助程序未连接，锁定保护暂未生效' : 'Helper disconnected. Tab protection is unavailable.');

    for (const tab of tabs) {
      const isLocked = locked.has(tab.id);
      const row = document.createElement('li');
      const button = document.createElement('button');
      const title = document.createElement('span');
      const label = document.createElement('span');
      title.className = 'title';
      title.textContent = tab.title || (chinese ? '未命名标签' : 'Untitled tab');
      button.title = title.textContent;
      if (tab.active) button.setAttribute('aria-current', 'true');
      label.className = 'status';
      if (isLocked) {
        label.textContent = chinese ? '🔒 已锁定' : '🔒 Locked';
        if (tab.pinned) label.textContent += chinese ? ' · 📌 已固定' : ' · 📌 Pinned';
      } else if (tab.pinned) {
        label.textContent = (chinese ? '📌 仅固定' : '📌 Pinned only');
      } else {
        label.textContent = (chinese ? '未锁定' : 'Unlocked');
      }
      button.append(title, label);
      button.addEventListener('click', async () => {
        try {
          await chrome.tabs.update(tab.id, { active: true });
          window.close();
        } catch {
          notice.textContent = (chinese ? '该标签已关闭或移出当前窗口' : 'The tab closed or moved to another window.');
          row.remove();
        }
      });
      row.append(button);
      list.append(row);
    }
  } catch {
    notice.textContent = (chinese ? '读取失败，请关闭面板后重试' : 'Close and reopen this panel to try again.');
  }
}

showTabs();
