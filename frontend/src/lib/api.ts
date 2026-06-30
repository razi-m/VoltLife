// API client — centralized fetch wrappers for the VoltLife backend

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:8000');

interface FetchOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options;
  
  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  const res = await fetch(`${API_BASE}${path}`, config);

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const err = data?.error || {};
    throw new ApiError(res.status, err.code || 'unknown', err.message || res.statusText);
  }

  return res.json();
}

// ─── Batteries ───────────────────────────────────
export const api = {
  batteries: {
    list: (params?: Record<string, string | number>) => {
      const qs = params ? '?' + new URLSearchParams(
        Object.entries(params).reduce((acc, [k, v]) => ({ ...acc, [k]: String(v) }), {} as Record<string, string>)
      ).toString() : '';
      return request<import('./types').BatteryListResponse>(`/api/v1/batteries${qs}`);
    },
    get: (id: number) =>
      request<import('./types').BatteryDetail>(`/api/v1/batteries/${id}`),
    getAadhaar: (id: number) =>
      request<import('./types').AadhaarPassport>(`/api/v1/batteries/${id}/aadhaar`),
    ingest: (batteries: unknown[]) =>
      request<{ job_id: string; accepted: number; rejected: number }>('/api/v1/batteries/ingest', {
        method: 'POST',
        body: { batteries },
      }),
  },

  // ─── Jobs ───────────────────────────────────
  jobs: {
    get: (jobId: string) =>
      request<import('./types').JobStatus>(`/api/v1/jobs/${jobId}`),
  },

  // ─── Sites ───────────────────────────────────
  sites: {
    list: () => request<{ items: import('./types').Site[] }>('/api/v1/sites'),
  },

  // ─── Impact ───────────────────────────────────
  impact: {
    summary: () => request<import('./types').ImpactSummary>('/api/v1/impact/summary'),
  },

  // ─── Dashboard ─────────────────────────────────
  dashboard: {
    stats: () => request<import('./types').DashboardStats>('/api/v1/dashboard/stats'),
  },

  // ─── Deployments ───────────────────────────────
  deployments: {
    list: (params?: Record<string, string | number>) => {
      const qs = params ? '?' + new URLSearchParams(
        Object.entries(params).reduce((acc, [k, v]) => ({ ...acc, [k]: String(v) }), {} as Record<string, string>)
      ).toString() : '';
      return request<{ items: import('./types').DeploymentItem[]; total: number; page: number }>(`/api/v1/deployments${qs}`);
    },
    approve: (id: number) =>
      request<{ id: number; status: string; message: string }>(`/api/v1/deployments/${id}/approve`, { method: 'PATCH' }),
  },

  // ─── Analytics ─────────────────────────────────
  analytics: {
    fleet: () => request<import('./types').FleetAnalytics>('/api/v1/analytics/fleet'),
  },

  // ─── AI Chat ───────────────────────────────────
  ai: {
    chat: (message: string) =>
      request<import('./types').ChatResponse>('/api/v1/ai/chat', {
        method: 'POST',
        body: { message },
      }),
    suggestions: () =>
      request<{ suggestions: string[] }>('/api/v1/ai/suggestions'),
  },

  // ─── Marketplace ─────────────────────────────────
  marketplace: {
    summary: () => request<{ total_asset_value: string; auctions_count: number; recently_sold: number; second_life_index: number }>('/api/v1/marketplace/summary'),
    auctions: (grade?: string) => {
      const qs = grade ? `?grade_filter=${grade}` : '';
      return request<{ id: number; bpan: string; grade: string; chemistry: string; current_bid: number; time_remaining: string; rated_capacity_kwh: number }[]>(`/api/v1/marketplace/auctions${qs}`);
    },
    bid: (id: number) => request<{ status: string; message: string; new_bid: number }>(`/api/v1/marketplace/auctions/${id}/bid`, { method: 'POST' }),
    lots: (params?: Record<string, string | number>) => {
      const qs = params ? '?' + new URLSearchParams(
        Object.entries(params).reduce((acc, [k, v]) => ({ ...acc, [k]: String(v) }), {} as Record<string, string>)
      ).toString() : '';
      return request<any[]>(`/api/v1/marketplace/lots${qs}`);
    },
    suppliers: () => request<any[]>('/api/v1/marketplace/suppliers'),
  },

  // ─── Suppliers ───────────────────────────────────
  suppliers: {
    dashboardStats: (token: string) =>
      request<any>('/api/v1/suppliers/dashboard/stats', {
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    dashboardInventory: (token: string) =>
      request<any[]>('/api/v1/suppliers/dashboard/inventory', {
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    dashboardOrders: (token: string) =>
      request<any[]>('/api/v1/suppliers/dashboard/orders', {
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    dashboardRequirements: (token: string) =>
      request<any[]>('/api/v1/suppliers/dashboard/requirements', {
        headers: { 'Authorization': `Bearer ${token}` }
      }),
  },


  // ─── Requirements ─────────────────────────────────
  requirements: {
    create: (useCaseText: string, token: string) =>
      request<any>('/api/v1/requirements', {
        method: 'POST',
        body: { use_case_text: useCaseText },
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    matches: (id: number, token: string) =>
      request<any[]>(`/api/v1/requirements/${id}/matches`, {
        headers: { 'Authorization': `Bearer ${token}` }
      }),
  },

  // ─── Quotes ────────────────────────────────────────
  quotes: {
    list: (token: string) =>
      request<any[]>('/api/v1/quotes', {
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    create: (lotId: number, quantity: number, token: string) =>
      request<any>('/api/v1/quotes', {
        method: 'POST',
        body: { inventory_lot_id: lotId, quantity },
        headers: { 'Authorization': `Bearer ${token}` }
      }),
  },

  // ─── Payments ──────────────────────────────────────
  payments: {
    checkoutSession: (quoteId: number, token: string) =>
      request<{ session_id: string; checkout_url: string }>('/api/v1/payments/checkout-session', {
        method: 'POST',
        body: { quote_id: quoteId },
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    mockConfirm: (sessionId: string, token: string) =>
      request<any>('/api/v1/payments/mock-confirm', {
        method: 'POST',
        body: { session_id: sessionId },
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    orders: (token: string) =>
      request<any[]>('/api/v1/payments/orders', {
        headers: { 'Authorization': `Bearer ${token}` }
      }),
  },

  // ─── Logistics ─────────────────────────────────────
  logistics: {
    tracking: (orderId: number, token: string) =>
      request<any>(`/api/v1/logistics/orders/${orderId}/tracking`, {
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    triggerCallback: (orderId: number, status: string) =>
      request<{ status: string; order_id: number; new_state: string }>('/api/v1/logistics/callback', {
        method: 'POST',
        body: { order_id: orderId, status }
      }),
    confirmReceipt: (orderId: number, token: string) =>
      request<{ status: string; order_id: number; new_state: string }>(`/api/v1/logistics/orders/${orderId}/confirm-receipt`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    raiseIssue: (orderId: number, issueText: string, token: string) =>
      request<{ status: string; ticket_id: number; order_id: number; issue_text: string }>(`/api/v1/logistics/orders/${orderId}/raise-issue`, {
        method: 'POST',
        body: { issue_text: issueText },
        headers: { 'Authorization': `Bearer ${token}` }
      }),
  },

  // ─── Subscriptions ──────────────────────────────
  subscriptions: {
    plans: () =>
      request<any[]>('/api/v1/subscriptions/plans'),
    status: (token: string) =>
      request<{ status: string; plan_name: string | null; expires_at: string | null }>('/api/v1/subscriptions/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    createSession: (planName: string, token: string) =>
      request<{ session_id: string; checkout_url: string | null; amount_paise: number; key_id: string; is_mock: boolean }>('/api/v1/subscriptions/create-session', {
        method: 'POST',
        body: { plan_name: planName },
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    verify: (payload: { plan_name: string; session_id: string }, token: string) =>
      request<{ status: string; subscription: any }>('/api/v1/subscriptions/verify', {
        method: 'POST',
        body: payload,
        headers: { 'Authorization': `Bearer ${token}` }
      }),
    cancel: (token: string) =>
      request<{ status: string; subscription: any }>('/api/v1/subscriptions/cancel', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      }),
  },

  // ─── Demo ──────────────────────────────────────
  demo: {
    reset: (demoKey: string) =>
      request<{ status: string; message: string }>('/api/v1/demo/reset', {
        method: 'POST',
        headers: { 'X-Demo-Key': demoKey },
      }),
    replay: (demoKey: string) =>
      request<{ status: string; message: string }>('/api/v1/demo/replay', {
        method: 'POST',
        headers: { 'X-Demo-Key': demoKey },
      }),
  },

  // ─── Aadhaar (public) ──────────────────────────
  aadhaar: {
    getPublic: (aadhaarId: string) =>
      request<import('./types').AadhaarPassport>(`/api/v1/aadhaar/${aadhaarId}`),
  },
};

export { ApiError };
export const WS_URL = (API_BASE.replace('http', 'ws')) + '/ws/feed';
