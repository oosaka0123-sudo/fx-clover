(() => {
  'use strict';

  const setText = (selector, value) => {
    const el = document.querySelector(selector);
    if (el && value !== undefined && value !== null) el.textContent = String(value);
  };

  fetch('./status.json', { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) throw new Error(`status.json HTTP ${response.status}`);
      return response.json();
    })
    .then((data) => {
      document.querySelectorAll('[data-key]').forEach((el) => {
        const key = el.dataset.key;
        if (Object.prototype.hasOwnProperty.call(data, key)) el.textContent = data[key];
      });
      setText('#updated', `PUBLIC STATUS · ${data.updated || 'unknown'}`);
    })
    .catch(() => {
      setText('#updated', 'PUBLIC STATUS · STATIC FALLBACK');
    });
})();
