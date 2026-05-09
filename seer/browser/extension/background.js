// Service worker — polls for commands from the bridge and routes to content script

const BRIDGE = 'http://localhost:7842';
const POLL_MS = 300;

async function getActiveTabId() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab?.id ?? null;
}

async function sendToContent(tabId, msg) {
  try {
    return await chrome.tabs.sendMessage(tabId, msg);
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

async function poll() {
  try {
    const res = await fetch(`${BRIDGE}/command`, { method: 'GET' });
    if (!res.ok) return;
    const cmd = await res.json();
    if (!cmd || !cmd.type) return;

    const tabId = await getActiveTabId();
    if (!tabId) {
      await fetch(`${BRIDGE}/result`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ok: false, error: 'No active tab' })
      });
      return;
    }

    const result = await sendToContent(tabId, cmd);
    await fetch(`${BRIDGE}/result`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(result ?? { ok: false, error: 'No response from content script' })
    });
  } catch (_) {
    // Bridge not running — silently skip
  }
}

// Poll continuously
setInterval(poll, POLL_MS);
