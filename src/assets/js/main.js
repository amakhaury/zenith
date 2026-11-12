/* ZENITH — скрипты лендинга. Без зависимостей. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;

  /* ---------- Мобильное меню ---------- */
  var menu = d.getElementById('menu');
  var openBtn = d.querySelector('[data-menu-open]');
  var closeBtn = d.querySelector('[data-menu-close]');
  function setMenu(open) {
    if (!menu) return;
    if (open) { menu.hidden = false; requestAnimationFrame(function () { menu.classList.add('is-open'); }); }
    else { menu.classList.remove('is-open'); setTimeout(function () { if (!menu.classList.contains('is-open')) menu.hidden = true; }, 260); }
    openBtn && openBtn.setAttribute('aria-expanded', String(open));
    root.style.overflow = open ? 'hidden' : '';
    if (open) { closeBtn && closeBtn.focus(); } else { openBtn && openBtn.focus({ preventScroll: true }); }
  }
  openBtn && openBtn.addEventListener('click', function () { setMenu(true); });
  closeBtn && closeBtn.addEventListener('click', function () { setMenu(false); });
  menu && menu.addEventListener('click', function (e) { if (e.target.closest('a[href^="#"]')) setMenu(false); });
  d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && menu && !menu.hidden) setMenu(false); });

  /* ---------- Активный пункт навигации ---------- */
  var navLinks = [].slice.call(d.querySelectorAll('.nav__link'));
  if ('IntersectionObserver' in window && navLinks.length) {
    var map = {};
    navLinks.forEach(function (a) { var s = d.querySelector(a.getAttribute('href')); if (s) map[s.id] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var link = map[en.target.id];
        if (!link) return;
        if (en.isIntersecting) { navLinks.forEach(function (l) { l.removeAttribute('aria-current'); }); link.setAttribute('aria-current', 'true'); }
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    Object.keys(map).forEach(function (id) { io.observe(d.getElementById(id)); });
  }

  /* ---------- Появление при прокрутке ---------- */
  var reveal = d.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var ro = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('is-visible'); ro.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
    reveal.forEach(function (el) { ro.observe(el); });
  } else {
    reveal.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* ---------- Карусель услуг: перетаскивание мышью ---------- */
  var scroller = d.querySelector('[data-drag-scroll]');
  if (scroller) {
    var down = false, startX = 0, startLeft = 0, moved = 0;
    scroller.addEventListener('pointerdown', function (e) {
      if (e.pointerType !== 'mouse' || e.button !== 0) return;
      down = true; moved = 0; startX = e.clientX; startLeft = scroller.scrollLeft;
    });
    window.addEventListener('pointermove', function (e) {
      if (!down) return;
      var dx = e.clientX - startX;
      moved = Math.max(moved, Math.abs(dx));
      if (moved > 5) { scroller.classList.add('is-dragging'); scroller.scrollLeft = startLeft - dx; }
    });
    window.addEventListener('pointerup', function () {
      if (!down) return;
      down = false;
      setTimeout(function () { scroller.classList.remove('is-dragging'); }, 0);
    });
    scroller.addEventListener('click', function (e) { if (moved > 5) { e.preventDefault(); e.stopPropagation(); } }, true);
    scroller.addEventListener('dragstart', function (e) { e.preventDefault(); });
  }

  /* ---------- Цели Метрики ---------- */
  function goal(name) { try { if (window.ym && root.dataset.metrika) window.ym(+root.dataset.metrika, 'reachGoal', name); } catch (e) {} }
  d.querySelectorAll('[data-goal]').forEach(function (a) {
    a.addEventListener('click', function () { goal(a.getAttribute('data-goal')); });
  });

  /* ---------- Заявка → WhatsApp ---------- */
  var form = d.querySelector('[data-form]');
  if (form) {
    var nameI = form.querySelector('#f-name'), serviceI = form.querySelector('#f-service'), textI = form.querySelector('#f-text');
    var statusEl = form.querySelector('.form__status');
    var wa = form.getAttribute('data-wa'), contact = form.getAttribute('data-contact'), brand = form.getAttribute('data-brand');

    // выбор услуги в карусели → подставляем в заявку
    d.querySelectorAll('[data-service]').forEach(function (a) {
      a.addEventListener('click', function () {
        var v = a.getAttribute('data-service');
        [].forEach.call(serviceI.options, function (o) { if (o.value === v || o.text === v) serviceI.value = o.value || o.text; });
        setTimeout(function () { nameI.focus({ preventScroll: true }); }, 600);
      });
    });

    var errEl = d.getElementById('f-name-err');
    nameI.addEventListener('input', function () { nameI.removeAttribute('aria-invalid'); errEl.textContent = ''; });

    function buildText() {
      var lines = ['Здравствуйте' + (contact ? ', ' + contact : '') + '! Заявка с сайта ' + brand + '.'];
      lines.push('Имя: ' + nameI.value.trim().replace(/\s+/g, ' '));
      if (serviceI.value) lines.push('Услуга: ' + serviceI.value);
      var t = textI.value.trim();
      if (t) lines.push('Сообщение: ' + t);
      return lines.join('\n');
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      statusEl.textContent = '';
      if (nameI.value.trim().length < 2) {
        nameI.setAttribute('aria-invalid', 'true'); errEl.textContent = 'Укажите имя'; nameI.focus(); return;
      }
      var url = 'https://wa.me/' + wa + '?text=' + encodeURIComponent(buildText());
      goal('lead_wa');
      // на телефоне — переход в приложение, на компьютере — новая вкладка (WhatsApp Web / Desktop)
      var mobile = matchMedia('(hover: none) and (pointer: coarse)').matches;
      var win = mobile ? null : window.open(url, '_blank'); // с 'noopener' open() всегда возвращает null
      if (win) { try { win.opener = null; } catch (err) {} } else location.href = url;
      statusEl.innerHTML = 'Если WhatsApp не открылся, <a href="' + url + '" target="_blank" rel="noopener">нажмите здесь</a>.';
    });
  }
  /* ---------- Яндекс Метрика: только после согласия ---------- */
  var mid = root.dataset.metrika;
  var banner = d.getElementById('cookie');
  function loadMetrika() {
    if (!mid || window.ym) return;
    (function (m, e, t, r, i, k, a) { m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); }; m[i].l = 1 * new Date(); k = e.createElement(t), a = e.getElementsByTagName(t)[0], k.async = 1, k.src = r, a.parentNode.insertBefore(k, a); })(window, d, 'script', 'https://mc.yandex.ru/metrika/tag.js', 'ym');
    window.ym(+mid, 'init', { clickmap: true, trackLinks: true, accurateTrackBounce: true, webvisor: false });
  }
  if (mid && banner) {
    var choice = null;
    try { choice = localStorage.getItem('zx-consent'); } catch (e) {}
    if (choice === '1') loadMetrika();
    else if (choice !== '0') banner.hidden = false;
    banner.addEventListener('click', function (e) {
      var b = e.target.closest('[data-cookie]');
      if (!b) return;
      var v = b.getAttribute('data-cookie');
      try { localStorage.setItem('zx-consent', v); } catch (err) {}
      banner.hidden = true;
      if (v === '1') loadMetrika();
    });
  }
})();
