// Service worker — connects to Seer's Native Messaging Host with throttled reconnect.

const HOST_NAME = 'com.seer.host';
let port = null;
let lastConnectAt = 0;
const MIN_RECONNECT_MS = 5000; // back off to avoid spawn storms

function connect() {
  const now = Date.now();
  if (now - lastConnectAt < MIN_RECONNECT_MS) return;
  lastConnectAt = now;

  try {
    port = chrome.runtime.connectNative(HOST_NAME);
  } catch (e) {
    console.error('[seer] connectNative failed — is the native messaging host registered? Run: python -m seer.browser.install_native_host <ext_id>', e);
    port = null;
    return;
  }

  port.onMessage.addListener(async (cmd) => {
    if (!cmd || !cmd.type) return;
    let result;
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab?.id) {
        result = { ok: false, error: 'No active tab' };
      } else if (cmd.type === 'EXTRACT') {
        // Static-function injection — bypasses page CSP because no string eval.
        try {
          const [{ result: value }] = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            world: 'MAIN',
            args: [cmd.selector, cmd.attribute || 'innerText', cmd.limit || 50],
            func: (selector, attribute, limit) => {
              try {
                const els = [...document.querySelectorAll(selector)].slice(0, limit);
                const items = els.map((el) => {
                  const v = el[attribute];
                  if (v == null) return el.getAttribute?.(attribute) ?? null;
                  return typeof v === 'string' ? v.trim() : String(v);
                });
                return { ok: true, count: els.length, items };
              } catch (e) {
                return { ok: false, error: String(e) };
              }
            },
          });
          result = value ?? { ok: false, error: 'executeScript returned no result' };
        } catch (e) {
          result = { ok: false, error: 'executeScript: ' + e.message };
        }
      } else if (cmd.type === 'EVAL') {
        // Use chrome.scripting in MAIN world — bypasses page CSP (eval limits don't apply to extension-injected code).
        try {
          const [{ result: value }] = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            world: 'MAIN',
            args: [cmd.code],
            func: async (code) => {
              try {
                // Wrap in async fn so user code can use await
                const fn = new Function('return (async () => { return (' + code + ') })()');
                const v = await fn();
                return { ok: true, result: v !== undefined ? String(v) : null };
              } catch (e) {
                return { ok: false, error: String(e) };
              }
            },
          });
          result = value ?? { ok: false, error: 'executeScript returned no result' };
        } catch (e) {
          result = { ok: false, error: 'executeScript: ' + e.message };
        }
      } else {
        try {
          result = await chrome.tabs.sendMessage(tab.id, cmd);
        } catch (_) {
          try {
            result = await chrome.runtime.sendMessage(cmd);
          } catch (e2) {
            result = { ok: false, error: e2.message };
          }
        }
      }
    } catch (e) {
      result = { ok: false, error: e.message };
    }
    try {
      port.postMessage(result ?? { ok: false, error: 'No response from content script' });
    } catch (e) {
      console.error('[seer] postMessage failed — native host likely died', e);
      port = null;
      setTimeout(connect, MIN_RECONNECT_MS);
    }
  });

  port.onDisconnect.addListener(() => {
    port = null;
    setTimeout(connect, MIN_RECONNECT_MS);
  });
}

connect();

// Popup uses this to show connection status.
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === 'PING_BRIDGE') {
    sendResponse({ ok: !!port });
    return false;
  }
});

// Keep service worker alive — MV3 idles workers after ~30s, which would kill the native host.
chrome.alarms.create('seer-keepalive', { periodInMinutes: 0.4 }); // every 24s
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'seer-keepalive') {
    if (!port) connect();
  }
});
