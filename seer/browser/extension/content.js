// Content script — runs in every page, extracts a filtered DOM snapshot

function extractDOM() {
  const MAX_NODES = 200;
  const nodes = [];
  let counter = 0;

  const SKIP_TAGS = new Set([
    'script', 'style', 'noscript', 'svg', 'path', 'meta', 'link', 'head'
  ]);

  const INTERACTIVE_ROLES = new Set([
    'button', 'link', 'textbox', 'searchbox', 'combobox', 'listbox',
    'menuitem', 'tab', 'checkbox', 'radio', 'switch', 'slider'
  ]);

  function walk(el, depth) {
    if (counter >= MAX_NODES || depth > 8) return;
    if (SKIP_TAGS.has(el.tagName?.toLowerCase())) return;

    const tag = el.tagName?.toLowerCase() || '';
    const role = el.getAttribute?.('aria-label') ? el.getAttribute('aria-label') : '';
    const ariaRole = el.getAttribute?.('role') || '';
    const text = (el.innerText || el.textContent || '').trim().slice(0, 100);
    const id = el.id || '';
    const cls = (el.className && typeof el.className === 'string')
      ? el.className.split(' ').filter(Boolean).slice(0, 3).join(' ')
      : '';
    const href = el.href || '';
    const placeholder = el.placeholder || '';
    const value = (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') ? (el.value || '') : '';
    const type = el.type || '';

    const isInteractive =
      ['a', 'button', 'input', 'textarea', 'select', 'label'].includes(tag) ||
      INTERACTIVE_ROLES.has(ariaRole) ||
      el.getAttribute?.('onclick') != null ||
      el.getAttribute?.('tabindex') != null;

    const hasText = text.length > 0;

    if (isInteractive || hasText) {
      const node = { id: counter, tag, depth };
      if (role) node.aria_label = role;
      if (ariaRole) node.role = ariaRole;
      if (text && text !== placeholder) node.text = text.slice(0, 80);
      if (id) node.element_id = id;
      if (cls) node.classes = cls;
      if (href) node.href = href.slice(0, 120);
      if (placeholder) node.placeholder = placeholder;
      if (value) node.value = value.slice(0, 80);
      if (type) node.type = type;
      nodes.push(node);
      counter++;
    }

    for (const child of el.children) {
      walk(child, depth + 1);
    }
  }

  walk(document.body, 0);

  return {
    url: location.href,
    title: document.title,
    node_count: nodes.length,
    truncated: counter >= MAX_NODES,
    nodes
  };
}

function findElement(nodeId) {
  // Re-walk to find element by its position in our filtered tree
  const MAX_NODES = 200;
  const SKIP_TAGS = new Set(['script','style','noscript','svg','path','meta','link','head']);
  const INTERACTIVE_ROLES = new Set([
    'button','link','textbox','searchbox','combobox','listbox',
    'menuitem','tab','checkbox','radio','switch','slider'
  ]);

  let counter = 0;
  let found = null;

  function walk(el, depth) {
    if (found || counter >= MAX_NODES || depth > 8) return;
    if (SKIP_TAGS.has(el.tagName?.toLowerCase())) return;

    const tag = el.tagName?.toLowerCase() || '';
    const ariaRole = el.getAttribute?.('role') || '';
    const text = (el.innerText || el.textContent || '').trim();

    const isInteractive =
      ['a','button','input','textarea','select','label'].includes(tag) ||
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

// Listen for commands from background script
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === 'GET_DOM') {
    sendResponse({ ok: true, data: extractDOM() });
  } else if (msg.type === 'CLICK') {
    const el = findElement(msg.nodeId);
    if (!el) { sendResponse({ ok: false, error: `Node ${msg.nodeId} not found` }); return; }
    el.scrollIntoView({ block: 'center' });
    el.click();
    sendResponse({ ok: true, tag: el.tagName?.toLowerCase() });
  } else if (msg.type === 'TYPE') {
    const el = findElement(msg.nodeId);
    if (!el) { sendResponse({ ok: false, error: `Node ${msg.nodeId} not found` }); return; }
    el.focus();
    el.value = msg.text;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    sendResponse({ ok: true });
  }
  return true; // keep channel open for async
});
