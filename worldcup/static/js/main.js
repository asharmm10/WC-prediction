/**
 * FIFA World Cup 2026 Family Prediction League — Main JavaScript
 * ================================================================
 * Vanilla JS interactive & animated features for the premium
 * football prediction site. No external libraries required.
 *
 * Features:
 *  1. Countdown Timer with flip animation
 *  2. Confetti Effect
 *  3. Floating Footballs background
 *  4. Stadium Lights Effect
 *  5. Scroll Animations (AOS-like via IntersectionObserver)
 *  6. Navbar Mobile Toggle & active-link highlighting
 *  7. Prediction Form Enhancements (AJAX, auto-save indicator)
 *  8. Toast Notifications
 *  9. Leaderboard Animations
 * 10. Match Card Interactions
 * 11. Login Form Enhancement
 * 12. Page Load Animation
 * 13. Live Match Updates (Polling)
 * 14. Score Picker (+/- buttons)
 * 15. CSRF Token Helper
 */

(function () {
  'use strict';

  // ------------------------------------------------------------------
  // Utility: prefers-reduced-motion check
  // ------------------------------------------------------------------
  const prefersReducedMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches;

  // ------------------------------------------------------------------
  // Utility: Debounce
  // ------------------------------------------------------------------
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

  // ------------------------------------------------------------------
  // CSRF Token Helper
  // ------------------------------------------------------------------
  function getCSRFToken() {
    // Try cookie first
    const cookie = document.cookie
      .split(';')
      .filter(function (c) {
        return c.trim().startsWith('csrftoken=');
      });
    if (cookie.length) return cookie[0].split('=')[1];
    // Fallback to meta tag
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  // ==================================================================
  // 1. COUNTDOWN TIMER
  // ==================================================================
  let countdownInterval = null;

  function initCountdown() {
    const container = document.getElementById('countdown');
    if (!container) return;

    // Build digit boxes if they don't already exist in the markup
    if (!container.querySelector('.countdown-digit')) {
      container.innerHTML = buildCountdownHTML();
    }

    fetchCountdown();

    // Refresh from server every 60 s to stay in sync
    setInterval(fetchCountdown, 60000);

    // Client-side tick every second
    countdownInterval = setInterval(tickCountdown, 1000);
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
        '    <span class="digit-next">00</span>' +
        '  </div>' +
        '  <div class="countdown-label">' + labels[i] + '</div>' +
        '</div>';
      if (i < units.length - 1) {
        html += '<div class="countdown-separator">:</div>';
      }
    });
    return html;
  }

  let countdownSeconds = 0;
  let countdownMatch = '';

  function fetchCountdown() {
    fetch('/api/countdown/', { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        countdownSeconds = data.seconds_remaining || 0;
        countdownMatch = data.match || '';
        renderCountdown(countdownSeconds);
      })
      .catch(function () {
        // Silently fail — client-side tick will keep running
      });
  }

  function tickCountdown() {
    if (countdownSeconds > 0) {
      countdownSeconds -= 1;
    }
    renderCountdown(countdownSeconds);
  }

  function renderCountdown(totalSec) {
    const container = document.getElementById('countdown');
    if (!container) return;

    if (totalSec <= 0) {
      container.innerHTML =
        '<div class="countdown-match-day">MATCH DAY!</div>';
      if (countdownInterval) clearInterval(countdownInterval);
      return;
    }

    const d = Math.floor(totalSec / 86400);
    const h = Math.floor((totalSec % 86400) / 3600);
    const m = Math.floor((totalSec % 3600) / 60);
    const s = totalSec % 60;

    updateDigit('days', pad(d));
    updateDigit('hours', pad(h));
    updateDigit('minutes', pad(m));
    updateDigit('seconds', pad(s));
  }

  function pad(n) {
    return n < 10 ? '0' + n : '' + n;
  }

  /**
   * Flip-style animation: compare current value with new value,
   * animate only when they differ.
   */
  function updateDigit(unit, value) {
    const digitEl = document.querySelector(
      '.countdown-digit[data-unit="' + unit + '"]'
    );
    if (!digitEl) return;

    const current = digitEl.querySelector('.digit-current');
    if (!current) return;

    if (current.textContent !== value) {
      // Add flip class for CSS animation
      digitEl.classList.add('flipping');
      current.textContent = value;
      setTimeout(function () {
        digitEl.classList.remove('flipping');
      }, 300);
    }
  }

  // ==================================================================
  // 2. CONFETTI EFFECT
  // ==================================================================
  function triggerConfetti() {
    if (prefersReducedMotion) return;

    const canvas = document.createElement('canvas');
    canvas.id = 'confetti-canvas';
    canvas.style.cssText =
      'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;';
    document.body.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const colors = [
      '#FFD700', '#FFFFFF', '#F5C518', '#E6C200',
      '#FFF8DC', '#DAA520', '#F0E68C', '#FAFAD2',
      '#C5A028', '#B8860B'
    ];
    const PIECE_COUNT = 150;
    const pieces = [];

    for (let i = 0; i < PIECE_COUNT; i++) {
      pieces.push({
        x: Math.random() * canvas.width,
        y: Math.random() * -canvas.height,          // start above viewport
        w: Math.random() * 8 + 4,
        h: Math.random() * 6 + 3,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        rotSpeed: (Math.random() - 0.5) * 8,
        drift: (Math.random() - 0.5) * 2,
        speed: Math.random() * 3 + 2,
        opacity: Math.random() * 0.5 + 0.5
      });
    }

    let startTime = Date.now();
    const DURATION = 5000; // auto-cleanup after 5 seconds

    function animate() {
      const elapsed = Date.now() - startTime;
      if (elapsed > DURATION) {
        // Fade out
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        document.body.removeChild(canvas);
        return;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Fade pieces in the last second
      const fadeFactor = elapsed > DURATION - 1000
        ? (DURATION - elapsed) / 1000
        : 1;

      for (let i = 0; i < pieces.length; i++) {
        const p = pieces[i];
        p.y += p.speed;
        p.x += p.drift;
        p.rotation += p.rotSpeed;

        // Wrap horizontally
        if (p.x > canvas.width + 20) p.x = -20;
        if (p.x < -20) p.x = canvas.width + 20;

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.globalAlpha = p.opacity * fadeFactor;
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
        ctx.restore();
      }

      requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
  }

  // ==================================================================
  // 3. FLOATING FOOTBALLS
  // ==================================================================
  function initFloatingFootballs() {
    if (prefersReducedMotion) return;

    const container = document.querySelector('.floating-footballs');
    if (!container) {
      // Auto-create a container at the start of body
      const wrapper = document.createElement('div');
      wrapper.className = 'floating-footballs';
      wrapper.setAttribute('aria-hidden', 'true');
      wrapper.style.cssText =
        'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;overflow:hidden;z-index:0;';
      document.body.prepend(wrapper);
    }

    const host = document.querySelector('.floating-footballs');
    const COUNT = 6;

    for (let i = 0; i < COUNT; i++) {
      const ball = document.createElement('div');
      ball.className = 'floating-football';

      const size = Math.random() * 30 + 20;  // 20-50px
      const left = Math.random() * 100;        // 0-100%
      const top = Math.random() * 100;
      const duration = Math.random() * 20 + 30; // 30-50s for parallax
      const delay = Math.random() * -30;
      const opacity = Math.random() * 0.05 + 0.1; // 0.1-0.15

      ball.style.cssText =
        'position:absolute;' +
        'left:' + left + '%;' +
        'top:' + top + '%;' +
        'width:' + size + 'px;' +
        'height:' + size + 'px;' +
        'opacity:' + opacity + ';' +
        'background-image:url("data:image/svg+xml,' + footballSVG() + '");' +
        'background-size:contain;' +
        'background-repeat:no-repeat;' +
        'animation:floatBall ' + duration + 's ' + delay + 's infinite ease-in-out alternate;';

      host.appendChild(ball);
    }

    // Inject the keyframes if not already present
    if (!document.getElementById('floating-football-styles')) {
      const style = document.createElement('style');
      style.id = 'floating-football-styles';
      style.textContent =
        '@keyframes floatBall {' +
        '  0%   { transform: translate(0, 0) rotate(0deg); }' +
        '  25%  { transform: translate(30px, -40px) rotate(90deg); }' +
        '  50%  { transform: translate(-20px, 20px) rotate(180deg); }' +
        '  75%  { transform: translate(40px, 30px) rotate(270deg); }' +
        '  100% { transform: translate(-10px, -20px) rotate(360deg); }' +
        '}';
      document.head.appendChild(style);
    }
  }

  /** Inline SVG data URI for a simple football icon */
  function footballSVG() {
    return encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">' +
        '<circle cx="32" cy="32" r="30" fill="%23fff" stroke="%23333" stroke-width="2"/>' +
        '<path d="M32 2 L38 18 L54 18 L41 28 L46 44 L32 35 L18 44 L23 28 L10 18 L26 18Z" ' +
        'fill="%23333" stroke="%23333" stroke-width="0.5"/>' +
      '</svg>'
    );
  }

  // ==================================================================
  // 4. STADIUM LIGHTS EFFECT
  // ==================================================================
  function initStadiumLights() {
    if (prefersReducedMotion) return;

    const container = document.querySelector('.stadium-lights');
    if (!container) {
      const wrapper = document.createElement('div');
      wrapper.className = 'stadium-lights';
      wrapper.setAttribute('aria-hidden', 'true');
      wrapper.style.cssText =
        'position:fixed;top:0;left:0;width:100%;height:60px;pointer-events:none;z-index:1;overflow:hidden;';
      document.body.prepend(wrapper);
    }

    const host = document.querySelector('.stadium-lights');
    const BEAM_COUNT = 4;

    for (let i = 0; i < BEAM_COUNT; i++) {
      const beam = document.createElement('div');
      beam.className = 'stadium-beam';

      const leftPos = (i + 0.5) * (100 / BEAM_COUNT);
      beam.style.cssText =
        'position:absolute;' +
        'top:0;' +
        'left:' + leftPos + '%;' +
        'width:120px;' +
        'height:300px;' +
        'margin-left:-60px;' +
        'background:linear-gradient(180deg, rgba(255,215,0,0.12) 0%, rgba(255,215,0,0) 100%);' +
        'transform-origin:top center;' +
        'animation:stadiumSweep ' + (6 + i * 2) + 's ease-in-out infinite alternate;' +
        'animation-delay:' + (i * -1.5) + 's;';

      host.appendChild(beam);
    }

    // Inject keyframes
    if (!document.getElementById('stadium-light-styles')) {
      const style = document.createElement('style');
      style.id = 'stadium-light-styles';
      style.textContent =
        '@keyframes stadiumSweep {' +
        '  0%   { transform: rotate(-15deg); opacity: 0.4; }' +
        '  50%  { transform: rotate(0deg);   opacity: 0.7; }' +
        '  100% { transform: rotate(15deg);  opacity: 0.4; }' +
        '}';
      document.head.appendChild(style);
    }
  }

  // ==================================================================
  // 5. SCROLL ANIMATIONS (AOS-like via IntersectionObserver)
  // ==================================================================
  function initScrollAnimations() {
    const elements = document.querySelectorAll('[data-aos]');
    if (!elements.length) return;

    // Map of animation types to their initial & final states
    const animMap = {
      'fade-up':    { init: 'translateY(40px)',  final: 'translateY(0)' },
      'fade-down':  { init: 'translateY(-40px)', final: 'translateY(0)' },
      'fade-left':  { init: 'translateX(-40px)', final: 'translateX(0)' },
      'fade-right': { init: 'translateX(40px)',  final: 'translateX(0)' },
      'zoom-in':    { init: 'scale(0.8)',        final: 'scale(1)' },
      'fade':       { init: 'none',              final: 'none' }
    };

    // Set initial hidden state
    elements.forEach(function (el) {
      const type = el.getAttribute('data-aos') || 'fade-up';
      const map = animMap[type] || animMap['fade-up'];

      el.style.opacity = '0';
      if (map.init !== 'none') {
        el.style.transform = map.init;
      }
      el.style.transition =
        'opacity 0.6s ease, transform 0.6s ease';
    });

    if (prefersReducedMotion) {
      // Show everything immediately
      elements.forEach(function (el) { el.style.opacity = '1'; el.style.transform = 'none'; });
      return;
    }

    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;

          const el = entry.target;
          const delay = parseInt(el.getAttribute('data-aos-delay') || '0', 10);
          const type = el.getAttribute('data-aos') || 'fade-up';
          const map = animMap[type] || animMap['fade-up'];

          setTimeout(function () {
            el.style.opacity = '1';
            if (map.final !== 'none') {
              el.style.transform = map.final;
            }
            el.classList.add('aos-animate');
          }, delay);

          observer.unobserve(el);
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );

    elements.forEach(function (el) { observer.observe(el); });
  }

  // ==================================================================
  // 6. NAVBAR MOBILE TOGGLE
  // ==================================================================
  function initNavbar() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    const toggler = navbar.querySelector('.navbar-toggler');
    const collapse = navbar.querySelector('.navbar-collapse');
    if (!toggler || !collapse) return;

    // Toggle on button click
    toggler.addEventListener('click', function () {
      collapse.classList.toggle('show');
      toggler.setAttribute(
        'aria-expanded',
        collapse.classList.contains('show')
      );
    });

    // Close on outside click
    document.addEventListener('click', function (e) {
      if (
        collapse.classList.contains('show') &&
        !collapse.contains(e.target) &&
        !toggler.contains(e.target)
      ) {
        collapse.classList.remove('show');
        toggler.setAttribute('aria-expanded', 'false');
      }
    });

    // Close on nav-link click (for single-page sections)
    const navLinks = collapse.querySelectorAll('.nav-link');
    navLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        collapse.classList.remove('show');
        toggler.setAttribute('aria-expanded', 'false');
      });
    });

    // Smooth scroll for hash links
    navLinks.forEach(function (link) {
      const href = link.getAttribute('href');
      if (href && href.startsWith('#') && href.length > 1) {
        link.addEventListener('click', function (e) {
          const target = document.querySelector(href);
          if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
          }
        });
      }
    });

    // Active link highlighting based on scroll position
    const sections = document.querySelectorAll('section[id]');
    if (sections.length) {
      const handleScroll = debounce(function () {
        const scrollY = window.scrollY + 100;
        sections.forEach(function (section) {
          const top = section.offsetTop;
          const height = section.offsetHeight;
          const id = section.getAttribute('id');
          const link = navbar.querySelector('.nav-link[href="#' + id + '"]');
          if (link) {
            if (scrollY >= top && scrollY < top + height) {
              link.classList.add('active');
            } else {
              link.classList.remove('active');
            }
          }
        });
      }, 50);

      window.addEventListener('scroll', handleScroll, { passive: true });
    }
  }

  // ==================================================================
  // 7. PREDICTION FORM ENHANCEMENTS
  // ==================================================================
  function initPredictionForms() {
    const forms = document.querySelectorAll('.prediction-form');
    if (!forms.length) return;

    forms.forEach(function (form) {
      const matchId = form.getAttribute('data-match-id');
      const isLocked = form.classList.contains('locked');

      if (isLocked) {
        disableForm(form);
        return;
      }

      // AJAX form submission
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        submitPredictionForm(form, matchId);
      });

      // Auto-save indicator
      const inputs = form.querySelectorAll('input[type="number"]');
      let autoSaveTimer = null;
      inputs.forEach(function (input) {
        input.addEventListener('input', function () {
          clearTimeout(autoSaveTimer);
          showAutoSaveIndicator(form, 'typing...');
          autoSaveTimer = setTimeout(function () {
            showAutoSaveIndicator(form, 'auto-saving...');
            submitPredictionForm(form, matchId, true);
          }, 2000);
        });
      });
    });
  }

  function submitPredictionForm(form, matchId, isAutoSave) {
    const formData = new FormData(form);
    formData.append('csrfmiddlewaretoken', getCSRFToken());

    const url = form.getAttribute('action') ||
      '/predict/' + matchId + '/';

    fetch(url, {
      method: 'POST',
      body: formData,
      credentials: 'same-origin',
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
      .then(function (res) {
        if (res.ok) {
          return res.json().catch(function () {
            // Server may return a redirect (non-JSON) on success
            return { success: true };
          });
        }
        throw new Error('Server returned ' + res.status);
      })
      .then(function (data) {
        if (isAutoSave) {
          showAutoSaveIndicator(form, 'saved');
        } else {
          showToast('Prediction saved!', 'success');
        }
        // Brief green flash on form
        form.classList.add('form-saved');
        setTimeout(function () {
          form.classList.remove('form-saved');
        }, 1000);
      })
      .catch(function (err) {
        if (isAutoSave) {
          showAutoSaveIndicator(form, 'save failed');
        } else {
          showToast('Error saving prediction. Please try again.', 'error');
        }
      });
  }

  function showAutoSaveIndicator(form, text) {
    let indicator = form.querySelector('.auto-save-indicator');
    if (!indicator) {
      indicator = document.createElement('span');
      indicator.className = 'auto-save-indicator';
      indicator.style.cssText =
        'font-size:0.75rem;color:#888;margin-left:8px;transition:color 0.3s;';
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.parentNode.insertBefore(indicator, submitBtn.nextSibling);
      } else {
        form.appendChild(indicator);
      }
    }
    indicator.textContent = text;
    if (text === 'saved') {
      indicator.style.color = '#28a745';
    } else if (text === 'save failed') {
      indicator.style.color = '#dc3545';
    } else {
      indicator.style.color = '#888';
    }
  }

  function disableForm(form) {
    const inputs = form.querySelectorAll('input, button, select, textarea');
    inputs.forEach(function (el) {
      el.disabled = true;
    });
    form.classList.add('form-locked');

    // Add lock overlay
    const overlay = document.createElement('div');
    overlay.className = 'lock-overlay';
    overlay.innerHTML =
      '<span class="lock-icon" aria-hidden="true">&#128274;</span>' +
      '<span class="lock-text">Predictions locked</span>';
    overlay.style.cssText =
      'position:absolute;top:0;left:0;right:0;bottom:0;display:flex;' +
      'flex-direction:column;align-items:center;justify-content:center;' +
      'background:rgba(0,0,0,0.5);border-radius:8px;z-index:5;color:#fff;';
    form.style.position = 'relative';
    form.appendChild(overlay);
  }

  // ==================================================================
  // 8. TOAST NOTIFICATIONS
  // ==================================================================
  let toastContainer = null;

  function ensureToastContainer() {
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toast-container';
      toastContainer.style.cssText =
        'position:fixed;top:20px;right:20px;z-index:10000;display:flex;' +
        'flex-direction:column;gap:10px;pointer-events:none;';
      document.body.appendChild(toastContainer);
    }
    return toastContainer;
  }

  function showToast(message, type) {
    type = type || 'success';
    const container = ensureToastContainer();

    const colorMap = {
      success: { bg: '#1a1a2e', border: '#FFD700', text: '#FFD700', icon: '\u2705' },
      error:   { bg: '#1a1a2e', border: '#dc3545', text: '#dc3545', icon: '\u274C' },
      warning: { bg: '#1a1a2e', border: '#ffc107', text: '#ffc107', icon: '\u26A0\uFE0F' },
      info:    { bg: '#1a1a2e', border: '#17a2b8', text: '#17a2b8', icon: '\u2139\uFE0F' }
    };

    const colors = colorMap[type] || colorMap.success;

    const toast = document.createElement('div');
    toast.className = 'toast-notification toast-' + type;
    toast.style.cssText =
      'pointer-events:auto;padding:12px 20px;border-radius:8px;' +
      'background:' + colors.bg + ';border-left:4px solid ' + colors.border + ';' +
      'color:' + colors.text + ';font-size:0.9rem;max-width:360px;' +
      'box-shadow:0 4px 20px rgba(0,0,0,0.3);cursor:pointer;' +
      'transform:translateX(120%);transition:transform 0.4s ease,opacity 0.4s ease;' +
      'display:flex;align-items:center;gap:8px;';
    toast.innerHTML =
      '<span class="toast-icon">' + colors.icon + '</span>' +
      '<span class="toast-message">' + message + '</span>';

    // Slide in
    container.appendChild(toast);
    requestAnimationFrame(function () {
      toast.style.transform = 'translateX(0)';
    });

    // Auto-dismiss after 4 seconds
    const dismissTimer = setTimeout(function () {
      dismissToast(toast);
    }, 4000);

    // Manual dismiss on click
    toast.addEventListener('click', function () {
      clearTimeout(dismissTimer);
      dismissToast(toast);
    });
  }

  function dismissToast(toast) {
    toast.style.transform = 'translateX(120%)';
    toast.style.opacity = '0';
    setTimeout(function () {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 400);
  }

  // ==================================================================
  // 9. LEADERBOARD ANIMATIONS
  // ==================================================================
  function initLeaderboard() {
    const board = document.querySelector('.leaderboard');
    if (!board) return;

    const rows = board.querySelectorAll('.leaderboard-row');
    if (!rows.length) return;

    if (prefersReducedMotion) {
      rows.forEach(function (row) { row.style.opacity = '1'; });
      return;
    }

    // Staggered entry animation
    rows.forEach(function (row, index) {
      row.style.opacity = '0';
      row.style.transform = 'translateX(-30px)';
      row.style.transition = 'opacity 0.5s ease, transform 0.5s ease';

      setTimeout(function () {
        row.style.opacity = '1';
        row.style.transform = 'translateX(0)';
        row.classList.add('visible');
      }, 100 + index * 80);
    });

    // Number counting animation for points
    rows.forEach(function (row) {
      const pointsEl = row.querySelector('.points-value');
      if (!pointsEl) return;

      const targetValue = parseInt(pointsEl.textContent, 10);
      if (isNaN(targetValue) || targetValue === 0) return;

      animateCounter(pointsEl, 0, targetValue, 1200);
    });

    // Trophy animation for #1
    const firstRow = rows[0];
    if (firstRow) {
      const trophy = firstRow.querySelector('.trophy-icon');
      if (trophy) {
        trophy.classList.add('trophy-bounce');
      }
    }

    // Medal shine for top 3
    for (let i = 0; i < Math.min(3, rows.length); i++) {
      const medal = rows[i].querySelector('.medal');
      if (medal) {
        medal.classList.add('medal-shine');
      }
    }
  }

  /**
   * Animate a numeric counter from start to end over the given duration.
   */
  function animateCounter(el, start, end, duration) {
    const startTime = performance.now();

    function step(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(start + (end - start) * eased);
      el.textContent = current;
      if (progress < 1) {
        requestAnimationFrame(step);
      }
    }

    requestAnimationFrame(step);
  }

  // Inject leaderboard-specific animations
  (function injectLeaderboardStyles() {
    if (document.getElementById('leaderboard-anim-styles')) return;
    const style = document.createElement('style');
    style.id = 'leaderboard-anim-styles';
    style.textContent =
      '@keyframes trophyBounce {' +
      '  0%, 100% { transform: scale(1); }' +
      '  50%      { transform: scale(1.25) rotate(-5deg); }' +
      '}' +
      '.trophy-bounce { animation: trophyBounce 1.5s ease-in-out infinite; }' +
      '@keyframes medalShine {' +
      '  0%   { background-position: -100px 0; }' +
      '  100% { background-position: 200px 0; }' +
      '}' +
      '.medal-shine {' +
      '  background-image: linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.4) 50%, transparent 70%);' +
      '  background-size: 200px 100%;' +
      '  animation: medalShine 3s ease-in-out infinite;' +
      '}';
    document.head.appendChild(style);
  })();

  // ==================================================================
  // 10. MATCH CARD INTERACTIONS
  // ==================================================================
  function initMatchCards() {
    const cards = document.querySelectorAll('.match-card');
    if (!cards.length) return;

    cards.forEach(function (card) {
      // Hover tilt/glow effect
      if (!prefersReducedMotion) {
        card.addEventListener('mousemove', function (e) {
          const rect = card.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;
          const centerX = rect.width / 2;
          const centerY = rect.height / 2;

          const rotateX = ((y - centerY) / centerY) * -4; // subtle tilt
          const rotateY = ((x - centerX) / centerX) * 4;

          card.style.transform =
            'perspective(600px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg)';
          card.classList.add('card-hover');
        });

        card.addEventListener('mouseleave', function () {
          card.style.transform = '';
          card.classList.remove('card-hover');
        });
      }

      // Click to expand prediction form
      const expandBtn = card.querySelector('.expand-prediction');
      const predForm = card.querySelector('.prediction-form-wrapper');
      if (expandBtn && predForm) {
        expandBtn.addEventListener('click', function () {
          predForm.classList.toggle('expanded');
          expandBtn.setAttribute(
            'aria-expanded',
            predForm.classList.contains('expanded')
          );
        });
      }

      // Status badge pulse for live matches
      if (card.classList.contains('match-live')) {
        const badge = card.querySelector('.match-status-badge');
        if (badge) badge.classList.add('pulse-live');
      }

      // Lock animation when match is expired
      if (card.classList.contains('match-locked')) {
        card.classList.add('locked-animate');
      }
    });

    // Inject match-card styles
    if (!document.getElementById('match-card-anim-styles')) {
      const style = document.createElement('style');
      style.id = 'match-card-anim-styles';
      style.textContent =
        '.match-card { transition: transform 0.2s ease, box-shadow 0.2s ease; }' +
        '.card-hover { box-shadow: 0 8px 30px rgba(255,215,0,0.15) !important; }' +
        '@keyframes pulseLive {' +
        '  0%, 100% { opacity: 1; transform: scale(1); }' +
        '  50%      { opacity: 0.6; transform: scale(1.1); }' +
        '}' +
        '.pulse-live { animation: pulseLive 1.5s ease-in-out infinite; }' +
        '.prediction-form-wrapper { max-height:0;overflow:hidden;transition:max-height 0.4s ease; }' +
        '.prediction-form-wrapper.expanded { max-height:400px; }' +
        '@keyframes lockShake {' +
        '  0%, 100% { transform: rotate(0); }' +
        '  25%      { transform: rotate(-3deg); }' +
        '  75%      { transform: rotate(3deg); }' +
        '}' +
        '.locked-animate { animation: lockShake 0.4s ease; }';
      document.head.appendChild(style);
    }
  }

  // ==================================================================
  // 11. LOGIN FORM ENHANCEMENT
  // ==================================================================
  function initLoginForm() {
    const form = document.querySelector('.login-form');
    if (!form) return;

    // Secret code show/hide toggle
    const secretInput = form.querySelector('input[name="secret_code"]');
    if (secretInput) {
      const toggleBtn = document.createElement('button');
      toggleBtn.type = 'button';
      toggleBtn.className = 'secret-toggle';
      toggleBtn.innerHTML = '&#128065;'; // eye emoji
      toggleBtn.setAttribute('aria-label', 'Toggle secret code visibility');
      toggleBtn.style.cssText =
        'position:absolute;right:10px;top:50%;transform:translateY(-50%);' +
        'background:none;border:none;cursor:pointer;font-size:1.1rem;color:#888;';

      const wrapper = document.createElement('div');
      wrapper.style.position = 'relative';
      secretInput.parentNode.insertBefore(wrapper, secretInput);
      wrapper.appendChild(secretInput);
      wrapper.appendChild(toggleBtn);

      toggleBtn.addEventListener('click', function () {
        if (secretInput.type === 'password') {
          secretInput.type = 'text';
          toggleBtn.innerHTML = '&#128064;'; // eye-with-line emoji
        } else {
          secretInput.type = 'password';
          toggleBtn.innerHTML = '&#128065;';
        }
      });
    }

    // Loading state on submit
    form.addEventListener('submit', function () {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.dataset.originalText = btn.textContent;
        btn.innerHTML =
          '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ' +
          'Signing in...';
      }
    });

    // Error shake — triggered if .login-error is present
    const errorEl = form.querySelector('.login-error');
    if (errorEl) {
      form.classList.add('shake');
      setTimeout(function () {
        form.classList.remove('shake');
      }, 600);
    }

    // Success celebration
    const successEl = form.querySelector('.login-success');
    if (successEl) {
      setTimeout(triggerConfetti, 300);
    }

    // Inject login styles
    if (!document.getElementById('login-anim-styles')) {
      const style = document.createElement('style');
      style.id = 'login-anim-styles';
      style.textContent =
        '@keyframes shakeForm {' +
        '  0%, 100% { transform: translateX(0); }' +
        '  10%, 30%, 50%, 70%, 90% { transform: translateX(-6px); }' +
        '  20%, 40%, 60%, 80% { transform: translateX(6px); }' +
        '}' +
        '.shake { animation: shakeForm 0.5s ease; }';
      document.head.appendChild(style);
    }
  }

  // ==================================================================
  // 12. PAGE LOAD ANIMATION
  // ==================================================================
  function initPageLoad() {
    // Loading bar at top
    const bar = document.createElement('div');
    bar.id = 'page-load-bar';
    bar.style.cssText =
      'position:fixed;top:0;left:0;height:3px;width:0;z-index:9999;' +
      'background:linear-gradient(90deg, #FFD700, #F5C518);transition:width 0.4s ease;';
    document.body.appendChild(bar);

    // Animate bar
    requestAnimationFrame(function () { bar.style.width = '60%'; });

    window.addEventListener('load', function () {
      bar.style.width = '100%';
      setTimeout(function () {
        bar.style.opacity = '0';
        setTimeout(function () {
          if (bar.parentNode) bar.parentNode.removeChild(bar);
        }, 300);
      }, 200);
    });

    // Fade in page content
    const main = document.querySelector('main') || document.querySelector('.main-content');
    if (main) {
      main.style.opacity = '0';
      main.style.transition = 'opacity 0.6s ease';
      requestAnimationFrame(function () {
        main.style.opacity = '1';
      });
    }

    // Stagger navbar items
    const navItems = document.querySelectorAll('.navbar .nav-item');
    navItems.forEach(function (item, i) {
      item.style.opacity = '0';
      item.style.transform = 'translateY(-10px)';
      item.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      setTimeout(function () {
        item.style.opacity = '1';
        item.style.transform = 'translateY(0)';
      }, 150 + i * 80);
    });

    // Hero section special entrance
    const hero = document.querySelector('.hero');
    if (hero && !prefersReducedMotion) {
      hero.style.opacity = '0';
      hero.style.transform = 'translateY(30px)';
      hero.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
      setTimeout(function () {
        hero.style.opacity = '1';
        hero.style.transform = 'translateY(0)';
      }, 300);
    }
  }

  // ==================================================================
  // 13. LIVE MATCH UPDATES (POLLING)
  // ==================================================================
  let liveUpdateInterval = null;

  function initLiveUpdates() {
    // Poll every 60 seconds
    liveUpdateInterval = setInterval(pollLiveUpdates, 60000);
    // Also poll once after 5 seconds to catch up on initial load
    setTimeout(pollLiveUpdates, 5000);
  }

  function pollLiveUpdates() {
    fetch('/api/countdown/', { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        // Update countdown if present
        if (data.seconds_remaining !== undefined) {
          countdownSeconds = data.seconds_remaining;
          countdownMatch = data.match || '';
        }

        // Update match cards on the page
        updateMatchCardsFromServer();
      })
      .catch(function () {
        // Silent failure
      });
  }

  function updateMatchCardsFromServer() {
    // Fetch the current page's match data via a lightweight API
    // We'll parse the matches page HTML to detect changes
    // A more robust solution would use a dedicated JSON API,
    // but we work with what we have.
    const matchCards = document.querySelectorAll('.match-card[data-match-id]');
    if (!matchCards.length) return;

    // For each visible match card, fetch its detail via AJAX
    matchCards.forEach(function (card) {
      const matchId = card.getAttribute('data-match-id');
      fetch('/match/' + matchId + '/', {
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(function (res) {
          if (!res.ok) return null;
          return res.text();
        })
        .then(function (html) {
          if (!html) return;

          // Parse the returned HTML to extract status & scores
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, 'text/html');

          // Update status badge
          const newStatus = doc.querySelector('.match-status-badge');
          const oldStatus = card.querySelector('.match-status-badge');
          if (newStatus && oldStatus) {
            const newStatusText = newStatus.textContent.trim();
            const oldStatusText = oldStatus.textContent.trim();
            if (newStatusText !== oldStatusText) {
              oldStatus.textContent = newStatus.textContent;
              oldStatus.className = newStatus.className;

              // Notify user
              if (newStatusText.toLowerCase() === 'live') {
                showToast('A match has gone LIVE!', 'info');
                oldStatus.classList.add('pulse-live');
              } else if (newStatusText.toLowerCase() === 'completed') {
                showToast('Match result is in!', 'success');
              }

              // Update card classes
              card.classList.remove('match-upcoming', 'match-live', 'match-completed');
              card.classList.add('match-' + newStatusText.toLowerCase());
            }
          }

          // Update scores
          const newHomeScore = doc.querySelector('.home-score');
          const newAwayScore = doc.querySelector('.away-score');
          if (newHomeScore && newAwayScore) {
            const oldHome = card.querySelector('.home-score');
            const oldAway = card.querySelector('.away-score');
            if (oldHome && oldAway) {
              if (oldHome.textContent !== newHomeScore.textContent ||
                  oldAway.textContent !== newAwayScore.textContent) {
                oldHome.textContent = newHomeScore.textContent;
                oldAway.textContent = newAwayScore.textContent;
                oldHome.classList.add('score-updated');
                oldAway.classList.add('score-updated');
                setTimeout(function () {
                  oldHome.classList.remove('score-updated');
                  oldAway.classList.remove('score-updated');
                }, 2000);
              }
            }
          }

          // Recalculate leaderboard if on that page
          const leaderboardPage = document.querySelector('.leaderboard');
          if (leaderboardPage) {
            refreshLeaderboard();
          }
        })
        .catch(function () {
          // Silent
        });
    });
  }

  function refreshLeaderboard() {
    fetch('/leaderboard/', {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (res) { return res.text(); })
      .then(function (html) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newBoard = doc.querySelector('.leaderboard');
        const oldBoard = document.querySelector('.leaderboard');
        if (newBoard && oldBoard) {
          // Check for position changes
          const oldRows = oldBoard.querySelectorAll('.leaderboard-row');
          const newRows = newBoard.querySelectorAll('.leaderboard-row');

          oldRows.forEach(function (oldRow, idx) {
            if (newRows[idx]) {
              const oldPoints = oldRow.querySelector('.points-value');
              const newPoints = newRows[idx].querySelector('.points-value');
              if (oldPoints && newPoints) {
                if (oldPoints.textContent !== newPoints.textContent) {
                  oldPoints.textContent = newPoints.textContent;
                  oldRow.classList.add('position-changed');
                  setTimeout(function () {
                    oldRow.classList.remove('position-changed');
                  }, 3000);
                }
              }
            }
          });
        }
      })
      .catch(function () {
        // Silent
      });
  }

  // Inject live-update styles
  (function injectLiveUpdateStyles() {
    if (document.getElementById('live-update-styles')) return;
    const style = document.createElement('style');
    style.id = 'live-update-styles';
    style.textContent =
      '@keyframes scoreFlash {' +
      '  0%   { color: #FFD700; transform: scale(1.3); }' +
      '  100% { color: inherit; transform: scale(1); }' +
      '}' +
      '.score-updated { animation: scoreFlash 0.6s ease; }' +
      '.position-changed { background: rgba(255,215,0,0.1) !important; transition: background 0.5s ease; }';
    document.head.appendChild(style);
  })();

  // ==================================================================
  // 14. SCORE PICKER (Number Wheel / +/- Buttons)
  // ==================================================================
  function initScorePicker() {
    const inputs = document.querySelectorAll(
      '.prediction-form input[type="number"][name$="_score"]'
    );
    if (!inputs.length) return;

    inputs.forEach(function (input) {
      // Skip if already enhanced
      if (input.parentNode.classList.contains('score-picker')) return;

      const maxVal = parseInt(input.getAttribute('max') || '20', 10);
      const minVal = parseInt(input.getAttribute('min') || '0', 10);

      // Wrapper
      const wrapper = document.createElement('div');
      wrapper.className = 'score-picker';
      wrapper.style.cssText =
        'display:inline-flex;align-items:center;gap:4px;';

      // Minus button
      const minusBtn = document.createElement('button');
      minusBtn.type = 'button';
      minusBtn.className = 'score-btn score-btn-minus';
      minusBtn.innerHTML = '&minus;';
      minusBtn.setAttribute('aria-label', 'Decrease score');
      minusBtn.style.cssText =
        'width:36px;height:36px;border-radius:50%;border:2px solid #FFD700;' +
        'background:transparent;color:#FFD700;font-size:1.2rem;cursor:pointer;' +
        'display:flex;align-items:center;justify-content:center;transition:all 0.2s ease;';

      // Plus button
      const plusBtn = document.createElement('button');
      plusBtn.type = 'button';
      plusBtn.className = 'score-btn score-btn-plus';
      plusBtn.innerHTML = '&plus;';
      plusBtn.setAttribute('aria-label', 'Increase score');
      plusBtn.style.cssText =
        'width:36px;height:36px;border-radius:50%;border:2px solid #FFD700;' +
        'background:transparent;color:#FFD700;font-size:1.2rem;cursor:pointer;' +
        'display:flex;align-items:center;justify-content:center;transition:all 0.2s ease;';

      // Style the input
      input.style.cssText =
        'width:50px;height:50px;text-align:center;font-size:1.5rem;font-weight:bold;' +
        'border:2px solid #333;border-radius:8px;background:#1a1a2e;color:#FFD700;' +
        'transition:transform 0.15s ease;-moz-appearance:textfield;';
      input.classList.add('score-input');

      // Remove spinner arrows
      const arrowStyle = document.createElement('style');
      arrowStyle.textContent =
        '.score-input::-webkit-inner-spin-button,' +
        '.score-input::-webkit-outer-spin-button { -webkit-appearance:none;margin:0; }';
      if (!document.getElementById('score-picker-arrow-fix')) {
        arrowStyle.id = 'score-picker-arrow-fix';
        document.head.appendChild(arrowStyle);
      }

      // Wrap the input
      input.parentNode.insertBefore(wrapper, input);
      wrapper.appendChild(minusBtn);
      wrapper.appendChild(input);
      wrapper.appendChild(plusBtn);

      // Event handlers
      function updateValue(delta) {
        let val = parseInt(input.value, 10);
        if (isNaN(val)) val = 0;
        val = Math.max(minVal, Math.min(maxVal, val + delta));
        input.value = val;

        // Scale animation
        input.style.transform = 'scale(1.2)';
        setTimeout(function () {
          input.style.transform = 'scale(1)';
        }, 150);

        // Trigger input event for auto-save
        input.dispatchEvent(new Event('input', { bubbles: true }));

        // Haptic feedback
        if (navigator.vibrate) {
          navigator.vibrate(10);
        }
      }

      minusBtn.addEventListener('click', function () {
        updateValue(-1);
        minusBtn.style.background = 'rgba(255,215,0,0.2)';
        setTimeout(function () { minusBtn.style.background = 'transparent'; }, 150);
      });

      plusBtn.addEventListener('click', function () {
        updateValue(1);
        plusBtn.style.background = 'rgba(255,215,0,0.2)';
        setTimeout(function () { plusBtn.style.background = 'transparent'; }, 150);
      });

      // Hover effects
      [minusBtn, plusBtn].forEach(function (btn) {
        btn.addEventListener('mouseenter', function () {
          btn.style.background = 'rgba(255,215,0,0.15)';
          btn.style.transform = 'scale(1.1)';
        });
        btn.addEventListener('mouseleave', function () {
          btn.style.background = 'transparent';
          btn.style.transform = 'scale(1)';
        });
      });
    });
  }

  // ==================================================================
  // 15. INITIALIZATION
  // ==================================================================
  document.addEventListener('DOMContentLoaded', function () {
    initPageLoad();
    initNavbar();
    initCountdown();
    initFloatingFootballs();
    initStadiumLights();
    initScrollAnimations();
    initPredictionForms();
    initScorePicker();
    initMatchCards();
    initLeaderboard();
    initLoginForm();
    initLiveUpdates();

    // Trigger confetti if there's a celebration flag in the page
    if (document.querySelector('.celebrate')) {
      setTimeout(triggerConfetti, 500);
    }
  });

  // Expose showToast globally for use in inline scripts or other modules
  window.showToast = showToast;
  window.triggerConfetti = triggerConfetti;
})();
