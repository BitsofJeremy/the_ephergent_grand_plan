const DEFAULT_MAX = 15728640; // 15MB

function toMB(bytes) {
  return (bytes / (1024 * 1024)).toFixed(2);
}

function createOverlay(iframe, msg, sizeText) {
  const wrapper = document.createElement('div');
  wrapper.style.position = 'relative';
  wrapper.style.display = 'block';

  const container = document.createElement('div');
  container.style.position = 'absolute';
  container.style.inset = '0';
  container.style.display = 'flex';
  container.style.flexDirection = 'column';
  container.style.alignItems = 'center';
  container.style.justifyContent = 'center';
  container.style.background = 'linear-gradient(180deg, rgba(2,6,23,0.6), rgba(2,6,23,0.7))';
  container.style.color = '#e8e8f0';
  container.style.backdropFilter = 'blur(4px)';
  container.style.zIndex = '20';
  container.style.padding = '1rem';
  container.style.textAlign = 'center';

  const title = document.createElement('div');
  title.textContent = msg;
  title.style.fontFamily = 'JetBrains Mono, monospace';
  title.style.fontSize = '14px';
  title.style.marginBottom = '6px';

  const detail = document.createElement('div');
  detail.textContent = sizeText || 'Size unknown';
  detail.style.fontSize = '12px';
  detail.style.opacity = '0.85';
  detail.style.marginBottom = '12px';

  const btn = document.createElement('button');
  btn.textContent = 'Load anyway';
  btn.style.background = '#00d4ff';
  btn.style.color = '#081018';
  btn.style.border = 'none';
  btn.style.padding = '8px 12px';
  btn.style.borderRadius = '8px';
  btn.style.cursor = 'pointer';
  btn.style.fontFamily = 'JetBrains Mono, monospace';

  btn.addEventListener('click', () => {
    const original = iframe.getAttribute('data-eph-src');
    if (original) {
      iframe.setAttribute('src', original);
      container.remove();
    }
  });

  container.appendChild(title);
  container.appendChild(detail);
  container.appendChild(btn);

  // position container inside iframe's parent
  const parent = iframe.parentElement || iframe;
  parent.style.position = parent.style.position || 'relative';
  parent.appendChild(container);
}

function preventLoading(iframe, size, max) {
  // stash original src and remove it to avoid loading
  const src = iframe.getAttribute('src');
  if (!src) return;
  iframe.setAttribute('data-eph-src', src);
  iframe.removeAttribute('src');
  const msg = `This embedded game exceeds the ${toMB(max)}MB limit.`;
  const sizeText = `Reported size: ${toMB(size)} MB (limit: ${toMB(max)} MB)`;
  createOverlay(iframe, msg, sizeText);
}

function maybeWarn(iframe, size, max) {
  // If we can't determine size, show a gentle warning but allow loading.
  // Show a smaller overlay that can be dismissed.
  const src = iframe.getAttribute('src');
  if (!src) return;
  iframe.setAttribute('data-eph-src', src);
  // keep src for now but show warning
  const msg = `Unable to verify game size before loading.`;
  const sizeText = `Proceed if you trust this source — limit: ${toMB(max)} MB`;
  createOverlay(iframe, msg, sizeText);
}

async function checkIframe(iframe) {
  const maxAttr = iframe.getAttribute('data-max-bytes');
  const max = maxAttr ? parseInt(maxAttr, 10) : DEFAULT_MAX;
  const src = iframe.getAttribute('src');
  if (!src) return;

  // Try HEAD first
  try {
    const resp = await fetch(src, { method: 'HEAD', mode: 'cors' });
    const cl = resp.headers.get('Content-Length');
    if (cl) {
      const size = parseInt(cl, 10);
      if (!Number.isNaN(size) && size > max) {
        preventLoading(iframe, size, max);
      }
      return;
    }
  } catch (err) {
    // continue to fallback
    // console.warn('embed-check HEAD failed', err);
  }

  // Fallback: attempt a ranged GET for first byte to try to obtain Content-Range
  try {
    const r = await fetch(src, { method: 'GET', headers: { Range: 'bytes=0-0' }, mode: 'cors' });
    const cr = r.headers.get('Content-Range');
    if (cr) {
      // format: bytes 0-0/12345
      const total = cr.split('/').pop();
      const size = parseInt(total, 10);
      if (!Number.isNaN(size) && size > max) {
        preventLoading(iframe, size, max);
      }
      return;
    }
  } catch (err) {
    // console.warn('embed-check range failed', err);
  }

  // final fallback: unknown size
  maybeWarn(iframe, null, max);
}

document.addEventListener('DOMContentLoaded', () => {
  const iframes = Array.from(document.querySelectorAll('iframe[data-max-bytes]'));
  iframes.forEach(iframe => {
    // run check but don't block UI
    checkIframe(iframe);
  });
});
