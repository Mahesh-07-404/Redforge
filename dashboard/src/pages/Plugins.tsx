import React, { useState, useEffect } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import { RedForgeAPI } from '../services/api';
import { Plugin } from '../types';
import { Grid, Plus, Trash2, ShieldAlert, CheckCircle } from 'lucide-react';

export const Plugins: React.FC = () => {
  const { settings } = useSettings();
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [pluginIdInput, setPluginIdInput] = useState('');
  const [pluginVersionInput, setPluginVersionInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPluginsList = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await RedForgeAPI.listPlugins(settings.apiUrl, settings.apiKey, settings.authToken);
      // Map to standard Plugin interfaces
      const mapped = (data.plugins || []).map((p: any) => ({
        plugin_id: p.plugin_id || p.id,
        name: p.name || p.plugin_id || p.id,
        version: p.version || '1.0.0',
        description: p.description || 'No description provided.',
        enabled: p.enabled ?? true,
        installed: p.installed ?? true,
      }));
      setPlugins(mapped);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch plugins list');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPluginsList();
  }, [settings.apiUrl]);

  const handleInstallPlugin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pluginIdInput.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await RedForgeAPI.installPlugin(
        settings.apiUrl,
        pluginIdInput.trim(),
        pluginVersionInput.trim() || undefined,
        settings.apiKey,
        settings.authToken
      );
      setPluginIdInput('');
      setPluginVersionInput('');
      fetchPluginsList();
    } catch (err: any) {
      setError(err.message || 'Failed to install plugin');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTogglePlugin = async (pluginId: string, currentlyEnabled: boolean) => {
    setError(null);
    try {
      if (currentlyEnabled) {
        await RedForgeAPI.disablePlugin(settings.apiUrl, pluginId, settings.apiKey, settings.authToken);
      } else {
        await RedForgeAPI.enablePlugin(settings.apiUrl, pluginId, settings.apiKey, settings.authToken);
      }
      setPlugins((prev) =>
        prev.map((p) => (p.plugin_id === pluginId ? { ...p, enabled: !currentlyEnabled } : p))
      );
    } catch (err: any) {
      setError(err.message || 'Failed to toggle plugin status');
    }
  };

  const handleUninstallPlugin = async (pluginId: string) => {
    if (window.confirm(`Are you sure you want to uninstall plugin "${pluginId}"?`)) {
      setError(null);
      try {
        await RedForgeAPI.uninstallPlugin(settings.apiUrl, pluginId, settings.apiKey, settings.authToken);
        setPlugins((prev) => prev.filter((p) => p.plugin_id !== pluginId));
      } catch (err: any) {
        setError(err.message || 'Failed to uninstall plugin');
      }
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground m-0">Plugins Manager</h2>
          <p className="text-sm text-muted-foreground">Install plugins, enable custom tools, and extend core OS functionality</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded border border-rose-800/40 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        {/* Install Plugin Form */}
        <div className="md:col-span-1 rounded-lg border border-border bg-card overflow-hidden">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <Plus className="h-4 w-4 text-primary" /> Install Plugin
            </h3>
          </div>
          <div className="p-6">
            <form onSubmit={handleInstallPlugin} className="space-y-4">
              {/* Plugin ID */}
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground uppercase font-semibold">Plugin Identifier (Registry ID)</label>
                <input
                  type="text"
                  required
                  value={pluginIdInput}
                  onChange={(e) => setPluginIdInput(e.target.value)}
                  placeholder="e.g. shodan-connector"
                  className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground placeholder:text-muted-foreground/60"
                />
              </div>

              {/* Version */}
              <div className="space-y-1">
                <label className="text-xs text-muted-foreground uppercase font-semibold">Version (Optional)</label>
                <input
                  type="text"
                  value={pluginVersionInput}
                  onChange={(e) => setPluginVersionInput(e.target.value)}
                  placeholder="e.g. 1.2.0"
                  className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground placeholder:text-muted-foreground/60 font-mono"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold text-xs rounded shadow-[0_0_15px_rgba(170,59,255,0.25)] flex items-center justify-center gap-2 transition"
              >
                <Grid className="h-3.5 w-3.5" /> Install Plugin
              </button>
            </form>
          </div>
        </div>

        {/* Plugins Grid list */}
        <div className="md:col-span-2 rounded-lg border border-border bg-card overflow-hidden flex flex-col">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <Grid className="h-4 w-4 text-primary" /> Installed Plugins
            </h3>
          </div>
          <div className="p-6 flex-1">
            {loading && plugins.length === 0 ? (
              <div className="text-center py-12 text-sm text-muted-foreground">Loading plugins list...</div>
            ) : plugins.length === 0 ? (
              <div className="text-center py-12 text-sm text-muted-foreground">
                No custom plugins installed. Add new custom extensions on the left form.
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {plugins.map((plugin) => (
                  <div
                    key={plugin.plugin_id}
                    className="p-4 rounded-lg border border-border bg-muted/30 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-bold text-sm text-foreground m-0">{plugin.name}</h4>
                          <span className="text-[9px] font-mono text-muted-foreground uppercase">Version: {plugin.version}</span>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold border uppercase tracking-wider ${
                          plugin.enabled
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-slate-500/15 text-slate-400 border-slate-500/25'
                        }`}>
                          {plugin.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                      <p className="mt-3 text-xs text-muted-foreground leading-normal font-light">{plugin.description}</p>
                    </div>

                    <div className="mt-6 pt-3 border-t border-border/40 flex items-center justify-between">
                      {/* Enable/Disable Toggle */}
                      <button
                        onClick={() => handleTogglePlugin(plugin.plugin_id, plugin.enabled)}
                        className={`px-2.5 py-1 rounded text-[10px] uppercase font-bold tracking-wider transition ${
                          plugin.enabled
                            ? 'bg-slate-500/20 hover:bg-slate-500/30 text-foreground border border-border'
                            : 'bg-primary/20 hover:bg-primary/25 text-primary border border-primary/30'
                        }`}
                      >
                        {plugin.enabled ? 'Disable' : 'Enable'}
                      </button>

                      {/* Uninstall */}
                      <button
                        onClick={() => handleUninstallPlugin(plugin.plugin_id)}
                        className="p-1.5 rounded border border-border hover:border-rose-900/60 text-muted-foreground hover:text-rose-500 hover:bg-rose-950/20 transition"
                        title="Uninstall Plugin"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
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
