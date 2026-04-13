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
                throw new Error('Could not connect to the server. Please check your connection.');
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
