/* İnsanlık Eli — small enhancements. The site works without this file. */
(function () {
  var doc = document;

  // remember the chosen language for the next visit to the home address
  try { localStorage.setItem('lang', doc.documentElement.lang); } catch (e) {}

  // header shadow when scrolled
  var header = doc.querySelector('.site-header');
  var onScroll = function () { if (header) header.classList.toggle('scrolled', window.scrollY > 8); };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // mobile menu
  var toggle = doc.querySelector('.menu-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = doc.body.classList.toggle('menu-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    doc.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && doc.body.classList.contains('menu-open')) {
        doc.body.classList.remove('menu-open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.focus();
      }
    });
  }

  // count-up numbers (the final number is already in the page)
  var counts = doc.querySelectorAll('.count[data-to]');
  if (counts.length && 'IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var sep = doc.documentElement.lang === 'tr' ? '.' : ',';
    var fmt = function (n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, sep); };
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        io.unobserve(en.target);
        var el = en.target, to = parseInt(el.getAttribute('data-to'), 10) || 0, t0 = null, dur = 1400;
        var step = function (ts) {
          if (!t0) t0 = ts;
          var p = Math.min(1, (ts - t0) / dur), eased = 1 - Math.pow(1 - p, 3);
          el.textContent = fmt(Math.round(to * eased));
          if (p < 1) requestAnimationFrame(step);
        };
        el.textContent = '0';
        requestAnimationFrame(step);
      });
    }, { threshold: 0.4 });
    counts.forEach(function (c) { io.observe(c); });
  }

  // copy buttons (IBAN, SWIFT)
  doc.querySelectorAll('.copy[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy');
      var label = btn.querySelector('span');
      var original = label ? label.textContent : '';
      var done = function () {
        btn.classList.add('done');
        if (label) label.textContent = btn.getAttribute('data-done') || '✓';
        setTimeout(function () { btn.classList.remove('done'); if (label) label.textContent = original; }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallback(text); done(); });
      } else { fallback(text); done(); }
    });
  });
  function fallback(text) {
    var ta = doc.createElement('textarea');
    ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
    doc.body.appendChild(ta); ta.select();
    try { doc.execCommand('copy'); } catch (e) {}
    doc.body.removeChild(ta);
  }

  // project filter
  var filterBtns = doc.querySelectorAll('.chip-btn[data-filter]');
  filterBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      var f = b.getAttribute('data-filter');
      filterBtns.forEach(function (x) { x.classList.toggle('active', x === b); });
      doc.querySelectorAll('#project-list .card').forEach(function (c) {
        c.classList.toggle('is-hidden', !!f && c.getAttribute('data-program') !== f);
      });
    });
  });

  // lightbox
  var box = doc.getElementById('lightbox');
  if (box && typeof box.showModal === 'function') {
    var img = box.querySelector('img');
    doc.querySelectorAll('[data-lightbox]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        img.src = a.getAttribute('href');
        var inner = a.querySelector('img');
        img.alt = inner ? inner.alt : '';
        box.showModal();
      });
    });
    box.addEventListener('click', function () { box.close(); });
  }
})();
