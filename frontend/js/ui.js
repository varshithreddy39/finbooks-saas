// ─────────────────────────────────────────────────────────────
// Finbooks UI Helpers — loaded in <head> before everything else
// showToast() and showBanner() are available globally on all pages
// ─────────────────────────────────────────────────────────────

/**
 * showToast(message, type, duration)
 * Slide-in toast in the top-right corner.
 * type: 'success' | 'error' | 'warning' | 'info'
 */
window.showToast = function(message, type, duration) {
  type = type || 'info';
  duration = duration || 4000;

  var existing = document.getElementById('fb-toast');
  if (existing) existing.remove();

  var icons = { success: 'check_circle', error: 'error', warning: 'warning', info: 'info' };
  var colors = { success: '#059669', error: '#dc2626', warning: '#d97706', info: '#0d6e6e' };

  var toast = document.createElement('div');
  toast.id = 'fb-toast';
  toast.style.cssText = [
    'position:fixed', 'top:20px', 'right:20px', 'z-index:9999',
    'display:flex', 'align-items:flex-start', 'gap:10px',
    'max-width:360px', 'min-width:260px',
    'padding:14px 16px', 'border-radius:12px',
    'box-shadow:0 8px 30px rgba(0,0,0,0.18)',
    'color:white', 'font-family:Inter,sans-serif', 'font-size:13.5px', 'line-height:1.5',
    'background:' + (colors[type] || colors.info),
    'animation:fb-toast-in 0.28s cubic-bezier(0.34,1.56,0.64,1) forwards'
  ].join(';');

  toast.innerHTML =
    '<span class="material-symbols-outlined" style="font-size:20px;flex-shrink:0;margin-top:1px">' + (icons[type] || 'info') + '</span>' +
    '<span style="flex:1">' + message + '</span>' +
    '<button onclick="this.parentElement.remove()" style="background:none;border:none;color:white;opacity:0.7;cursor:pointer;padding:0 0 0 6px;font-size:18px;line-height:1;flex-shrink:0" title="Dismiss">\u00d7</button>';

  if (!document.getElementById('fb-ui-style')) {
    var style = document.createElement('style');
    style.id = 'fb-ui-style';
    style.textContent =
      '@keyframes fb-toast-in{from{opacity:0;transform:translateX(30px) scale(0.95)}to{opacity:1;transform:translateX(0) scale(1)}}' +
      '@keyframes fb-toast-out{from{opacity:1;transform:translateX(0) scale(1)}to{opacity:0;transform:translateX(30px) scale(0.95)}}' +
      '@keyframes fb-banner-in{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}';
    document.head.appendChild(style);
  }

  document.body.appendChild(toast);

  var timer = setTimeout(function() {
    toast.style.animation = 'fb-toast-out 0.25s ease forwards';
    setTimeout(function() { if (toast.parentNode) toast.remove(); }, 260);
  }, duration);

  toast.querySelector('button').addEventListener('click', function() { clearTimeout(timer); });
};

/**
 * showBanner(containerId, message, type)
 * Renders an inline alert banner inside a container div.
 * type: 'success' | 'error' | 'warning' | 'info'
 * Pass empty message to clear the banner.
 */
window.showBanner = function(containerId, message, type) {
  type = type || 'error';
  var container = document.getElementById(containerId);
  if (!container) return;

  if (!message) {
    container.innerHTML = '';
    container.style.display = 'none';
    return;
  }

  var cfg = {
    success: { bg: '#f0fdf4', border: '#bbf7d0', text: '#166534', icon: 'check_circle',  iconColor: '#16a34a' },
    error:   { bg: '#fef2f2', border: '#fecaca', text: '#991b1b', icon: 'error',          iconColor: '#ef4444' },
    warning: { bg: '#fffbeb', border: '#fde68a', text: '#92400e', icon: 'warning',        iconColor: '#f59e0b' },
    info:    { bg: '#eff6ff', border: '#bfdbfe', text: '#1e40af', icon: 'info',           iconColor: '#3b82f6' }
  };
  var c = cfg[type] || cfg.info;

  container.style.display = 'block';
  container.style.animation = 'fb-banner-in 0.22s ease forwards';
  container.innerHTML =
    '<div style="display:flex;align-items:flex-start;gap:10px;padding:12px 14px;border-radius:10px;border:1px solid ' + c.border + ';background:' + c.bg + '">' +
      '<span class="material-symbols-outlined" style="font-size:17px;margin-top:1px;flex-shrink:0;color:' + c.iconColor + '">' + c.icon + '</span>' +
      '<p style="font-size:13px;line-height:1.5;color:' + c.text + ';flex:1;margin:0">' + message + '</p>' +
    '</div>';
};
