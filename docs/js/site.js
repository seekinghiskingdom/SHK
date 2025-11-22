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
    try {
      const url = new URL(a.href);
      if (url.origin === location.origin) return;
      a.setAttribute('target', '_blank');
      a.setAttribute('rel', 'noopener noreferrer');
    } catch (e) {
      // ignore malformed URLs
    }
  });
})();

// 3) Skip-link focus fix (accessibility)
(() => {
  const main = document.getElementById('content');
  if (main) main.setAttribute('tabindex', '-1');
})();

// 4) Header hamburger toggle – controls .site-header.nav-open
(() => {
  const header = document.querySelector('.site-header');
  const toggle = document.querySelector('.nav-toggle');

  if (!header || !toggle) return;

  toggle.addEventListener('click', () => {
    const isOpen = header.classList.toggle('nav-open');
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });
})();

// 5) Mobile: toggle submenus via the small ▾ button, keep parent link navigable
(() => {
  const toggles = document.querySelectorAll('.nav-item.has-submenu .submenu-toggle');
  if (!toggles.length) return;

  toggles.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const item = btn.closest('.nav-item');
      if (!item) return;
      const isOpen = item.classList.toggle('submenu-open');
      btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
  });
})();

// 6) Help CTA collapse/expand (cross button)
(() => {
  const cta = document.getElementById('help-cta');
  if (!cta) return;
  const toggle = cta.querySelector('.help-cta-toggle');
  if (!toggle) return;

  toggle.addEventListener('click', () => {
    const isCollapsed = cta.classList.toggle('help-cta--collapsed');
    toggle.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
  });
})();
