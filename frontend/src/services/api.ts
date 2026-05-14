const API_BASE = (import.meta as any).env?.VITE_API_BASE || '/api';

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    let msg = text;
    try {
      const parsed = JSON.parse(text);
      msg = parsed.detail || parsed.message || text;
    } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as any;
  return res.json();
}

async function multipartRequest<T = any>(path: string, formData: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    let msg = text;
    try {
      const parsed = JSON.parse(text);
      msg = parsed.detail || msg;
    } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Auth ──
export const auth = {
  login: (email: string, password: string) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string, name: string, organization?: string) =>
    request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name, organization }),
    }),
  me: () => request('/auth/me'),
  updateMe: (name?: string, organization?: string) =>
    request('/auth/me', { method: 'PUT', body: JSON.stringify({ name, organization }) }),
  logout: () => request('/auth/logout', { method: 'POST' }),
};

// ── Regulations ──
export const regulations = {
  list: (params: { jurisdiction?: string; category?: string; search?: string; page?: number; limit?: number } = {}) => {
    const q = new URLSearchParams();
    if (params.jurisdiction) q.set('jurisdiction', params.jurisdiction);
    if (params.category) q.set('category', params.category);
    if (params.search) q.set('search', params.search);
    if (params.page) q.set('page', String(params.page));
    if (params.limit) q.set('limit', String(params.limit));
    return request(`/regulations${q.toString() ? '?' + q.toString() : ''}`);
  },
  get: (id: string) => request(`/regulations/${id}`),
  search: (q: string, page = 1) => request(`/regulations/search?q=${encodeURIComponent(q)}&page=${page}`),
  create: (data: any) => request('/regulations', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any) => request(`/regulations/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) => request(`/regulations/${id}`, { method: 'DELETE' }),
};

// ── Assessments ──
export const assessments = {
  dashboard: () => request('/assessments/dashboard'),
  list: (params: { page?: number; limit?: number; status?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.page) q.set('page', String(params.page));
    if (params.limit) q.set('limit', String(params.limit));
    if (params.status) q.set('status', params.status);
    return request(`/assessments${q.toString() ? '?' + q.toString() : ''}`);
  },
  get: (id: string) => request(`/assessments/${id}`),
  create: (regulation_id: string, next_review_date?: string) =>
    request('/assessments', { method: 'POST', body: JSON.stringify({ regulation_id, next_review_date }) }),
  runAI: (id: string) => request(`/assessments/${id}/run-ai`, { method: 'POST' }),
  history: (id: string) => request(`/assessments/${id}/history`),
};

// ── Risk Items ──
export const riskItems = {
  get: (id: string) => request(`/risk-items/${id}`),
  update: (id: string, data: { status?: string; mitigation_plan?: string; due_date?: string }) =>
    request(`/risk-items/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  byAssessment: (assessmentId: string) => request(`/risk-items/by-assessment/${assessmentId}`),
};

// ── Alerts ──
export const alerts = {
  list: (params: { page?: number; limit?: number; unread_only?: boolean; severity?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.page) q.set('page', String(params.page));
    if (params.limit) q.set('limit', String(params.limit));
    if (params.unread_only) q.set('unread_only', 'true');
    if (params.severity) q.set('severity', params.severity);
    return request(`/alerts${q.toString() ? '?' + q.toString() : ''}`);
  },
  markRead: (id: string) => request(`/alerts/${id}/read`, { method: 'PATCH' }),
  markAllRead: () => request('/alerts/read-all', { method: 'PATCH' }),
  generate: () => request('/alerts/generate', { method: 'POST' }),
  dismiss: (id: string) => request(`/alerts/${id}`, { method: 'DELETE' }),
};

// ── Evidence ──
export const evidence = {
  upload: (assessmentId: string, file: File, riskItemId?: string, description?: string) => {
    const fd = new FormData();
    fd.append('assessment_id', assessmentId);
    fd.append('file', file);
    if (riskItemId) fd.append('risk_item_id', riskItemId);
    if (description) fd.append('description', description);
    return multipartRequest('/evidence/upload', fd);
  },
  byAssessment: (assessmentId: string) => request(`/evidence/by-assessment/${assessmentId}`),
  delete: (id: string) => request(`/evidence/${id}`, { method: 'DELETE' }),
};

// ── Calendar ──
export const calendar = {
  get: (year: number, month: number) => request(`/calendar?year=${year}&month=${month}`),
};

// ── Watches ──
export const watches = {
  list: () => request('/watches'),
  watch: (regulationId: string) => request(`/watches/${regulationId}`, { method: 'POST' }),
  unwatch: (regulationId: string) => request(`/watches/${regulationId}`, { method: 'DELETE' }),
};

// ── Reports ──
export const reports = {
  assessment: (assessmentId: string, template: 'executive' | 'technical' | 'audit' = 'executive') =>
    fetch(`${API_BASE}/reports/assessment/${assessmentId}?template=${template}`, {
      headers: authHeaders(),
    }).then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.text();
    }),
  crossRegulation: (regulationIds: string[]) =>
    request(`/reports/cross-regulation?regulation_ids=${regulationIds.join(',')}`),
};

// ── AI ──
export const ai = {
  analyzeRegulation: (regulation_text: string, regulation_id?: string) =>
    request('/ai/analyze-regulation', {
      method: 'POST',
      body: JSON.stringify({ regulation_text, regulation_id }),
    }),
  riskAssessment: (organization_type: string, industry: string, current_practices: string[]) =>
    request('/ai/risk-assessment', {
      method: 'POST',
      body: JSON.stringify({ organization_type, industry, current_practices }),
    }),
  gapAnalysis: (regulation_id: string, stated_controls: string[]) =>
    request('/ai/gap-analysis', {
      method: 'POST',
      body: JSON.stringify({ regulation_id, stated_controls }),
    }),
  generatePolicy: (regulation_id: string, organization_name: string, organization_context?: string) =>
    request('/ai/generate-policy', {
      method: 'POST',
      body: JSON.stringify({ regulation_id, organization_name, organization_context }),
    }),
  chat: (message: string, session_id: string, context_assessment_id?: string, context_regulation_id?: string) =>
    request('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id, context_assessment_id, context_regulation_id }),
    }),
  chatHistory: (sessionId: string) => request(`/ai/chat/${sessionId}`),
  logs: (params: { page?: number; limit?: number; analysis_type?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.page) q.set('page', String(params.page));
    if (params.limit) q.set('limit', String(params.limit));
    if (params.analysis_type) q.set('analysis_type', params.analysis_type);
    return request(`/ai/logs${q.toString() ? '?' + q.toString() : ''}`);
  },
  // Apply pass 5 — additional AI helpers
  crossRegulationMapper: (regulation_ids: string[]) =>
    request('/ai/cross-regulation-mapper', {
      method: 'POST',
      body: JSON.stringify({ regulation_ids }),
    }),
  readinessSimulator: (data: { scenario?: string; regulation_id?: string; controls_in_place?: string[]; event?: string }) =>
    request('/ai/readiness-simulator', { method: 'POST', body: JSON.stringify(data) }),
  evidenceExtract: (data: { extracted_text: string; regulation_id?: string; document_type?: string }) =>
    request('/ai/evidence-extract', { method: 'POST', body: JSON.stringify(data) }),
  secEdgarFeed: (cik?: string) =>
    request('/ai/external-feed/sec-edgar', { method: 'POST', body: JSON.stringify({ cik }) }),
};
