import { APIResponse } from '../types';

// Helper to get headers
function getHeaders(apiKey: string, authToken: string): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  } else if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }
  return headers;
}

// Global fetch wrapper that extracts the payload or throws
async function request<T>(
  url: string,
  options: RequestInit,
  apiKey: string,
  authToken: string
): Promise<T> {
  const finalOptions = {
    ...options,
    headers: {
      ...getHeaders(apiKey, authToken),
      ...(options.headers || {}),
    },
  };

  const response = await fetch(url, finalOptions);
  
  if (response.status === 204) {
    return {} as T;
  }

  const data: APIResponse<T> = await response.json();
  if (response.ok && data.status === 'success') {
    return data.payload;
  } else {
    const errMsg = data.errors?.join(', ') || 'API request failed';
    throw new Error(errMsg);
  }
}

export const RedForgeAPI = {
  // System/Health
  async getSystemInfo(apiUrl: string, apiKey = '', token = '') {
    return request<any>(`${apiUrl}/api/v1/system/info`, { method: 'GET' }, apiKey, token);
  },

  async getHealth(apiUrl: string) {
    const res = await fetch(`${apiUrl}/api/v1/health`);
    return res.json();
  },

  async getMetrics(apiUrl: string) {
    const res = await fetch(`${apiUrl}/metrics`);
    return res.json();
  },

  // Auth
  async login(apiUrl: string, username: string, password: string) {
    const res = await fetch(`${apiUrl}/api/v1/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.errors?.join(', ') || 'Login failed');
    }
    return data.payload; // access_token, token_type
  },

  async listApiKeys(apiUrl: string, apiKey: string, token: string) {
    return request<{ api_keys: any[]; total: number }>(
      `${apiUrl}/api/v1/auth/api-keys`,
      { method: 'GET' },
      apiKey,
      token
    );
  },

  async createApiKey(apiUrl: string, name: string, scopes: string[], apiKey: string, token: string) {
    return request<any>(
      `${apiUrl}/api/v1/auth/api-keys`,
      {
        method: 'POST',
        body: JSON.stringify({ name, scopes }),
      },
      apiKey,
      token
    );
  },

  async revokeApiKey(apiUrl: string, keyId: string, apiKey: string, token: string) {
    return request<void>(
      `${apiUrl}/api/v1/auth/api-keys/${keyId}`,
      { method: 'DELETE' },
      apiKey,
      token
    );
  },

  // Sessions
  async listSessions(apiUrl: string, apiKey = '', token = '') {
    return request<any[]>(`${apiUrl}/api/v1/sessions`, { method: 'GET' }, apiKey, token);
  },

  async createSession(apiUrl: string, sessionData: any, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/sessions`,
      {
        method: 'POST',
        body: JSON.stringify(sessionData),
      },
      apiKey,
      token
    );
  },

  async deleteSession(apiUrl: string, sessionId: string, apiKey = '', token = '') {
    return request<void>(
      `${apiUrl}/api/v1/sessions/${sessionId}`,
      { method: 'DELETE' },
      apiKey,
      token
    );
  },

  // Chat
  async sendChatMessage(apiUrl: string, message: string, sessionId: string, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/chat`,
      {
        method: 'POST',
        body: JSON.stringify({ message, session_id: sessionId, stream: false }),
      },
      apiKey,
      token
    );
  },

  async getConversationHistory(apiUrl: string, sessionId: string, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/conversations/${sessionId}`,
      { method: 'GET' },
      apiKey,
      token
    );
  },

  // Workflows
  async listWorkflows(apiUrl: string, apiKey = '', token = '') {
    return request<{ workflows: any[]; total: number }>(
      `${apiUrl}/api/v1/workflows`,
      { method: 'GET' },
      apiKey,
      token
    );
  },

  async startWorkflow(apiUrl: string, payload: any, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/workflows/run`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      apiKey,
      token
    );
  },

  async getWorkflowDetails(apiUrl: string, workflowId: string, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/workflows/${workflowId}`,
      { method: 'GET' },
      apiKey,
      token
    );
  },

  // Planner
  async generatePlan(apiUrl: string, payload: any, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/planner/plan`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      apiKey,
      token
    );
  },

  // Reasoning
  async requestReasoningDecision(apiUrl: string, payload: any, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/reasoning/decide`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      apiKey,
      token
    );
  },

  // Execution
  async executeTool(apiUrl: string, payload: any, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/execution/run`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      apiKey,
      token
    );
  },

  // Reports
  async generateReport(apiUrl: string, payload: any, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/reports/generate`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      apiKey,
      token
    );
  },

  async getRawMarkdownReport(apiUrl: string, sessionId: string, apiKey = '', token = '') {
    const res = await fetch(`${apiUrl}/api/v1/reports/${sessionId}/markdown`, {
      method: 'GET',
      headers: getHeaders(apiKey, token),
    });
    if (!res.ok) {
      throw new Error('Failed to fetch raw markdown report');
    }
    return res.text();
  },

  // Memory
  async storeMemory(apiUrl: string, payload: any, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/memory/store`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      apiKey,
      token
    );
  },

  async queryMemory(apiUrl: string, payload: any, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/memory/query`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      apiKey,
      token
    );
  },

  async flushMemory(apiUrl: string, sessionId: string, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/memory/session/${sessionId}`,
      { method: 'DELETE' },
      apiKey,
      token
    );
  },

  // Plugins
  async listPlugins(apiUrl: string, apiKey = '', token = '') {
    return request<{ plugins: any[]; total: number }>(
      `${apiUrl}/api/v1/plugins`,
      { method: 'GET' },
      apiKey,
      token
    );
  },

  async installPlugin(apiUrl: string, pluginId: string, version?: string, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/plugins/install`,
      {
        method: 'POST',
        body: JSON.stringify({ plugin_id: pluginId, version }),
      },
      apiKey,
      token
    );
  },

  async enablePlugin(apiUrl: string, pluginId: string, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/plugins/${pluginId}/enable`,
      { method: 'POST' },
      apiKey,
      token
    );
  },

  async disablePlugin(apiUrl: string, pluginId: string, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/plugins/${pluginId}/disable`,
      { method: 'POST' },
      apiKey,
      token
    );
  },

  async uninstallPlugin(apiUrl: string, pluginId: string, apiKey = '', token = '') {
    return request<void>(
      `${apiUrl}/api/v1/plugins/${pluginId}`,
      { method: 'DELETE' },
      apiKey,
      token
    );
  },

  // MCP
  async discoverMcp(apiUrl: string, apiKey = '', token = '') {
    return request<any>(
      `${apiUrl}/api/v1/mcp/discover`,
      { method: 'GET' },
      apiKey,
      token
    );
  },

  // WebSockets Connection Helper
  createWebSocket(apiUrl: string, path: string, token = ''): WebSocket {
    const wsUrl = new URL(apiUrl);
    wsUrl.protocol = wsUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    wsUrl.pathname = path;
    if (token) {
      wsUrl.searchParams.set('token', token);
    }
    return new WebSocket(wsUrl.toString());
  },
};
