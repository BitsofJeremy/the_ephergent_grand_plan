const STORAGE_KEY = 'eph_spoiler_level';
const LEVELS = ['safe','s2','s3'];
const ICONS = { safe: '🟢', s2: '🟡', s3: '🔴' };

function getLevel() {
  return localStorage.getItem(STORAGE_KEY) || 'safe';
}

function setLevel(l) {
  if (!LEVELS.includes(l)) return;
  localStorage.setItem(STORAGE_KEY, l);
  applyLevel();
}

function applyLevel() {
  const current = getLevel();
  document.querySelectorAll('[data-spoiler-level]').forEach(el => {
    const lvl = el.getAttribute('data-spoiler-level');
    if (!lvl) return;
    const rank = LEVELS.indexOf(lvl);
    const allowed = LEVELS.indexOf(current);
    if (rank <= allowed) {
      el.classList.remove('spoiler-hidden');
      el.classList.add('spoiler-visible');
      el.setAttribute('aria-hidden','false');
    } else {
      el.classList.add('spoiler-hidden');
      el.classList.remove('spoiler-visible');
      el.setAttribute('aria-hidden','true');
    }
  });
  updateControl();
}

function updateControl() {
  const ctrl = document.getElementById('eph-spoiler-control');
  if (!ctrl) return;
  const current = getLevel();
  ctrl.querySelectorAll('button[data-level]').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-level') === current);
  });
}

function makeControl() {
  if (document.getElementById('eph-spoiler-control')) return;
  const ctrl = document.createElement('div');
  ctrl.id = 'eph-spoiler-control';
  ctrl.setAttribute('aria-hidden','false');
  ctrl.style.position = 'fixed';
  ctrl.style.right = '12px';
  ctrl.style.bottom = '12px';
  ctrl.style.zIndex = 99999;
  ctrl.style.display = 'flex';
  ctrl.style.gap = '6px';

  LEVELS.forEach(l => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.setAttribute('data-level', l);
    btn.textContent = ICONS[l];
    btn.title = l === 'safe' ? 'Safe (no spoilers)' : (l === 's2' ? 'S2 (some spoilers)' : 'S3 (full spoilers)');
    btn.style.padding = '8px 10px';
    btn.style.borderRadius = '8px';
    btn.style.border = '1px solid rgba(255,255,255,0.06)';
    btn.style.background = 'rgba(255,255,255,0.02)';
    btn.style.color = 'white';
    btn.style.cursor = 'pointer';
    btn.addEventListener('click', () => setLevel(l));
    ctrl.appendChild(btn);
  });

  document.body.appendChild(ctrl);
}

function injectStyles() {
  if (document.getElementById('eph-spoiler-styles')) return;
  const s = document.createElement('style');
  s.id = 'eph-spoiler-styles';
  s.textContent = `
    [data-spoiler-level] { transition: opacity .18s ease, transform .18s ease; }
    .spoiler-hidden { opacity: 0; transform: translateY(-6px); pointer-events: none; height: 0 !important; overflow: hidden; }
    .spoiler-visible { opacity: 1; transform: none; }
    #eph-spoiler-control button.active { outline: 2px solid rgba(0,212,255,0.15); box-shadow: 0 6px 18px rgba(0,212,255,0.06); }
  `;
  document.head.appendChild(s);
}

document.addEventListener('DOMContentLoaded', () => {
  injectStyles();
  makeControl();
  applyLevel();
});

// Expose API for devs
window.EphSpoilers = { getLevel, setLevel, LEVELS };
