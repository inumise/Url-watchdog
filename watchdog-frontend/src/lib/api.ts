const API_URL = import.meta.env.VITE_API_URL || '';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = localStorage.getItem('token');
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return { error: errorData.detail || `Error: ${response.status}` };
    }
    
    const data = await response.json();
    return { data };
  } catch (err) {
    return { error: 'Network error. Please try again.' };
  }
}

export interface User {
  id: string;
  email: string;
  subscription_status: string;
  created_at: string;
}

export interface Monitor {
  id: string;
  name: string;
  url: string;
  keywords: string[];
  check_frequency: number;
  is_active: boolean;
  created_at: string;
  last_checked: string | null;
  last_result: string | null;
  last_match_found: boolean;
}

export interface NotificationChannel {
  id: string;
  name: string;
  channel_type: 'email' | 'telegram' | 'webhook';
  is_active: boolean;
  created_at: string;
  config_masked: Record<string, string>;
}

export interface CheckLog {
  id: string;
  monitor_id: string;
  checked_at: string;
  success: boolean;
  match_found: boolean;
  matched_keywords: string[];
  error_message: string | null;
}

export const api = {
  auth: {
    register: (email: string, password: string) =>
      request<{ access_token: string; token_type: string }>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    
    login: (email: string, password: string) =>
      request<{ access_token: string; token_type: string }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    
    me: () => request<User>('/api/auth/me'),
  },
  
  monitors: {
    list: () => request<Monitor[]>('/api/monitors'),
    
    get: (id: string) => request<Monitor>(`/api/monitors/${id}`),
    
    create: (data: { name: string; url: string; keywords: string[]; check_frequency: number }) =>
      request<Monitor>('/api/monitors', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    
    update: (id: string, data: Partial<Monitor>) =>
      request<Monitor>(`/api/monitors/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    
    delete: (id: string) =>
      request<{ message: string }>(`/api/monitors/${id}`, {
        method: 'DELETE',
      }),
    
    triggerCheck: (id: string) =>
      request<{ message: string }>(`/api/monitors/${id}/check`, {
        method: 'POST',
      }),
    
    getLogs: (id: string) => request<CheckLog[]>(`/api/monitors/${id}/logs`),
  },
  
  notifications: {
    list: () => request<NotificationChannel[]>('/api/notifications'),
    
    create: (data: { name: string; channel_type: string; config: Record<string, string> }) =>
      request<NotificationChannel>('/api/notifications', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    
    update: (id: string, data: Partial<{ name: string; config: Record<string, string>; is_active: boolean }>) =>
      request<NotificationChannel>(`/api/notifications/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    
    delete: (id: string) =>
      request<{ message: string }>(`/api/notifications/${id}`, {
        method: 'DELETE',
      }),
  },
  
  billing: {
    createCheckout: (successUrl: string, cancelUrl: string) =>
      request<{ checkout_url: string }>('/api/billing/checkout', {
        method: 'POST',
        body: JSON.stringify({ success_url: successUrl, cancel_url: cancelUrl }),
      }),
    
    createPortal: (returnUrl: string) =>
      request<{ portal_url: string }>('/api/billing/portal', {
        method: 'POST',
        body: JSON.stringify({ return_url: returnUrl }),
      }),
  },
};
