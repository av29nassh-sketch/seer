// Popup script — ask the background service worker if it's connected to the native host.

(async () => {
  const dot = document.getElementById('dot');
  const label = document.getElementById('label');
  try {
    const reply = await chrome.runtime.sendMessage({ type: 'PING_BRIDGE' });
    if (reply?.ok) {
      dot.className = 'dot ok';
      label.textContent = 'Connected to Seer';
    } else {
      dot.className = 'dot bad';
      label.textContent = 'Seer app not running';
    }
  } catch (e) {
    dot.className = 'dot bad';
    label.textContent = 'Seer app not running';
  }
})();
