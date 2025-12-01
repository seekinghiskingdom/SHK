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

// // 4) Header nav drawer (hamburger + overlay)
// (() => {
//   const toggle  = document.querySelector('[data-nav-toggle]');
//   const overlay = document.querySelector('[data-nav-overlay]');
//   if (!toggle || !overlay) return;

//   const drawer      = overlay.querySelector('.site-nav-drawer');
//   const closeButtons = overlay.querySelectorAll('[data-nav-close]');

//   function openNav() {
//     overlay.hidden = false;
//     document.body.classList.add('site-nav-open');
//     toggle.setAttribute('aria-expanded', 'true');
//   }

//   function closeNav() {
//     overlay.hidden = true;
//     document.body.classList.remove('site-nav-open');
//     toggle.setAttribute('aria-expanded', 'false');
//   }

//   // Hamburger toggle
//   toggle.addEventListener('click', () => {
//     if (overlay.hidden) {
//       openNav();
//     } else {
//       closeNav();
//     }
//   });

//   // Any X / close button inside the drawer
//   closeButtons.forEach(btn => {
//     btn.addEventListener('click', closeNav);
//   });

//   // Click on dim background closes drawer
//   overlay.addEventListener('click', (e) => {
//     if (e.target === overlay) {
//       closeNav();
//     }
//   });

//   // Esc key closes drawer
//   document.addEventListener('keydown', (e) => {
//     if (e.key === 'Escape' && !overlay.hidden) {
//       closeNav();
//     }
//   });
// })();


// 5) Mobile: toggle submenus via the small ▾ button, keep parent link navigable
// (() => {
//   const toggles = document.querySelectorAll('.nav-item.has-submenu .submenu-toggle');
//   if (!toggles.length) return;

//   toggles.forEach(btn => {
//     btn.addEventListener('click', (e) => {
//       e.preventDefault();
//       const item = btn.closest('.nav-item');
//       if (!item) return;
//       const isOpen = item.classList.toggle('submenu-open');
//       btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
//     });
//   });
// })();

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

// 7) Left Nav CTA: automatic path links + collapse
(() => {
  const navCta = document.getElementById('nav-cta');
  if (!navCta) return;

  const linksContainer = navCta.querySelector('.nav-cta-links');
  const toggle = navCta.querySelector('.nav-cta-toggle');

  // default collapsed on all screens
  navCta.classList.add('nav-cta--collapsed');
  if (toggle) toggle.setAttribute('aria-expanded', 'false');

  // Build path segments from current URL
  const base = navCta.dataset.baseurl || '';
  const fullPath = location.pathname;
  let relPath = fullPath;

  // Strip baseurl from the front if present (e.g. /SHK)
  if (base && relPath.startsWith(base)) {
    relPath = relPath.slice(base.length);
  }

  // Split into segments, filter empties
  const rawSegments = relPath.split('/').filter(Boolean);

  // Optionally skip language codes like en/grc/he in the breadcrumb CTA
  const segments = rawSegments.filter(seg => !/^(en|grc|he)$/i.test(seg));

  // Start with Home
  const crumbs = [];
  crumbs.push({
    label: 'Home',
    href: base || '/'
  });

  // Build accumulated paths
  let currentPath = '';
  segments.forEach((seg, idx) => {
    currentPath += '/' + seg;
    const isLast = idx === segments.length - 1;

    // Label logic: language-ish codes omitted above, short slugs uppercased (kjv),
    // others title-cased (literature → Literature, strongs-concordance → Strongs Concordance)
    let label;
    if (/^[a-z]{2,4}$/i.test(seg)) {
      label = seg.toUpperCase();
    } else {
      label = seg
        .replace(/-/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
    }

    crumbs.push({
      label,
      href: (base || '') + currentPath + '/'
    });
  });

  // Render as stacked buttons, bottom-up
  linksContainer.innerHTML = '';
  crumbs.forEach(crumb => {
    const a = document.createElement('a');
    a.href = crumb.href;
    a.textContent = crumb.label;
    a.className = 'btn nav-cta-link';
    linksContainer.appendChild(a);
  });

  // after crumbs.forEach(...) has run
  const prevUrl = navCta.dataset.prevUrl;
  const prevLabel = navCta.dataset.prevLabel || 'Prev';
  const nextUrl = navCta.dataset.nextUrl;
  const nextLabel = navCta.dataset.nextLabel || 'Next';
  if (prevUrl || nextUrl) {
    const row = document.createElement('div');
    row.className = 'nav-cta-prevnext';

    if (prevUrl) {
      const aPrev = document.createElement('a');
      aPrev.href = prevUrl;
      aPrev.textContent = '← ' + prevLabel;
      aPrev.className = 'btn nav-cta-link nav-cta-prev';
      row.appendChild(aPrev);
    }

    if (nextUrl) {
      const aNext = document.createElement('a');
      aNext.href = nextUrl;
      aNext.textContent = nextLabel + ' →';
      aNext.className = 'btn nav-cta-link nav-cta-next';
      row.appendChild(aNext);
    }

    linksContainer.appendChild(row);
  }

  // Collapse / expand behavior (similar to Help CTA)
  if (toggle) {
    toggle.addEventListener('click', () => {
      const isCollapsed = navCta.classList.toggle('nav-cta--collapsed');
      toggle.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
    });
  }
})();

// 8) Testimony CTA collapse/expand
(() => {
  const cta = document.getElementById('testimony-cta');
  if (!cta) return;
  const toggle = cta.querySelector('.testimony-cta-toggle');
  if (!toggle) return;

  // default collapsed
  cta.classList.add('testimony-cta--collapsed');
  toggle.setAttribute('aria-expanded', 'false');

  toggle.addEventListener('click', () => {
    const isCollapsed = cta.classList.toggle('testimony-cta--collapsed');
    toggle.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
  });
})();

// 9) User Profile Picture Selection (1–123)

// Choose which numeric avatar files are admin-only (e.g. 121–123 = SHK logos)
const SHK_ADMIN_ONLY_AVATAR_IDS = new Set([999, 998]); // adjust as needed

window.SHK_PROFILE_AVATARS = Array.from({ length: 123 }, (_, idx) => {
  const id = idx + 1; // 1–123
  return {
    key: `avatar-${id}`,                               // logical key stored in user metadata
    src: `${window.SHK_BASEURL || ''}/img/profiles/${id}.png`,
    adminOnly: SHK_ADMIN_ONLY_AVATAR_IDS.has(id)       // true only for reserved IDs
  };
});
// Add the two special SHK logos (998, 999)
[998, 999].forEach((id) => {
  window.SHK_PROFILE_AVATARS.push({
    key: `avatar-${id}`,
    src: `${window.SHK_BASEURL || ''}/img/profiles/${id}.png`,
    adminOnly: true
  });
});

// Helper: look up avatar URL by key, fall back gracefully
window.SHK_getAvatarUrlByKey = function (avatarKey) {
  if (!avatarKey || !window.SHK_PROFILE_AVATARS) return null;
  const match = window.SHK_PROFILE_AVATARS.find(a => a.key === avatarKey);
  return match ? match.src : null;
};

// Shared Supabase client helper (Phase 1.1)
window.SHK_getSupabaseClient = function () {
  if (!window.supabase || !window.supabase.createClient) return null;

  if (!window.shkSupabase) {
    const SUPABASE_URL = 'https://vubmekxghtydatmofsit.supabase.co';
    const SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_7BqkY9_i_wMhcupuThXibw_SHoGJox9';
    window.shkSupabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);
  }

  return window.shkSupabase;
};


// 10) Header account pill: avatar when logged in, "Sign in" when logged out
(() => {
  const pill = document.querySelector('.site-header-account-pill');
  if (!pill) return;

  const labelEl   = pill.querySelector('.site-header-account-label');
  const initialEl = document.getElementById('site-account-initial');
  const imgEl     = document.getElementById('site-account-avatar-img');

  const base = window.SHK_BASEURL || '';

  // Default: signed-out look
  if (labelEl)   labelEl.textContent = 'Sign in';
  if (initialEl) initialEl.textContent = '✝';
  if (imgEl)     imgEl.style.display = 'none';
  pill.href = `${base}/account/sign-in/`;

  const supabase = window.SHK_getSupabaseClient();
  if (!supabase) return;

  supabase.auth.getUser().then(({ data, error }) => {
    if (error || !data || !data.user) return;

    const user = data.user;
    const meta = user.user_metadata || {};

    const avatarKey   = meta.avatar_key;
    const displayName = meta.display_name;
    const handle      = meta.handle || null;
    const role        = meta.role || 'user';
    const email       = user.email || '';

    window.SHK_ROLE   = role;
    window.SHK_HANDLE = handle;

    let initial = '✝';
    if (displayName && displayName.trim()) initial = displayName.trim()[0].toUpperCase();
    else if (email)                         initial = email[0].toUpperCase();

    pill.href = `${base}/account/`;
    if (labelEl)   labelEl.textContent = '';

    if (avatarKey && window.SHK_getAvatarUrlByKey) {
      const url = window.SHK_getAvatarUrlByKey(avatarKey);
      if (url && imgEl) {
        imgEl.src = url;
        imgEl.style.display = 'block';
        if (initialEl) initialEl.textContent = '';
      }
    } else {
      if (imgEl)     imgEl.style.display = 'none';
      if (initialEl) initialEl.textContent = initial;
    }
  });
})();



// 11) Site left rail (desktop nav + search)
(() => {
  const rail = document.querySelector('.site-rail');
  if (!rail) return;

  const toggle       = rail.querySelector('.site-rail-toggle');
  const iconButtons  = rail.querySelectorAll('.site-rail-icon-btn');
  const groupElems   = rail.querySelectorAll('.site-rail-group');
  const groupHeaders = rail.querySelectorAll('.site-rail-group-header');
  const searchInput  = rail.querySelector('#site-rail-search-input');
  const allLinks     = rail.querySelectorAll('.site-rail-link');
  const panelClose   = rail.querySelector('.site-rail-panel-close');

  function isOpen() {
    return rail.classList.contains('site-rail--open');
  }

  function openRail() {
    rail.classList.add('site-rail--open');
  }

  function closeRail() {
    rail.classList.remove('site-rail--open');
  }

  // Top ☰ button
  if (toggle) {
    toggle.addEventListener('click', () => {
      if (isOpen()) {
        closeRail();
      } else {
        openRail();
      }
    });
  }

  // Close button in panel header
  if (panelClose) {
    panelClose.addEventListener('click', closeRail);
  }

  // Clicking an icon: open rail + open that section's group
  iconButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-rail-section');
      if (!id) return;

      openRail();

      groupElems.forEach(group => {
        const match = group.getAttribute('data-rail-group') === id;
        group.classList.toggle('site-rail-group--open', match);
      });

      const active = rail.querySelector(`.site-rail-group[data-rail-group="${id}"]`);
      if (active) {
        active.scrollIntoView({ block: 'start', behavior: 'smooth' });
      }
    });
  });

  // Expand/collapse groups inside panel
  groupHeaders.forEach(header => {
    header.addEventListener('click', () => {
      const group = header.closest('.site-rail-group');
      if (!group) return;

      const willOpen = !group.classList.contains('site-rail-group--open');

      // optional: only one open at a time
      if (willOpen) {
        groupElems.forEach(g => {
          if (g !== group) g.classList.remove('site-rail-group--open');
        });
      }

      group.classList.toggle('site-rail-group--open', willOpen);
    });
  });

  // Esc key closes
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isOpen()) {
      closeRail();
    }
  });

  // Simple client-side search over label + keywords
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.trim().toLowerCase();

      if (!q) {
        // Show everything
        groupElems.forEach(g => g.style.display = '');
        allLinks.forEach(li => li.style.display = '');
        return;
      }

      groupElems.forEach(group => {
        let anyVisible = false;
        const links = group.querySelectorAll('.site-rail-link');

        links.forEach(li => {
          const haystack = (li.dataset.search || '').toLowerCase();
          const match = haystack.includes(q);
          li.style.display = match ? '' : 'none';
          if (match) anyVisible = true;
        });

        group.style.display = anyVisible ? '' : 'none';
      });
    });
  }
})();
