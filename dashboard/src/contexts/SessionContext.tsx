import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Session } from '../types';
import { RedForgeAPI } from '../services/api';
import { useSettings } from './SettingsContext';

interface SessionContextType {
  sessions: Session[];
  activeSession: Session | null;
  activeSessionId: string | null;
  loading: boolean;
  error: string | null;
  setActiveSessionId: (id: string | null) => void;
  fetchSessions: () => Promise<void>;
  createSession: (sessionData: { mode: string; target?: string; autonomy: string; name: string }) => Promise<Session>;
  deleteSession: (id: string) => Promise<void>;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { settings } = useSettings();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionIdState] = useState<string | null>(() => {
    return localStorage.getItem('redforge_active_session_id') || null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setActiveSessionId = (id: string | null) => {
    setActiveSessionIdState(id);
    if (id) {
      localStorage.setItem('redforge_active_session_id', id);
    } else {
      localStorage.removeItem('redforge_active_session_id');
    }
  };

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await RedForgeAPI.listSessions(settings.apiUrl, settings.apiKey, settings.authToken);
      setSessions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch sessions');
    } finally {
      setLoading(false);
    }
  }, [settings.apiUrl, settings.apiKey, settings.authToken]);

  const createSession = async (sessionData: { mode: string; target?: string; autonomy: string; name: string }) => {
    setError(null);
    try {
      const newSession = await RedForgeAPI.createSession(
        settings.apiUrl,
        sessionData,
        settings.apiKey,
        settings.authToken
      );
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      return newSession;
    } catch (err: any) {
      const msg = err.message || 'Failed to create session';
      setError(msg);
      throw new Error(msg);
    }
  };

  const deleteSession = async (id: string) => {
    setError(null);
    try {
      await RedForgeAPI.deleteSession(settings.apiUrl, id, settings.apiKey, settings.authToken);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) {
        setActiveSessionId(null);
      }
    } catch (err: any) {
      const msg = err.message || 'Failed to delete session';
      setError(msg);
      throw new Error(msg);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;

  return (
    <SessionContext.Provider
      value={{
        sessions,
        activeSession,
        activeSessionId,
        loading,
        error,
        setActiveSessionId,
        fetchSessions,
        createSession,
        deleteSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};
