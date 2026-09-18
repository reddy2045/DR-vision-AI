const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function request(path, options = {}) {
  const token = localStorage.getItem('phc_token');
  const headers = new Headers(options.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (!(options.body instanceof FormData) && options.body !== undefined) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (response.status === 401) { localStorage.removeItem('phc_token'); localStorage.removeItem('phc_user'); window.dispatchEvent(new Event('phc:unauthorized')); }
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

export const mediaUrl = (value) => value && (value.startsWith('http') ? value : `${API_BASE_URL}${value}`);
export const api = {
  login: (payload) => request('/api/auth/login/', { method: 'POST', body: JSON.stringify(payload) }),
  register: (payload) => request('/api/auth/register/', { method: 'POST', body: JSON.stringify(payload) }),
  patients: () => request('/api/patients/'),
  screening: (patientId) => request(`/api/screening/${encodeURIComponent(patientId)}/`),
  referral: (id) => request(`/api/referral/${id}/`),
  createScreening: (formData) => request('/api/create_screening/', { method: 'POST', body: formData }),
  adminEmployees: (params = {}) => {
    const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value));
    return request(`/api/admin/employees/${query.toString() ? `?${query}` : ''}`);
  },
  createEmployee: (payload) => request('/api/admin/employees/', { method: 'POST', body: JSON.stringify(payload) }),
  updateEmployee: (id, payload) => request(`/api/admin/employees/${id}/`, { method: 'PATCH', body: JSON.stringify(payload) }),
};
