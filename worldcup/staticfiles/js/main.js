/**
 * FIFA World Cup 2026 Family Prediction League — Main JavaScript
 * ================================================================
 * Vanilla JS interactive & animated features for the premium
 * football prediction site.
 *
 * Features:
 *  1. Countdown Timer with flip animation
 *  2. Confetti Effect
 *  3. Floating Footballs background
 *  4. PARALLAX SCROLL — Players, logos, watermarks respond to scroll
 *  5. Particle Canvas — Colorful particles
 *  6. Navbar scroll detection
 *  7. Prediction Form (AJAX, score picker)
 *  8. Toast Notifications
 *  9. Page Load Animation
 *  10. CSRF & Gateway Integration
 */

(function () {
  'use strict';

  const prefersReducedMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches;

  function debounce(fn, delay) {
    let timer = null;
    return function () {
      const ctx = this;
      const args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () {
        fn.apply(ctx, args);
      }, delay);
    };
  }

  function getCSRFToken() {
    const cookie = document.cookie
      .split(';')
      .filter(function (c) {
        return c.trim().startsWith('csrftoken=');
      });
    if (cookie.length) return cookie[0].split('=')[1];
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  // ==================================================================
  // 1. COUNTDOWN TIMER
  // ==================================================================
  let countdownData = {
    days: 0, hours: 0, minutes: 0, seconds: 0,
    match: null, home_team: null, away_team: null,
  };

  function initCountdown() {
    const container = document.getElementById('countdown');
    if (!container) return;

    if (!container.querySelector('.countdown-digit')) {
      container.innerHTML = buildCountdownHTML();
    }

    fetchCountdown();
    setInterval(fetchCountdown, 60000);
    setInterval(tickCountdown, 1000);
  }

  function buildCountdownHTML() {
    const units = ['days', 'hours', 'minutes', 'seconds'];
    const labels = ['Days', 'Hours', 'Minutes', 'Seconds'];
    let html = '';
    units.forEach(function (unit, i) {
      html +=
        '<div class="countdown-unit">' +
        '  <div class="countdown-digit" data-unit="' + unit + '">' +
        '    <span class="digit-current">00</span>' +
        '  </div>' +
        '  <div class="countdown-label">' + labels[i] + '</div>' +
        '</div>';
      if (i < 3) {
        html += '<span class="countdown-sep" style="color:rgba(212,175,55,0.3);font-size:1.5rem;font-weight:800;margin-top:-20px;">:</span>';
      }
    });
    return html;
  }

  function fetchCountdown() {
    const port = new URLSearchParams(window.location.search).get('XTransformPort');
    let url = '/api/countdown/';
    if (port) url += '?XTransformPort=' + port;

    fetch(url)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.seconds_remaining > 0) {
          const total = data.seconds_remaining;
          countdownData.days = Math.floor(total / 86400);
          countdownData.hours = Math.floor((total % 86400) / 3600);
          countdownData.minutes = Math.floor((total % 3600) / 60);
          countdownData.seconds = total % 60;
          countdownData.match = data.match;
          countdownData.home_team = data.home_team;
          countdownData.away_team = data.away_team;
        }
      })
      .catch(function () {});
  }

  function tickCountdown() {
    if (countdownData.seconds > 0) {
      countdownData.seconds--;
      if (countdownData.seconds < 0) {
        countdownData.seconds = 59;
        countdownData.minutes--;
        if (countdownData.minutes < 0) {
          countdownData.minutes = 59;
          countdownData.hours--;
          if (countdownData.hours < 0) {
            countdownData.hours = 23;
            countdownData.days = Math.max(0, countdownData.days - 1);
          }
        }
      }
    }
    updateCountdownDisplay();
  }

  function updateCountdownDisplay() {
    const units = ['days', 'hours', 'minutes', 'seconds'];
    units.forEach(function (unit) {
      const el = document.querySelector('.countdown-digit[data-unit="' + unit + '"]');
      if (!el) return;
      const val = countdownData[unit];
      const padded = val < 10 ? '0' + val : '' + val;
      const current = el.querySelector('.digit-current');
      if (current && current.textContent !== padded) {
        current.textContent = padded;
      }
    });
  }


  // ==================================================================
  // 2. CONFETTI
  // ==================================================================
  function fireConfetti() {
    if (prefersReducedMotion) return;
    const container = document.getElementById('confettiContainer');
    if (!container) return;
    const colors = ['#d4af37', '#f5d442', '#10b981', '#3b82f6', '#ef4444', '#f59e0b', '#8b5cf6'];
    for (let i = 0; i < 80; i++) {
      const piece = document.createElement('div');
      piece.className = 'confetti-piece';
      piece.style.left = Math.random() * 100 + '%';
      piece.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
      piece.style.animationDelay = (Math.random() * 1.5) + 's';
      piece.style.animationDuration = (2 + Math.random() * 2) + 's';
      piece.style.width = (6 + Math.random() * 8) + 'px';
      piece.style.height = (6 + Math.random() * 8) + 'px';
      piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
      container.appendChild(piece);
      setTimeout(function () {
        if (piece.parentNode) piece.parentNode.removeChild(piece);
      }, 5000);
    }
  }


  // Floating footballs removed — caused mobile flickering


  // Parallax scroll removed — caused mobile flickering, players not visible


  // Particle canvas removed — caused mobile flickering


  // ==================================================================
  // 6. NAVBAR SCROLL DETECTION
  // ==================================================================
  function initNavbar() {
    const navbar = document.getElementById('mainNavbar');
    if (!navbar) return;

    function checkScroll() {
      if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    }

    window.addEventListener('scroll', checkScroll, { passive: true });
    checkScroll();
  }


  // ==================================================================
  // 7. PREDICTION FORM (AJAX + Score Picker)
  // ==================================================================
  function initPredictionForms() {
    document.addEventListener('submit', function (e) {
      const form = e.target;
      if (!form.classList.contains('prediction-form')) return;
      if (!form.dataset.ajax) return;

      e.preventDefault();
      const formData = new FormData(form);
      const csrfToken = getCSRFToken();

      fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken,
        },
      })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          showToast(data.message || 'Prediction submitted!', 'success');
          fireConfetti();
          // Update the UI
          const matchCard = form.closest('.match-card');
          if (matchCard) {
            const statusArea = matchCard.querySelector('.prediction-status');
            if (statusArea) {
              statusArea.innerHTML = '<span class="match-predicted-badge"><i class="bi bi-check-circle"></i> Predicted: ' + data.home_score + ' - ' + data.away_score + '</span>';
            }
          }
        } else {
          showToast(data.message || 'Error submitting prediction', 'error');
        }
      })
      .catch(function () {
        showToast('Network error. Please try again.', 'error');
      });
    });

    // Score picker + / - buttons
    document.querySelectorAll('.score-picker').forEach(function (picker) {
      const input = picker.querySelector('input');
      const btnMinus = picker.querySelector('.btn-minus');
      const btnPlus = picker.querySelector('.btn-plus');
      if (!input || !btnMinus || !btnPlus) return;

      btnMinus.addEventListener('click', function () {
        const val = parseInt(input.value) || 0;
        if (val > 0) input.value = val - 1;
      });

      btnPlus.addEventListener('click', function () {
        const val = parseInt(input.value) || 0;
        if (val < 20) input.value = val + 1;
      });
    });
  }


  // ==================================================================
  // 8. TOAST NOTIFICATIONS
  // ==================================================================
  function showToast(message, type) {
    type = type || 'info';
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast-custom ' + type;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(function () {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 300);
    }, 4000);
  }


  // ==================================================================
  // 9. PAGE LOAD ANIMATION
  // ==================================================================
  function initPageLoad() {
    const loadingBar = document.getElementById('loading-bar');
    if (loadingBar) {
      loadingBar.classList.add('active');
      setTimeout(function () {
        loadingBar.classList.add('complete');
        setTimeout(function () {
          loadingBar.classList.remove('active', 'complete');
          loadingBar.style.width = '0';
        }, 500);
      }, 600);
    }
  }


  // ==================================================================
  // 10. GATEWAY INTEGRATION (XTransformPort)
  // ==================================================================
  function initGateway() {
    const PORT = '8000';
    const PARAM = 'XTransformPort';
    const urlParams = new URLSearchParams(window.location.search);
    const isBehindGateway = urlParams.has(PARAM);

    if (!isBehindGateway) return;

    function fixUrl(url) {
      if (!url || url.startsWith('#') || url.startsWith('http') || url.startsWith('mailto') || url.startsWith('tel') || url.startsWith('javascript') || url.startsWith('//')) return url;
      try {
        const urlObj = new URL(url, window.location.origin);
        if (!urlObj.searchParams.has(PARAM) && urlObj.pathname.startsWith('/')) {
          urlObj.searchParams.set(PARAM, PORT);
          return urlObj.pathname + urlObj.search;
        }
      } catch (err) {}
      return url;
    }

    // Fix links on click
    document.addEventListener('click', function (e) {
      const link = e.target.closest('a[href]');
      if (link) {
        const href = link.getAttribute('href');
        const fixed = fixUrl(href);
        if (fixed !== href) link.setAttribute('href', fixed);
      }
    });

    // Fix forms on submit
    document.addEventListener('submit', function (e) {
      const form = e.target;
      if (form.tagName !== 'FORM') return;
      const action = form.getAttribute('action') || window.location.pathname;
      const fixed = fixUrl(action);
      if (fixed !== action) form.setAttribute('action', fixed);
    }, true);

    // Fix fetch
    const originalFetch = window.fetch;
    window.fetch = function (url, options) {
      if (typeof url === 'string') {
        url = fixUrl(url);
      }
      return originalFetch.call(this, url, options);
    };

    // Fix existing links, forms, and images
    function fixAll() {
      document.querySelectorAll('a[href]').forEach(function (link) {
        const href = link.getAttribute('href');
        const fixed = fixUrl(href);
        if (fixed !== href) link.setAttribute('href', fixed);
      });
      document.querySelectorAll('form[action]').forEach(function (form) {
        const action = form.getAttribute('action');
        const fixed = fixUrl(action);
        if (fixed !== action) form.setAttribute('action', fixed);
      });
      // Fix img src attributes to include XTransformPort
      document.querySelectorAll('img[src]').forEach(function (img) {
        const src = img.getAttribute('src');
        const fixed = fixUrl(src);
        if (fixed !== src) img.setAttribute('src', fixed);
      });
      // Fix CSS background-image URLs in style attributes
      document.querySelectorAll('[style*="url("]').forEach(function (el) {
        const style = el.getAttribute('style');
        const fixed = style.replace(/url\(['"]?(\/[^'")\s]+)['"]?\)/g, function(match, url) {
          const fixedUrl = fixUrl(url);
          return match.replace(url, fixedUrl);
        });
        if (fixed !== style) el.setAttribute('style', fixed);
      });
    }

    fixAll();
    const observer = new MutationObserver(fixAll);
    observer.observe(document.body, { childList: true, subtree: true });
  }


  // ==================================================================
  // 11. ADMIN TAB SWITCHING
  // ==================================================================
  function initAdminTabs() {
    const tabs = document.querySelectorAll('.admin-tab');
    const panels = document.querySelectorAll('.admin-panel');

    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        const target = this.dataset.tab;
        tabs.forEach(function (t) { t.classList.remove('active'); });
        panels.forEach(function (p) { p.style.display = 'none'; });
        this.classList.add('active');
        const panel = document.getElementById(target);
        if (panel) panel.style.display = 'block';
      });
    });
  }


  // ==================================================================
  // INITIALIZE EVERYTHING
  // ==================================================================
  function init() {
    initCountdown();
    initNavbar();
    initPredictionForms();
    initPageLoad();
    initGateway();
    initAdminTabs();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
