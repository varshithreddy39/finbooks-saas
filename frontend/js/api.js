// API base URL — set window.API_BASE_URL before this script to override (e.g. from a config.js)
// Falls back to localhost for local development
const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8001/api';

const api = {
    async request(endpoint, options = {}, _isRetry = false) {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        if (headers['Content-Type'] === undefined) {
            delete headers['Content-Type'];
        }

        let response;
        try {
            response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...options,
                headers
            });
        } catch (err) {
            console.error('Fetch error:', err);
            if (err.message === 'Failed to fetch') {
                throw new Error('Server is waking up, please wait 30 seconds and try again.');
            }
            throw err;
        }

        // Auto-refresh on 401 (expired token)
        if (response.status === 401 && !_isRetry) {
            const refreshed = await api._tryRefresh();
            if (refreshed) {
                return api.request(endpoint, options, true);
            } else {
                localStorage.removeItem('token');
                localStorage.removeItem('refresh_token');
                window.location = '../login_page/code.html';
                throw new Error('Session expired. Please log in again.');
            }
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Server error: ${response.status}`);
        }

        return response.json();
    },

    async _tryRefresh() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) return false;
        try {
            const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });
            if (!res.ok) return false;
            const data = await res.json();
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            return true;
        } catch (e) {
            return false;
        }
    },

    auth: {
        signup: (data) => api.request('/auth/signup', { method: 'POST', body: JSON.stringify(data) }),
        login: (data) => api.request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
        resetPassword: (email) => api.request('/auth/reset-password', { method: 'POST', body: JSON.stringify({ email }) }),
        deleteAccount: () => api.request('/auth/delete-account', { method: 'DELETE' }),
    },

    company: {
        getProfile: (companyId) => api.request(`/company/profile?company_id=${companyId}`),
        getMine: () => api.request('/company/profile/mine'),
        setup: (data) => api.request('/company/setup', { method: 'POST', body: JSON.stringify(data) }),
        uploadLogo: (companyId, file) => {
            const formData = new FormData();
            formData.append('file', file);
            return api.request(`/company/upload-logo?company_id=${companyId}`, {
                method: 'POST',
                body: formData,
                headers: { 'Content-Type': undefined }
            });
        },
        uploadSignature: (companyId, file) => {
            const formData = new FormData();
            formData.append('file', file);
            return api.request(`/company/upload-signature?company_id=${companyId}`, {
                method: 'POST',
                body: formData,
                headers: { 'Content-Type': undefined }
            });
        }
    },

    invoices: {
        list: (companyId) => api.request(`/invoices/?company_id=${companyId}`),
        create: (data, companyId) => api.request(`/invoices/create?company_id=${companyId}`, { method: 'POST', body: JSON.stringify(data) }),
        get: (invoiceId, companyId) => api.request(`/invoices/${invoiceId}?company_id=${companyId}`),
        update: (invoiceId, data, companyId) => api.request(`/invoices/${invoiceId}?company_id=${companyId}`, { method: 'PUT', body: JSON.stringify(data) }),
        delete: (invoiceId, companyId) => api.request(`/invoices/${invoiceId}?company_id=${companyId}`, { method: 'DELETE' }),
    },

    masters: {
        getCustomers: (companyId) => api.request(`/masters/customers?company_id=${companyId}`),
        getProducts: (companyId) => api.request(`/masters/products?company_id=${companyId}`),
        addProduct: (data, companyId) => api.request(`/masters/products?company_id=${companyId}`, { method: 'POST', body: JSON.stringify(data) }),
        addCustomer: (data, companyId) => api.request(`/masters/customers?company_id=${companyId}`, { method: 'POST', body: JSON.stringify(data) }),
        deleteProduct: (id, companyId) => api.request(`/masters/products/${id}?company_id=${companyId}`, { method: 'DELETE' }),
        deleteCustomer: (id, companyId) => api.request(`/masters/customers/${id}?company_id=${companyId}`, { method: 'DELETE' }),
        getVendors: (companyId) => api.request(`/masters/vendors?company_id=${companyId}`),
        addVendor: (data, companyId) => api.request(`/masters/vendors?company_id=${companyId}`, { method: 'POST', body: JSON.stringify(data) }),
        deleteVendor: (id, companyId) => api.request(`/masters/vendors/${id}?company_id=${companyId}`, { method: 'DELETE' }),
    },

    quotations: {
        list: (companyId) => api.request(`/quotations/?company_id=${companyId}`),
        create: (data, companyId) => api.request(`/quotations/create?company_id=${companyId}`, { method: 'POST', body: JSON.stringify(data) }),
        get: (quotationId, companyId) => api.request(`/quotations/${quotationId}?company_id=${companyId}`),
        update: (quotationId, data, companyId) => api.request(`/quotations/${quotationId}?company_id=${companyId}`, { method: 'PUT', body: JSON.stringify(data) }),
        getPdf: (quotationId, companyId) => `${API_BASE_URL}/quotations/${quotationId}/pdf?company_id=${companyId}`,
        delete: (quotationId, companyId) => api.request(`/quotations/${quotationId}?company_id=${companyId}`, { method: 'DELETE' }),
    },

    creditNotes: {
        list: (companyId) => api.request(`/credit-notes/list?company_id=${companyId}`),
        create: (data, companyId) => api.request(`/credit-notes/create?company_id=${companyId}`, { method: 'POST', body: JSON.stringify(data) }),
        update: (cnId, data, companyId) => api.request(`/credit-notes/${cnId}?company_id=${companyId}`, { method: 'PUT', body: JSON.stringify(data) }),
        get: (cnId, companyId) => api.request(`/credit-notes/${cnId}?company_id=${companyId}`),
        getPdf: (cnId, companyId) => `${API_BASE_URL}/credit-notes/${cnId}/pdf?company_id=${companyId}`,
        delete: (cnId, companyId) => api.request(`/credit-notes/${cnId}?company_id=${companyId}`, { method: 'DELETE' })
    }
};

window.PrecisionApi = api;

// ─────────────────────────────────────────────────────────────
// Global UI helpers — available on every page
// ─────────────────────────────────────────────────────────────

/**
 * showToast(message, type, duration)
 * Renders a slide-in toast in the top-right corner.
 * type: 'success' | 'error' | 'warning' | 'info'
 */
window.showToast = function(message, type = 'info', duration = 4000) {
  // Remove any existing toast with same id
  const existing = document.getElementById('fb-toast');
  if (existing) existing.remove();

  const icons = {
    success: 'check_circle',
    error:   'error',
    warning: 'warning',
    info:    'info'
  };
  const colors = {
    success: 'bg-emerald-600',
    error:   'bg-red-600',
    warning: 'bg-amber-500',
    info:    'bg-teal-700'
  };

  const toast = document.createElement('div');
  toast.id = 'fb-toast';
  toast.style.cssText = `
    position: fixed; top: 20px; right: 20px; z-index: 9999;
    display: flex; align-items: flex-start; gap: 10px;
    max-width: 360px; min-width: 260px;
    padding: 14px 16px; border-radius: 12px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.18);
    color: white; font-family: 'Inter', sans-serif; font-size: 13.5px; line-height: 1.5;
    animation: fb-toast-in 0.28s cubic-bezier(0.34,1.56,0.64,1) forwards;
  `;
  toast.className = colors[type] || colors.info;

  toast.innerHTML = `
    <span class="material-symbols-outlined" style="font-size:20px;flex-shrink:0;margin-top:1px">${icons[type] || 'info'}</span>
    <span style="flex:1">${message}</span>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;color:white;opacity:0.7;cursor:pointer;padding:0 0 0 6px;font-size:18px;line-height:1;flex-shrink:0" title="Dismiss">✕</button>
  `;

  // Inject keyframe once
  if (!document.getElementById('fb-toast-style')) {
    const style = document.createElement('style');
    style.id = 'fb-toast-style';
    style.textContent = `
      @keyframes fb-toast-in {
        from { opacity:0; transform: translateX(30px) scale(0.95); }
        to   { opacity:1; transform: translateX(0) scale(1); }
      }
      @keyframes fb-toast-out {
        from { opacity:1; transform: translateX(0) scale(1); }
        to   { opacity:0; transform: translateX(30px) scale(0.95); }
      }
    `;
    document.head.appendChild(style);
  }

  document.body.appendChild(toast);

  const timer = setTimeout(() => {
    toast.style.animation = 'fb-toast-out 0.25s ease forwards';
    setTimeout(() => toast.remove(), 260);
  }, duration);

  // Clear timer if manually dismissed
  toast.querySelector('button').addEventListener('click', () => clearTimeout(timer));
};

/**
 * showBanner(containerId, message, type)
 * Renders an inline alert banner inside a container element.
 * type: 'success' | 'error' | 'warning' | 'info'
 * Call showBanner('my-div', '') to clear.
 */
window.showBanner = function(containerId, message, type = 'error') {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!message) {
    container.innerHTML = '';
    container.style.display = 'none';
    return;
  }

  const cfg = {
    success: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-800', icon: 'check_circle', iconColor: 'text-emerald-500' },
    error:   { bg: 'bg-red-50',     border: 'border-red-200',     text: 'text-red-800',     icon: 'error',         iconColor: 'text-red-400'     },
    warning: { bg: 'bg-amber-50',   border: 'border-amber-200',   text: 'text-amber-800',   icon: 'warning',       iconColor: 'text-amber-500'   },
    info:    { bg: 'bg-blue-50',    border: 'border-blue-200',    text: 'text-blue-800',    icon: 'info',          iconColor: 'text-blue-500'    },
  };
  const c = cfg[type] || cfg.info;

  container.style.display = 'block';
  container.innerHTML = `
    <div class="flex items-start gap-2.5 p-3 rounded-lg border ${c.bg} ${c.border}">
      <span class="material-symbols-outlined text-base mt-0.5 flex-shrink-0 ${c.iconColor}">${c.icon}</span>
      <p class="text-sm leading-snug ${c.text} flex-1">${message}</p>
    </div>
  `;
};
