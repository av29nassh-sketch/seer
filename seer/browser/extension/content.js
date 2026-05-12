// Content script — receives commands from background.js (Native Messaging) and executes them in the page.

const SKIP_TAGS = new Set(['script','style','noscript','svg','path','meta','link','head']);
const INTERACTIVE_ROLES = new Set([
  'button','link','textbox','searchbox','combobox','listbox',
  'menuitem','tab','checkbox','radio','switch','slider'
]);
const MAX_NODES = 600;

function extractDOM() {
  const nodes = [];
  let counter = 0;

  function walk(el, depth) {
    if (counter >= MAX_NODES || depth > 12) return;
    if (!el || SKIP_TAGS.has(el.tagName?.toLowerCase())) return;

    const tag = el.tagName?.toLowerCase() || '';
    const ariaRole = el.getAttribute?.('role') || '';
    const ariaLabel = el.getAttribute?.('aria-label') || '';
    const text = (el.innerText || el.textContent || '').trim().slice(0, 100);
    const placeholder = el.placeholder || '';
    const value = (tag === 'input' || tag === 'textarea') ? (el.value || '') : '';
    const href = el.href || '';
    const type = el.type || '';
    const id = el.id || '';

    const isInteractive =
      ['a','button','input','textarea','select'].includes(tag) ||
      INTERACTIVE_ROLES.has(ariaRole) ||
      el.getAttribute?.('onclick') != null ||
      el.getAttribute?.('tabindex') != null;

    if (isInteractive || text.length > 0) {
      const node = { id: counter, tag, depth };
      if (ariaLabel) node.aria_label = ariaLabel;
      if (ariaRole) node.role = ariaRole;
      if (text && text !== placeholder) node.text = text.slice(0, 80);
      if (id) node.element_id = id;
      if (href) node.href = href.slice(0, 120);
      if (placeholder) node.placeholder = placeholder;
      if (value) node.value = value.slice(0, 80);
      if (type) node.type = type;
      nodes.push(node);
      counter++;
    }
    for (const child of el.children) walk(child, depth + 1);
  }

  walk(document.body, 0);
  return { url: location.href, title: document.title, node_count: nodes.length, truncated: counter >= MAX_NODES, nodes };
}

function findElement(nodeId) {
  let counter = 0;
  let found = null;

  function walk(el, depth) {
    if (found || counter >= MAX_NODES || depth > 12) return;
    if (!el || SKIP_TAGS.has(el.tagName?.toLowerCase())) return;

    const tag = el.tagName?.toLowerCase() || '';
    const ariaRole = el.getAttribute?.('role') || '';
    const text = (el.innerText || el.textContent || '').trim();

    const isInteractive =
      ['a','button','input','textarea','select'].includes(tag) ||
      INTERACTIVE_ROLES.has(ariaRole) ||
      el.getAttribute?.('onclick') != null ||
      el.getAttribute?.('tabindex') != null;

    if (isInteractive || text.length > 0) {
      if (counter === nodeId) { found = el; return; }
      counter++;
    }
    for (const child of el.children) walk(child, depth + 1);
  }

  walk(document.body, 0);
  return found;
}

async function handleCommand(cmd) {
  if (!cmd?.type) return { ok: false, error: 'no command type' };

  if (cmd.type === 'GET_DOM') {
    return { ok: true, data: extractDOM() };
  }

  if (cmd.type === 'CLICK') {
    const el = findElement(cmd.nodeId);
    if (!el) return { ok: false, error: `Node ${cmd.nodeId} not found` };
    el.scrollIntoView({ block: 'center' });
    el.click();
    return { ok: true, tag: el.tagName?.toLowerCase() };
  }

  if (cmd.type === 'TYPE') {
    const el = findElement(cmd.nodeId);
    if (!el) return { ok: false, error: `Node ${cmd.nodeId} not found` };
    el.focus();
    const tag = el.tagName.toLowerCase();
    const proto = tag === 'textarea' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
    const nativeSetter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (nativeSetter) nativeSetter.call(el, cmd.text);
    else el.value = cmd.text;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return { ok: true };
  }

  if (cmd.type === 'NAVIGATE') {
    location.href = cmd.url;
    return { ok: true };
  }

  if (cmd.type === 'QUERY_CLICK') {
    const els = document.querySelectorAll(cmd.selector);
    if (els.length === 0) return { ok: false, error: `No elements match: ${cmd.selector}` };
    // Click only the first match by default — deterministic. Use cmd.all=true to click all.
    if (cmd.all) {
      els.forEach(el => el.click());
      return { ok: true, count: els.length };
    }
    els[0].scrollIntoView({ block: 'center' });
    els[0].click();
    return { ok: true, matched: els.length, clicked: 1 };
  }

  if (cmd.type === 'QUERY_DBLCLICK') {
    const el = document.querySelector(cmd.selector);
    if (!el) return { ok: false, error: `No element found: ${cmd.selector}` };
    el.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }));
    return { ok: true };
  }

  if (cmd.type === 'EVAL') {
    // EVAL is handled by background.js via chrome.scripting.executeScript — never reach here.
    // Refuse so an attacker who somehow drives a bypassing message can't RCE.
    return { ok: false, error: 'EVAL must be routed via background.js executeScript, not content.js' };
  }

  if (cmd.type === 'SCROLL_TO_BOTTOM') {
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(r => setTimeout(r, 300));
    return { ok: true };
  }

  if (cmd.type === 'SCROLL') {
    if (cmd.selector) {
      const el = document.querySelector(cmd.selector);
      if (!el) return { ok: false, error: `No element: ${cmd.selector}` };
      if (cmd.to_bottom) {
        el.scrollTop = el.scrollHeight;
        el.dispatchEvent(new Event('scroll', { bubbles: true }));
      } else {
        el.scrollIntoView({ block: 'center' });
      }
    } else if (cmd.y !== undefined) {
      window.scrollBy(0, cmd.y);
    } else {
      document.querySelectorAll('*').forEach(el => {
        const s = window.getComputedStyle(el);
        if ((s.overflowY === 'scroll' || s.overflowY === 'auto') && el.scrollHeight > el.clientHeight + 10) {
          el.scrollTop = el.scrollHeight;
          el.dispatchEvent(new Event('scroll', { bubbles: false }));
          el.dispatchEvent(new Event('scroll', { bubbles: true }));
          el.dispatchEvent(new UIEvent('scroll', { bubbles: false, view: window }));
          el.dispatchEvent(new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: 9999 }));
          document.dispatchEvent(new Event('scroll', { bubbles: false }));
        }
      });
      window.scrollTo(0, document.body.scrollHeight);
    }
    await new Promise(r => setTimeout(r, 1000));
    return { ok: true };
  }

  if (cmd.type === 'HOVER') {
    const el = findElement(cmd.nodeId);
    if (!el) return { ok: false, error: `Node ${cmd.nodeId} not found` };
    el.scrollIntoView({ block: 'center' });
    el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, cancelable: true }));
    el.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true, cancelable: true }));
    return { ok: true, tag: el.tagName?.toLowerCase() };
  }

  if (cmd.type === 'KEY') {
    const target = cmd.nodeId !== undefined ? findElement(cmd.nodeId) : document.activeElement;
    const el = target || document.body;
    if (cmd.nodeId !== undefined) el.focus?.();
    ['keydown', 'keypress', 'keyup'].forEach(t =>
      el.dispatchEvent(new KeyboardEvent(t, { key: cmd.key, bubbles: true, cancelable: true }))
    );
    return { ok: true };
  }

  if (cmd.type === 'SELECT') {
    const el = findElement(cmd.nodeId);
    if (!el || el.tagName?.toLowerCase() !== 'select') return { ok: false, error: `Node ${cmd.nodeId} is not a select element` };
    const opt = Array.from(el.options).find(o => o.value === cmd.value || o.text === cmd.value);
    if (!opt) return { ok: false, error: `Option "${cmd.value}" not found` };
    el.value = opt.value;
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return { ok: true, selected: opt.text };
  }

  return { ok: false, error: `Unknown command type: ${cmd.type}` };
}

chrome.runtime.onMessage.addListener((cmd, _sender, sendResponse) => {
  handleCommand(cmd).then(sendResponse).catch(e => sendResponse({ ok: false, error: String(e) }));
  return true; // keep channel open for async sendResponse
});
