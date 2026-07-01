import React, { useState } from 'react';
import { useSession } from '../contexts/SessionContext';
import { SessionMode, AutonomyLevel } from '../types';
import { Layers, Plus, Trash2, CheckCircle, ExternalLink, Shield } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Sessions: React.FC = () => {
  const { sessions, activeSessionId, setActiveSessionId, createSession, deleteSession, loading, error } = useSession();
  const navigate = useNavigate();

  // Create session form states
  const [name, setName] = useState('');
  const [mode, setMode] = useState<SessionMode>('bugbounty');
  const [target, setTarget] = useState('');
  const [autonomy, setAutonomy] = useState<AutonomyLevel>('manual');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setSubmitting(true);
    setFormError(null);
    try {
      await createSession({
        name: name.trim(),
        mode,
        target: target.trim() || undefined,
        autonomy,
      });
      // Reset form
      setName('');
      setTarget('');
      navigate('/');
    } catch (err: any) {
      setFormError(err.message || 'Failed to create session');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to permanently delete session "${name}"?`)) {
      try {
        await deleteSession(id);
      } catch (err: any) {
        alert(err.message || 'Failed to delete session');
      }
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground m-0">Target Sessions</h2>
          <p className="text-sm text-muted-foreground">Manage active security operations, scopes, and session contexts</p>
        </div>
      </div>

      {(error || formError) && (
        <div className="p-4 rounded border border-rose-800/40 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2">
          <span>{error || formError}</span>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        {/* Create Session Form */}
        <div className="md:col-span-1 rounded-lg border border-border bg-card overflow-hidden">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <Plus className="h-4 w-4 text-primary" /> Create New Session
            </h3>
          </div>
          <div className="p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Name */}
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground uppercase font-semibold">Session Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Acme Web Penetration Scan"
                  className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground placeholder:text-muted-foreground/60"
                />
              </div>

              {/* Mode */}
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground uppercase font-semibold">Session Mode</label>
                <select
                  value={mode}
                  onChange={(e) => setMode(e.target.value as SessionMode)}
                  className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground"
                >
                  <option value="bugbounty" className="bg-card">Bug Bounty Mode</option>
                  <option value="pentest" className="bg-card">Pentesting Mode</option>
                  <option value="ctf" className="bg-card">CTF solver Mode</option>
                  <option value="learning" className="bg-card">Learning Mode</option>
                  <option value="coding" className="bg-card">Coding Mode</option>
                  <option value="android" className="bg-card">Android Pentest Mode</option>
                </select>
              </div>

              {/* Target */}
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground uppercase font-semibold">Target Domain / IP / URL</label>
                <input
                  type="text"
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  placeholder="e.g. scanme.nmap.org"
                  className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground placeholder:text-muted-foreground/60"
                />
              </div>

              {/* Autonomy */}
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground uppercase font-semibold">Autonomy Level</label>
                <select
                  value={autonomy}
                  onChange={(e) => setAutonomy(e.target.value as AutonomyLevel)}
                  className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground"
                >
                  <option value="manual" className="bg-card">Manual (Strict Gate Approval)</option>
                  <option value="semi" className="bg-card">Semi-Autonomous (Confirm high-risk)</option>
                  <option value="full" className="bg-card">Fully Autonomous (Auto-run scans)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold text-xs rounded shadow-[0_0_15px_rgba(170,59,255,0.25)] flex items-center justify-center gap-2 transition"
              >
                <Plus className="h-3.5 w-3.5" /> Initialize Session
              </button>
            </form>
          </div>
        </div>

        {/* Sessions list */}
        <div className="md:col-span-2 rounded-lg border border-border bg-card overflow-hidden flex flex-col">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <Layers className="h-4 w-4 text-primary" /> Configured Sessions
            </h3>
          </div>
          <div className="p-6 flex-1">
            {loading && sessions.length === 0 ? (
              <div className="text-center py-12 text-sm text-muted-foreground">Loading sessions list...</div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-12 text-sm text-muted-foreground">
                No active targets configured. Setup a new target session on the left card to get started.
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {sessions.map((sess) => {
                  const isActive = activeSessionId === sess.id;
                  return (
                    <div
                      key={sess.id}
                      className={`p-5 rounded-lg border flex flex-col justify-between transition-all duration-200 ${
                        isActive
                          ? 'border-primary bg-primary/5 shadow-[0_0_15px_rgba(170,59,255,0.1)]'
                          : 'border-border bg-muted/20 hover:border-border/80'
                      }`}
                    >
                      <div>
                        <div className="flex items-start justify-between">
                          <h4 className="font-bold text-sm text-foreground truncate max-w-[80%]" title={sess.name}>
                            {sess.name}
                          </h4>
                          {isActive && (
                            <span className="flex items-center gap-1 text-[10px] font-bold text-primary uppercase tracking-wider">
                              <CheckCircle className="h-3.5 w-3.5 text-primary" /> Active
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] font-mono text-muted-foreground block select-all">ID: {sess.id}</span>

                        <div className="mt-4 space-y-1 text-xs text-muted-foreground">
                          <div className="flex justify-between">
                            <span>Target:</span>
                            <span className="font-semibold text-foreground truncate max-w-[150px]">{sess.target || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Mode:</span>
                            <span className="font-semibold text-foreground uppercase text-[10px]">{sess.mode}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Autonomy:</span>
                            <span className="font-semibold text-foreground uppercase text-[10px]">{sess.autonomy}</span>
                          </div>
                        </div>
                      </div>

                      <div className="mt-6 pt-3 border-t border-border/40 flex items-center justify-between">
                        <button
                          onClick={() => {
                            setActiveSessionId(sess.id);
                            navigate('/');
                          }}
                          className={`px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5 transition ${
                            isActive
                              ? 'bg-primary text-primary-foreground hover:bg-primary/95'
                              : 'bg-muted border border-border text-foreground hover:bg-muted/80'
                          }`}
                        >
                          <ExternalLink className="h-3 w-3" /> {isActive ? 'Open Dashboard' : 'Activate'}
                        </button>

                        <button
                          onClick={() => handleDelete(sess.id, sess.name)}
                          className="p-1.5 rounded border border-border hover:border-rose-900/60 text-muted-foreground hover:text-rose-500 hover:bg-rose-950/20 transition"
                          title="Delete Session"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
