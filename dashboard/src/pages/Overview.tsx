import React, { useEffect, useState } from 'react';
import { useSession } from '../contexts/SessionContext';
import { useSettings } from '../contexts/SettingsContext';
import { RedForgeAPI } from '../services/api';
import { Finding, WorkflowRun } from '../types';
import {
  ShieldAlert,
  Server,
  Workflow,
  PlusCircle,
  FileCode,
  TrendingUp,
  Activity,
  Layers,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export const Overview: React.FC = () => {
  const { activeSession, sessions } = useSession();
  const { settings } = useSettings();
  const [metrics, setMetrics] = useState<any>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [activeWorkflows, setActiveWorkflows] = useState<WorkflowRun[]>([]);
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch System Metrics & Info
        const [sysData, metData] = await Promise.all([
          RedForgeAPI.getSystemInfo(settings.apiUrl, settings.apiKey, settings.authToken).catch(() => null),
          RedForgeAPI.getMetrics(settings.apiUrl).catch(() => null),
        ]);
        setSystemInfo(sysData);
        setMetrics(metData);

        // If there's an active session, load findings & active workflows
        if (activeSession) {
          // Fetch session findings (can extract from report generate or session details if available, or call report engine)
          // We can call generateReport dry-run or memory queries to get information
          const report = await RedForgeAPI.generateReport(
            settings.apiUrl,
            { session_id: activeSession.id, format: 'json' },
            settings.apiKey,
            settings.authToken
          ).catch(() => null);
          
          if (report && report.content) {
            try {
              const parsed = JSON.parse(report.content);
              setFindings(parsed.findings || []);
            } catch {
              // Parse findings from severity summary or similar
              setFindings([]);
            }
          } else {
            setFindings([]);
          }

          // Mock active workflows associated with session
          setActiveWorkflows([
            {
              workflow_id: 'recon_scan',
              run_id: 'run-9988',
              status: 'running',
              session_id: activeSession.id,
              started_at: new Date(Date.now() - 300000).toISOString(),
            },
          ]);
        } else {
          setFindings([]);
          setActiveWorkflows([]);
        }
      } catch (err) {
        console.error('Error fetching dashboard summary:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [activeSession, settings.apiUrl, settings.apiKey, settings.authToken]);

  // Summarize severities
  const severityCount = findings.reduce(
    (acc, f) => {
      const sev = f.severity?.toLowerCase() as any;
      if (acc[sev] !== undefined) {
        acc[sev]++;
      }
      return acc;
    },
    { critical: 0, high: 0, medium: 0, low: 0, info: 0 } as Record<string, number>
  );

  const getSeverityBg = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'bg-rose-950/40 text-rose-400 border-rose-800/60';
      case 'high':
        return 'bg-orange-950/40 text-orange-400 border-orange-800/60';
      case 'medium':
        return 'bg-amber-950/40 text-amber-400 border-amber-800/60';
      case 'low':
        return 'bg-blue-950/40 text-blue-400 border-blue-800/60';
      default:
        return 'bg-slate-900 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Welcome Banner */}
      <div className="p-6 rounded-lg border border-border bg-gradient-to-r from-primary/10 via-background to-background flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground">Welcome to RedForge Operations Control</h2>
          <p className="text-sm text-muted-foreground">
            {activeSession
              ? `Currently targeting ${activeSession.target || 'local workspace'} in ${activeSession.mode} mode.`
              : 'Select or create a new session to begin security scans.'}
          </p>
        </div>
        {!activeSession && (
          <button
            onClick={() => navigate('/sessions')}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-semibold rounded-md hover:bg-primary/90 transition shadow-[0_0_15px_rgba(170,59,255,0.3)]"
          >
            <PlusCircle className="h-4 w-4" /> Create Session
          </button>
        )}
      </div>

      {/* Metrics Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Metric 1 */}
        <div className="rounded-lg border border-border bg-card p-6 flex items-center justify-between">
          <div>
            <span className="text-xs text-muted-foreground uppercase tracking-widest">Target Vulnerabilities</span>
            <div className="text-2xl font-bold mt-1 text-foreground flex items-baseline gap-2">
              {findings.length}
              {findings.length > 0 && (
                <span className="text-xs text-rose-500 font-medium">
                  {severityCount.critical + severityCount.high} severe
                </span>
              )}
            </div>
          </div>
          <div className="h-10 w-10 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <ShieldAlert className="h-5 w-5" />
          </div>
        </div>

        {/* Metric 2 */}
        <div className="rounded-lg border border-border bg-card p-6 flex items-center justify-between">
          <div>
            <span className="text-xs text-muted-foreground uppercase tracking-widest">Active Sessions</span>
            <div className="text-2xl font-bold mt-1 text-foreground">{sessions.length}</div>
          </div>
          <div className="h-10 w-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
            <Layers className="h-5 w-5" />
          </div>
        </div>

        {/* Metric 3 */}
        <div className="rounded-lg border border-border bg-card p-6 flex items-center justify-between">
          <div>
            <span className="text-xs text-muted-foreground uppercase tracking-widest">Uptime</span>
            <div className="text-2xl font-bold mt-1 text-foreground">
              {metrics ? `${Math.round(metrics.uptime_seconds / 60)}m` : 'N/A'}
            </div>
          </div>
          <div className="h-10 w-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Activity className="h-5 w-5" />
          </div>
        </div>

        {/* Metric 4 */}
        <div className="rounded-lg border border-border bg-card p-6 flex items-center justify-between">
          <div>
            <span className="text-xs text-muted-foreground uppercase tracking-widest">Total API Requests</span>
            <div className="text-2xl font-bold mt-1 text-foreground">
              {metrics ? metrics.total_requests : 'N/A'}
            </div>
          </div>
          <div className="h-10 w-10 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <Server className="h-5 w-5" />
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Running Workflows */}
        <div className="rounded-lg border border-border bg-card flex flex-col overflow-hidden">
          <div className="p-6 border-b border-border flex items-center justify-between bg-card/50">
            <h3 className="font-bold text-sm text-foreground uppercase tracking-widest flex items-center gap-2">
              <Workflow className="h-4 w-4 text-primary" /> Active Workflows
            </h3>
            <Link to="/workflows" className="text-xs text-primary font-semibold hover:underline">
              View All
            </Link>
          </div>
          <div className="p-6 flex-1 flex flex-col justify-center">
            {activeWorkflows.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">
                No active workflow runs for the current session.
              </div>
            ) : (
              <div className="space-y-4">
                {activeWorkflows.map((run) => (
                  <div key={run.run_id} className="p-4 rounded border border-border bg-muted/30 flex items-center justify-between">
                    <div>
                      <div className="text-sm font-semibold text-foreground">{run.workflow_id}</div>
                      <div className="text-xs text-muted-foreground">ID: {run.run_id} • Started: {new Date(run.started_at).toLocaleTimeString()}</div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 uppercase tracking-widest animate-pulse">
                      {run.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Severity Summary */}
        <div className="rounded-lg border border-border bg-card flex flex-col overflow-hidden">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-sm text-foreground uppercase tracking-widest flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" /> Vulnerability Severity Breakdown
            </h3>
          </div>
          <div className="p-6 flex-1 flex flex-col justify-center space-y-3">
            {findings.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">
                No findings reported yet. Start scanning to populate vulnerabilities.
              </div>
            ) : (
              <>
                <div className="flex justify-between items-center text-xs text-muted-foreground">
                  <span>Critical & High</span>
                  <span>{severityCount.critical + severityCount.high} total</span>
                </div>
                <div className="w-full bg-muted rounded-full h-3 overflow-hidden flex">
                  <div
                    style={{ width: `${(severityCount.critical / findings.length) * 100}%` }}
                    className="bg-rose-500 h-full"
                    title={`Critical: ${severityCount.critical}`}
                  />
                  <div
                    style={{ width: `${(severityCount.high / findings.length) * 100}%` }}
                    className="bg-orange-500 h-full"
                    title={`High: ${severityCount.high}`}
                  />
                  <div
                    style={{ width: `${(severityCount.medium / findings.length) * 100}%` }}
                    className="bg-amber-500 h-full"
                    title={`Medium: ${severityCount.medium}`}
                  />
                  <div
                    style={{ width: `${(severityCount.low / findings.length) * 100}%` }}
                    className="bg-blue-500 h-full"
                    title={`Low: ${severityCount.low}`}
                  />
                </div>
                <div className="grid grid-cols-5 gap-2 pt-2 text-center text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  <div className="p-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    Crit: {severityCount.critical}
                  </div>
                  <div className="p-1 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">
                    High: {severityCount.high}
                  </div>
                  <div className="p-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    Med: {severityCount.medium}
                  </div>
                  <div className="p-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    Low: {severityCount.low}
                  </div>
                  <div className="p-1 rounded bg-slate-500/10 text-slate-400 border border-slate-500/20">
                    Info: {severityCount.info}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Recent Findings Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="p-6 border-b border-border bg-card/50 flex items-center justify-between">
          <h3 className="font-bold text-sm text-foreground uppercase tracking-widest flex items-center gap-2">
            <FileCode className="h-4 w-4 text-primary" /> Recent Findings
          </h3>
          <Link to="/evidence" className="text-xs text-primary font-semibold hover:underline">
            Browse Evidence
          </Link>
        </div>
        <div className="overflow-x-auto">
          {findings.length === 0 ? (
            <div className="text-center py-12 text-sm text-muted-foreground">
              No recent findings for the active session. Run port scans or vulnerability probes.
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/20 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  <th className="p-4">Severity</th>
                  <th className="p-4">Title</th>
                  <th className="p-4">Tool</th>
                  <th className="p-4">CVEs</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {findings.slice(0, 5).map((f) => (
                  <tr key={f.id} className="hover:bg-muted/10 transition text-xs">
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wider ${getSeverityBg(f.severity)}`}>
                        {f.severity}
                      </span>
                    </td>
                    <td className="p-4 font-semibold text-foreground">{f.title}</td>
                    <td className="p-4 text-muted-foreground font-mono">{f.tool || 'manual'}</td>
                    <td className="p-4 text-muted-foreground">
                      {f.cve && f.cve.length > 0 ? (
                        <div className="flex gap-1">
                          {f.cve.map((c) => (
                            <span key={c} className="bg-muted px-1.5 py-0.5 rounded text-[10px] text-foreground border border-border">
                              {c}
                            </span>
                          ))}
                        </div>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
