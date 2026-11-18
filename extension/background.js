const chinese = chrome.i18n.getUILanguage().startsWith('zh');
const locked = new Set();
const pinnedByLock = new Set();
const active = new Map();
let focused = chrome.windows.WINDOW_ID_NONE;
let port;
let ready = false;
let syncVersion = 0;
let retryDelay = 500;

async function sync() {
  const version = ++syncVersion;
  const tabId = active.get(focused);
  if (ready) port.postMessage({ protect: locked.has(tabId) });
  if (tabId !== undefined) {
    chrome.action.setBadgeText({ tabId, text: locked.has(tabId) ? (ready ? '🔒' : '!') : '' }).catch(() => {});
    chrome.action.setBadgeBackgroundColor({ tabId, color: '#1769aa' }).catch(() => {});
  }
  if (!ready) return;
  if (!locked.size || focused === chrome.windows.WINDOW_ID_NONE) {
    port.postMessage({ tabs: [] });
    return;
  }
  const tabs = await chrome.tabs.query({ windowId: focused }).catch(() => []);
  if (version === syncVersion && ready) {
    port.postMessage({ tabs: tabs.map(tab => [tab.title ?? '', locked.has(tab.id)]) });
  }
}

async function connect() {
  if (port) return;
  port = chrome.runtime.connectNative('local.tab_guard');
  port.onDisconnect.addListener(() => {
    const error = chrome.runtime.lastError?.message;
    if (error) console.warn(error);
    port = undefined;
    ready = false;
    chrome.action.setTitle({ title: chinese ? '标签保护未连接，请检查本机辅助程序' : 'Edge Tab Lock helper disconnected' });
    sync();
    setTimeout(connect, retryDelay);
    retryDelay = Math.min(retryDelay * 2, 10000);
  });
  port.onMessage.addListener(message => {
    if (message.ready) {
      ready = true;
      retryDelay = 500;
      chrome.action.setTitle({ title: chinese ? '标签保护已连接' : 'Edge Tab Lock helper connected' });
      sync();
    }
  });
  for (const window of await chrome.windows.getAll({ populate: true })) {
    const tab = window.tabs.find(t => t.active);
    if (tab) active.set(window.id, tab.id);
    if (window.focused) focused = window.id;
  }
  sync();
}

chrome.runtime.onInstalled.addListener(async () => {
  await chrome.contextMenus.removeAll();
  chrome.contextMenus.create({ id: 'lock', title: chinese ? '锁定标签，保留标题' : 'Lock tab and keep title', contexts: ['tab'] });
  chrome.contextMenus.create({ id: 'lock-and-pin', title: chinese ? '锁定并固定标签，隐藏 ×' : 'Lock and pin tab (hide ×)', contexts: ['tab'] });
  chrome.contextMenus.create({ id: 'unlock', title: chinese ? '解除标签锁定' : 'Unlock tab', contexts: ['tab'] });
});
chrome.runtime.onMessage.addListener((message, _sender, respond) => {
  if (message === 'tab-protection-status') {
    respond({ locked: [...locked], ready });
  }
});
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'lock') locked.add(tab.id);
  if (info.menuItemId === 'lock-and-pin') {
    if (!tab.pinned) {
      await chrome.tabs.update(tab.id, { pinned: true });
      pinnedByLock.add(tab.id);
    }
    locked.add(tab.id);
  }
  if (info.menuItemId === 'unlock') {
    if (pinnedByLock.has(tab.id)) {
      await chrome.tabs.update(tab.id, { pinned: false });
      pinnedByLock.delete(tab.id);
    }
    locked.delete(tab.id);
  }
  const [selected] = await chrome.tabs.query({ active: true, windowId: tab.windowId });
  if (selected) active.set(tab.windowId, selected.id);
  const window = await chrome.windows.get(tab.windowId);
  if (window.focused) focused = window.id;
  await connect();
  sync();
});
chrome.tabs.onActivated.addListener(({ tabId, windowId }) => { active.set(windowId, tabId); sync(); });
chrome.tabs.onRemoved.addListener(tabId => {
  locked.delete(tabId);
  pinnedByLock.delete(tabId);
  sync();
});
chrome.tabs.onCreated.addListener(sync);
chrome.tabs.onMoved.addListener(sync);
chrome.tabs.onAttached.addListener(sync);
chrome.tabs.onDetached.addListener(sync);
chrome.tabs.onUpdated.addListener((_tabId, change) => {
  if (change.title !== undefined || change.pinned !== undefined) sync();
});
chrome.windows.onFocusChanged.addListener(windowId => { focused = windowId; sync(); });
chrome.runtime.onStartup.addListener(connect);
connect();
