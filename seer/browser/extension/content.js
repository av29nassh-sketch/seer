// Content script — polls bridge for commands and executes them in the page

const BRIDGE = 'http://127.0.0.1:7842';
const POLL_MS = 400;

// ── DOM extraction ──────────────────────────────────────────────────────────

const SKIP_TAGS = new Set(['script','style','noscript','svg','path','meta','link','head']);
const INTERACTIVE_ROLES = new Set([
  'button','link','textbox','searchbox','combobox','listbox',
  'menuitem','tab','checkbox','radio','switch','slider'
]);
const MAX_NODES = 200;

function extractDOM() {
  const nodes = [];
  let counter = 0;

  function walk(el, depth) {
    if (counter >= MAX_NODES || depth > 8) return;
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
  return {
    url: location.href,
    title: document.title,
    node_count: nodes.length,
    truncated: counter >= MAX_NODES,
    nodes
  };
}

function findElement(nodeId) {
  let counter = 0;
  let found = null;

  function walk(el, depth) {
    if (found || counter >= MAX_NODES || depth > 8) return;
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

// ── Bridge polling ──────────────────────────────────────────────────────────

async function postResult(result) {
  await fetch(`${BRIDGE}/result`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(result)
  });
}

async function poll() {
  try {
    const res = await fetch(`${BRIDGE}/command`, { method: 'GET' });
    if (res.status === 204) return; // no pending command
    if (!res.ok) return;

    const cmd = await res.json();
    if (!cmd?.type) return;

    if (cmd.type === 'GET_DOM') {
      await postResult({ ok: true, data: extractDOM() });

    } else if (cmd.type === 'CLICK') {
      const el = findElement(cmd.nodeId);
      if (!el) {
        await postResult({ ok: false, error: `Node ${cmd.nodeId} not found` });
        return;
      }
      el.scrollIntoView({ block: 'center' });
      el.click();
      await postResult({ ok: true, tag: el.tagName?.toLowerCase() });

    } else if (cmd.type === 'TYPE') {
      const el = findElement(cmd.nodeId);
      if (!el) {
        await postResult({ ok: false, error: `Node ${cmd.nodeId} not found` });
        return;
      }
      el.focus();
      el.value = cmd.text;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      await postResult({ ok: true });

    } else if (cmd.type === 'QUERY_CLICK') {
      const els = document.querySelectorAll(cmd.selector);
      els.forEach(el => el.click());
      await postResult({ ok: true, count: els.length });

    } else if (cmd.type === 'QUERY_DBLCLICK') {
      const el = document.querySelector(cmd.selector);
      if (!el) {
        await postResult({ ok: false, error: `No element found: ${cmd.selector}` });
        return;
      }
      el.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true }));
      await postResult({ ok: true });
    }
  } catch (_) {
    // Bridge not running or network error — silently skip
  }
}

setInterval(poll, POLL_MS);
