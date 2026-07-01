import React, { useState, useEffect } from 'react';
import { useSession } from '../contexts/SessionContext';
import { useSettings } from '../contexts/SettingsContext';
import { RedForgeAPI } from '../services/api';
import { Database, Search, Plus, Trash2, Info, Compass } from 'lucide-react';

interface Memory {
  id: string;
  content: string;
  timestamp: string;
  tier: 'short' | 'long';
}

export const Memory: React.FC = () => {
  const { activeSession } = useSession();
  const { settings } = useSettings();

  const [memoryInput, setMemoryInput] = useState('');
  const [memoryTier, setMemoryTier] = useState<'short' | 'long'>('short');
  const [searchQuery, setSearchQuery] = useState('');
  const [memories, setMemories] = useState<Memory[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQueryResult = async (query = '') => {
    if (!activeSession) return;
    setLoading(true);
    setError(null);
    try {
      if (query.trim()) {
        const result = await RedForgeAPI.queryMemory(
          settings.apiUrl,
          { session_id: activeSession.id, query, top_k: 10 },
          settings.apiKey,
          settings.authToken
        );
        // Map query result list
        const list = (result.matches || result || []).map((m: any, idx: number) => ({
          id: m.id || `q-${idx}`,
          content: m.content || m.text || '',
          timestamp: m.timestamp || new Date().toISOString(),
          tier: m.tier || 'short',
        }));
        setMemories(list);
      } else {
        // Mock session note memories
        setMemories([
          {
            id: 'mem-001',
            content: 'Acme targets login endpoint at /api/v1/auth/login.',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            tier: 'short',
          },
          {
            id: 'mem-002',
            content: 'Nmap ports scanned: 80, 443, 8080.',
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            tier: 'short',
          },
        ]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to query memory database');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueryResult();
  }, [activeSession]);

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!memoryInput.trim() || !activeSession) return;

    setSubmitting(true);
    setError(null);
    try {
      await RedForgeAPI.storeMemory(
        settings.apiUrl,
        {
          session_id: activeSession.id,
          content: memoryInput.trim(),
          tier: memoryTier,
        },
        settings.apiKey,
        settings.authToken
      );
      
      const newEntry: Memory = {
        id: `mem-${Date.now()}`,
        content: memoryInput.trim(),
        timestamp: new Date().toISOString(),
        tier: memoryTier,
      };
      
      setMemories((prev) => [newEntry, ...prev]);
      setMemoryInput('');
    } catch (err: any) {
      setError(err.message || 'Failed to store new operations memory');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFlushMemory = async () => {
    if (!activeSession) return;
    if (window.confirm('Are you sure you want to flush short term session memory? Long term models persist.')) {
      setError(null);
      try {
        await RedForgeAPI.flushMemory(settings.apiUrl, activeSession.id, settings.apiKey, settings.authToken);
        setMemories([]);
        fetchQueryResult();
      } catch (err: any) {
        setError(err.message || 'Failed to flush short-term memories');
      }
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground m-0">Memory Base</h2>
          <p className="text-sm text-muted-foreground">Manage operation notes, targets knowledge, and context scopes</p>
        </div>
        {activeSession && (
          <button
            onClick={handleFlushMemory}
            className="px-3 py-1.5 bg-rose-500/10 border border-rose-500/20 rounded text-rose-400 text-xs font-semibold hover:bg-rose-500/20 transition"
          >
            Flush short term memory
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 rounded border border-rose-800/40 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2">
          <Info className="h-4 w-4 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        {/* Add Note Card */}
        <div className="md:col-span-1 rounded-lg border border-border bg-card overflow-hidden">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <Plus className="h-4 w-4 text-primary" /> Store Operations Note
            </h3>
          </div>
          <div className="p-6">
            {!activeSession ? (
              <div className="text-center py-4 text-xs text-muted-foreground">
                Please select an active target session to add note memories.
              </div>
            ) : (
              <form onSubmit={handleAddMemory} className="space-y-4">
                {/* Content input */}
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground uppercase font-semibold">Note content</label>
                  <textarea
                    required
                    rows={3}
                    value={memoryInput}
                    onChange={(e) => setMemoryInput(e.target.value)}
                    placeholder="e.g. Acme endpoints use Bearer JWT authentication schema."
                    className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground placeholder:text-muted-foreground/60"
                  />
                </div>

                {/* Tier */}
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground uppercase font-semibold">Memory Tier</label>
                  <select
                    value={memoryTier}
                    onChange={(e) => setMemoryTier(e.target.value as any)}
                    className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground"
                  >
                    <option value="short" className="bg-card">Short Term (Active session context)</option>
                    <option value="long" className="bg-card">Long Term (RAG knowledge base)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold text-xs rounded shadow-[0_0_15px_rgba(170,59,255,0.25)] flex items-center justify-center gap-2 transition"
                >
                  <Database className="h-3.5 w-3.5" /> Store Operations Note
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Query Memory Grid list */}
        <div className="md:col-span-2 rounded-lg border border-border bg-card overflow-hidden flex flex-col h-[400px]">
          <div className="p-6 border-b border-border bg-card/50 flex items-center justify-between">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <Database className="h-4 w-4 text-primary" /> Stored Memories
            </h3>
            {/* Search query box */}
            <div className="relative w-48">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search notes..."
                className="w-full pl-8 pr-3 py-1 rounded border border-border bg-muted/40 text-xs focus:outline-none focus:border-primary text-foreground"
              />
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            </div>
          </div>
          <div className="p-6 flex-1 overflow-y-auto space-y-4">
            {loading ? (
              <div className="text-center py-8 text-xs text-muted-foreground">Querying memory indexes...</div>
            ) : memories.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">
                No memories found matching current context queries.
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {memories.map((mem) => (
                  <div key={mem.id} className="p-4 rounded border border-border bg-muted/30 flex flex-col justify-between">
                    <p className="text-xs text-foreground font-light">{mem.content}</p>
                    <div className="mt-4 pt-2 border-t border-border/40 flex items-center justify-between text-[10px] text-muted-foreground uppercase font-semibold">
                      <span>Tier: {mem.tier}</span>
                      <span>{new Date(mem.timestamp).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
