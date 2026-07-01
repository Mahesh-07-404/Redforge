import React, { useState } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import { Settings as SettingsIcon, ShieldAlert, CheckCircle, Save, Moon, Sun, LogOut } from 'lucide-react';
import { RedForgeAPI } from '../services/api';

export const Settings: React.FC = () => {
  const { settings, updateSettings, logout } = useSettings();
  
  const [apiUrlInput, setApiUrlInput] = useState(settings.apiUrl);
  const [apiKeyInput, setApiKeyInput] = useState(settings.apiKey);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  
  const [submitting, setSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authSuccess, setAuthSuccess] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSaveConnectionSettings = (e: React.FormEvent) => {
    e.preventDefault();
    updateSettings({
      apiUrl: apiUrlInput.trim(),
      apiKey: apiKeyInput.trim(),
    });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;

    setSubmitting(true);
    setAuthError(null);
    setAuthSuccess(false);
    try {
      const authResponse = await RedForgeAPI.login(apiUrlInput.trim(), username.trim(), password.trim());
      if (authResponse && authResponse.access_token) {
        updateSettings({
          authToken: authResponse.access_token,
        });
        setAuthSuccess(true);
        setUsername('');
        setPassword('');
      } else {
        throw new Error('Access token not returned from API');
      }
    } catch (err: any) {
      setAuthError(err.message || 'Authentication failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground m-0">System Settings</h2>
          <p className="text-sm text-muted-foreground">Configure API gateway target endpoints, security keys, and user themes</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Connection card */}
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <SettingsIcon className="h-4 w-4 text-primary" /> API Connection & Authorization
            </h3>
          </div>
          <div className="p-6">
            <form onSubmit={handleSaveConnectionSettings} className="space-y-4">
              {/* API Base URL */}
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground uppercase font-semibold">API Gateway Base URL</label>
                <input
                  type="text"
                  required
                  value={apiUrlInput}
                  onChange={(e) => setApiUrlInput(e.target.value)}
                  placeholder="http://127.0.0.1:8000"
                  className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground font-mono"
                />
              </div>

              {/* API Key value */}
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground uppercase font-semibold">Static API Key (Optional)</label>
                <input
                  type="password"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder="rf_key_..."
                  className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground font-mono"
                />
                <span className="text-[10px] text-muted-foreground block">
                  API Key created in auth console can authenticate request contexts.
                </span>
              </div>

              <div className="flex items-center justify-between pt-2">
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold text-xs rounded shadow-[0_0_15px_rgba(170,59,255,0.25)] flex items-center gap-2 transition"
                >
                  <Save className="h-3.5 w-3.5" /> Save Configuration
                </button>
                {savedSuccess && (
                  <span className="text-emerald-400 text-xs font-semibold flex items-center gap-1.5 animate-in fade-in duration-300">
                    <CheckCircle className="h-4 w-4" /> Connection details saved
                  </span>
                )}
              </div>
            </form>
          </div>
        </div>

        {/* User Identity / JWT login card */}
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              User Authentication (JWT)
            </h3>
          </div>
          <div className="p-6">
            {settings.authToken ? (
              <div className="space-y-4">
                <div className="p-4 rounded border border-emerald-800/40 bg-emerald-950/20 text-emerald-300 text-xs flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 shrink-0 text-emerald-400" />
                  <span>Authenticated with active JWT token. Scopes: full admin access granted.</span>
                </div>
                <div className="p-3 bg-muted rounded border border-border">
                  <span className="text-[10px] text-muted-foreground uppercase font-semibold block">JWT Token Snippet</span>
                  <code className="text-[10px] font-mono break-all text-foreground">
                    {settings.authToken.substring(0, 30)}...
                  </code>
                </div>
                <button
                  onClick={logout}
                  className="px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 font-semibold text-xs rounded transition flex items-center gap-2"
                >
                  <LogOut className="h-3.5 w-3.5" /> De-authorize Token
                </button>
              </div>
            ) : (
              <form onSubmit={handleLogin} className="space-y-4">
                {authError && (
                  <div className="p-3 rounded border border-rose-800/40 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-rose-500" />
                    <span>{authError}</span>
                  </div>
                )}
                {authSuccess && (
                  <div className="p-3 rounded border border-emerald-800/40 bg-emerald-950/20 text-emerald-300 text-xs flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-emerald-500" />
                    <span>Authorized successfully!</span>
                  </div>
                )}

                {/* Username */}
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground uppercase font-semibold">Username</label>
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. operator"
                    className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground"
                  />
                </div>

                {/* Password */}
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground uppercase font-semibold">Password</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground"
                  />
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold text-xs rounded shadow-[0_0_15px_rgba(170,59,255,0.25)] flex items-center justify-center gap-2 transition"
                >
                  Authorize Operator Session
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
