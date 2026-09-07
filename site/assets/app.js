(() => {
  'use strict';

  const root = document.documentElement;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  root.classList.add('motion-ready');

  const setText = (selector, value) => {
    const el = document.querySelector(selector);
    if (el && value !== undefined && value !== null) el.textContent = String(value);
  };

  if (!reducedMotion) {
    const revealTargets = document.querySelectorAll(
      '.section-head, .stat, .status-panel, .flow article, .classification-grid article, .evidence-grid article, .safety-box, .source-list a, footer'
    );

    revealTargets.forEach((el, index) => {
      el.classList.add('reveal');
      el.dataset.delay = String((index % 4) + 1);
    });

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

      revealTargets.forEach((el) => observer.observe(el));
    } else {
      revealTargets.forEach((el) => el.classList.add('is-visible'));
    }

    let pointerFrame = 0;
    window.addEventListener('pointermove', (event) => {
      if (pointerFrame) return;
      pointerFrame = requestAnimationFrame(() => {
        root.style.setProperty('--mx', `${Math.round((event.clientX / window.innerWidth) * 100)}%`);
        root.style.setProperty('--my', `${Math.round((event.clientY / window.innerHeight) * 100)}%`);
        pointerFrame = 0;
      });
    }, { passive: true });
  }

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
