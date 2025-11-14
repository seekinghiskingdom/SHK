// 1) Active nav highlight
(() => {
  const here = location.pathname.replace(/index\.html$/, '');
  document.querySelectorAll('.nav a, .nav-link').forEach(a => {
    const href = a.getAttribute('href');
    if (!href) return;
    const path = new URL(href, location.origin).pathname;
    const isRoot = here === '/' && path.endsWith('/');
    const isSection = here.startsWith(path) && path !== '/';
    if (isRoot || isSection) a.classList.add('is-active');
  });
})();

// 2) External-link hygiene
(() => {
  document.querySelectorAll('a[href^="http"]').forEach(a => {
    if (a.href.startsWith(location.origin)) return;
    a.setAttribute('target', '_blank');
    a.setAttribute('rel', 'noopener noreferrer');
  });
})();

// 3) Skip-link focus fix (accessibility)
(() => {
  const main = document.getElementById('content');
  if (main) main.setAttribute('tabindex', '-1');
})();

// 4) Header hamburger toggle
(() => {
  const header = document.querySelector('.site-header');
  const toggle = document.querySelector('.nav-toggle');

  if (!header || !toggle) return;

  toggle.addEventListener('click', () => {
    const open = header.classList.toggle('nav-open');
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
})();

// 5) Mobile: toggle submenus on click
(() => {
  const submenuParents = document.querySelectorAll('.nav-item.has-submenu > .nav-parent');
  if (!submenuParents.length) return;

  submenuParents.forEach(link => {
    link.addEventListener('click', (e) => {
      // Only intercept on small screens (same breakpoint as CSS)
      if (window.innerWidth > 700) return;

      e.preventDefault();
      const item = link.closest('.nav-item');
      if (!item) return;
      item.classList.toggle('submenu-open');
    });
  });
})();
