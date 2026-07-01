import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RedForgeAPI } from './api';

describe('RedForge API Client Service Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('should fetch system health successfully', async () => {
    const mockHealthResponse = { status: 'healthy', version: '2.0.0' };
    const globalFetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockHealthResponse,
    });
    vi.stubGlobal('fetch', globalFetchMock);

    const result = await RedForgeAPI.getHealth('http://127.0.0.1:8000');
    expect(globalFetchMock).toHaveBeenCalledWith('http://127.0.0.1:8000/api/v1/health');
    expect(result).toEqual(mockHealthResponse);
  });

  it('should fetch metrics successfully', async () => {
    const mockMetrics = { total_requests: 120, uptime_seconds: 500.0, error_rate: 0.0 };
    const globalFetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockMetrics,
    });
    vi.stubGlobal('fetch', globalFetchMock);

    const result = await RedForgeAPI.getMetrics('http://127.0.0.1:8000');
    expect(globalFetchMock).toHaveBeenCalledWith('http://127.0.0.1:8000/metrics');
    expect(result).toEqual(mockMetrics);
  });

  it('should fetch session list using API keys and headers envelope', async () => {
    const mockPayload = [
      { id: 'sess-1', name: 'Acme Scan', mode: 'bugbounty', status: 'active' },
    ];
    const mockEnvelope = {
      status: 'success',
      payload: mockPayload,
      errors: [],
    };
    const globalFetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockEnvelope,
    });
    vi.stubGlobal('fetch', globalFetchMock);

    const result = await RedForgeAPI.listSessions('http://127.0.0.1:8000', 'rf_api_key_123', '');
    expect(globalFetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/v1/sessions',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          'X-API-Key': 'rf_api_key_123',
        }),
      })
    );
    expect(result).toEqual(mockPayload);
  });

  it('should throw an error when API returns error status envelope', async () => {
    const mockEnvelope = {
      status: 'error',
      errors: ['Session not found'],
    };
    const globalFetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => mockEnvelope,
    });
    vi.stubGlobal('fetch', globalFetchMock);

    await expect(
      RedForgeAPI.listSessions('http://127.0.0.1:8000', '', 'jwt_token_123')
    ).rejects.toThrow('Session not found');
  });

  it('should create WebSocket instance with correct token search query params', () => {
    const ws = RedForgeAPI.createWebSocket('http://127.0.0.1:8000', '/ws/chat', 'jwt_token_abc');
    expect(ws).toBeInstanceOf(WebSocket);
    // Note: in vitest/jsdom/node, URL structure will match ws://127.0.0.1:8000/ws/chat?token=jwt_token_abc
    expect(ws.url).toContain('ws://127.0.0.1:8000/ws/chat');
    expect(ws.url).toContain('token=jwt_token_abc');
  });
});
