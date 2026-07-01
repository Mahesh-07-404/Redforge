import React, { useEffect, useState, useRef } from 'react';
import { useSession } from '../contexts/SessionContext';
import { useSettings } from '../contexts/SettingsContext';
import { RedForgeAPI } from '../services/api';
import { Play, Activity, CheckCircle, AlertCircle, Compass, History } from 'lucide-react';

interface Workflow {
  id: string;
  name: string;
  description: string;
  stages: string[];
}

interface WorkflowRunState {
  workflow_id: string;
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  currentStage?: string;
  progress: number;
  stagesCompleted: string[];
}

export const Workflows: React.FC = () => {
  const { activeSession } = useSession();
  const { settings } = useSettings();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState('');
  const [targetOverride, setTargetOverride] = useState('');
  
  const [activeRun, setActiveRun] = useState<WorkflowRunState | null>(null);
  const [historyRuns, setHistoryRuns] = useState<WorkflowRunState[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  // Load available workflows
  useEffect(() => {
    const fetchWf = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await RedForgeAPI.listWorkflows(settings.apiUrl, settings.apiKey, settings.authToken);
        // Map raw response
        const mapped = (data.workflows || []).map((w: any) => ({
          id: w.id || w.workflow_id,
          name: w.name || w.id,
          description: w.description || 'No description provided.',
          stages: w.stages || ['recon', 'scan', 'exploit', 'report'],
        }));
        setWorkflows(mapped);
        if (mapped.length > 0) {
          setSelectedWorkflowId(mapped[0].id);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load workflows list');
      } finally {
        setLoading(false);
      }
    };
    fetchWf();
  }, [settings.apiUrl, settings.apiKey, settings.authToken]);

  const handleStartWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSession || !selectedWorkflowId || activeRun) return;

    setError(null);
    try {
      const target = targetOverride.trim() || activeSession.target || '';
      if (!target) {
        throw new Error('Please specify a scan target either in the active session or override it here.');
      }

      // Start workflow via API
      const result = await RedForgeAPI.startWorkflow(
        settings.apiUrl,
        {
          workflow_id: selectedWorkflowId,
          target,
          session_id: activeSession.id,
          parameters: {},
        },
        settings.apiKey,
        settings.authToken
      );

      const runId = result.run_id || `run-${Date.now().toString().slice(-4)}`;
      
      // Initialize Run Progress state
      const initialRun: WorkflowRunState = {
        workflow_id: selectedWorkflowId,
        run_id: runId,
        status: 'running',
        progress: 0.1,
        stagesCompleted: [],
      };
      setActiveRun(initialRun);

      // Connect to WebSocket /ws/workflow to track progress
      const socket = RedForgeAPI.createWebSocket(settings.apiUrl, '/ws/workflow', settings.authToken);
      wsRef.current = socket;

      socket.onopen = () => {
        socket.send(
          JSON.stringify({
            session_id: activeSession.id,
            workflow_id: selectedWorkflowId,
            target,
          })
        );
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.event_type === 'workflow_stage') {
            setActiveRun((prev) => {
              if (!prev) return null;
              const completed = [...prev.stagesCompleted];
              if (data.stage && !completed.includes(data.stage)) {
                completed.push(data.stage);
              }
              return {
                ...prev,
                currentStage: data.stage,
                progress: data.progress || prev.progress,
                stagesCompleted: completed,
              };
            });
          } else if (data.event_type === 'workflow_done') {
            setActiveRun((prev) => {
              if (!prev) return null;
              const finalState: WorkflowRunState = {
                ...prev,
                status: 'completed',
                progress: 1.0,
              };
              // Add to history
              setHistoryRuns((hist) => [finalState, ...hist]);
              return null;
            });
            socket.close();
          } else if (data.event_type === 'error') {
            setActiveRun((prev) => {
              if (!prev) return null;
              const finalState: WorkflowRunState = {
                ...prev,
                status: 'failed',
              };
              setHistoryRuns((hist) => [finalState, ...hist]);
              return null;
            });
            setError(data.message || 'Workflow execution error');
            socket.close();
          }
        } catch (err) {
          console.error('Failed to parse workflow progress event:', err);
        }
      };

      socket.onerror = () => {
        setError('Workflow WebSocket monitoring encountered an error.');
        setActiveRun(null);
      };

    } catch (err: any) {
      setError(err.message || 'Failed to start workflow execution');
      setActiveRun(null);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground m-0">Workflow Orchestrator</h2>
          <p className="text-sm text-muted-foreground">Launch and monitor modular security analysis procedures</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded border border-rose-800/40 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Launch panel */}
        <div className="md:col-span-1 rounded-lg border border-border bg-card overflow-hidden">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <Play className="h-4 w-4 text-primary" /> Start Security Workflow
            </h3>
          </div>
          <div className="p-6">
            {!activeSession ? (
              <div className="text-center py-4 text-xs text-muted-foreground">
                Please select an active session in the header first to launch a workflow.
              </div>
            ) : (
              <form onSubmit={handleStartWorkflow} className="space-y-4">
                {/* Select Workflow */}
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground uppercase font-semibold">Select Template</label>
                  <select
                    value={selectedWorkflowId}
                    onChange={(e) => setSelectedWorkflowId(e.target.value)}
                    disabled={activeRun !== null || loading}
                    className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground"
                  >
                    {workflows.map((w) => (
                      <option key={w.id} value={w.id} className="bg-card">
                        {w.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Target override */}
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground uppercase font-semibold">Target Override (Optional)</label>
                  <input
                    type="text"
                    value={targetOverride}
                    onChange={(e) => setTargetOverride(e.target.value)}
                    disabled={activeRun !== null}
                    placeholder={activeSession?.target || 'e.g. example.com'}
                    className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground placeholder:text-muted-foreground/60"
                  />
                  <span className="text-[10px] text-muted-foreground block">
                    Defaults to session target: <span className="font-semibold text-foreground">{activeSession.target || 'None'}</span>
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={activeRun !== null || !selectedWorkflowId}
                  className="w-full py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold text-xs rounded shadow-[0_0_15px_rgba(170,59,255,0.25)] flex items-center justify-center gap-2 transition disabled:opacity-50"
                >
                  <Play className="h-3.5 w-3.5" /> Launch Workflow
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Status / Monitoring panel */}
        <div className="md:col-span-2 rounded-lg border border-border bg-card overflow-hidden flex flex-col">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <Activity className="h-4 w-4 text-primary" /> Active Workflow Status
            </h3>
          </div>
          <div className="p-6 flex-1 flex flex-col justify-center">
            {!activeRun ? (
              <div className="text-center py-12 text-sm text-muted-foreground">
                No workflows currently running. Launch a new template on the left panel to begin monitoring.
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-base text-foreground m-0">{activeRun.workflow_id}</h4>
                    <span className="text-[10px] font-mono text-muted-foreground block">Run ID: {activeRun.run_id}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 uppercase tracking-widest animate-pulse">
                    {activeRun.status}
                  </span>
                </div>

                {/* Progress bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Progress</span>
                    <span>{Math.round(activeRun.progress * 100)}%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2.5 overflow-hidden">
                    <div
                      style={{ width: `${activeRun.progress * 100}%` }}
                      className="bg-primary h-full transition-all duration-500 shadow-[0_0_10px_rgba(170,59,255,0.4)]"
                    />
                  </div>
                </div>

                {/* Stage logs */}
                <div className="space-y-2">
                  <span className="text-xs text-muted-foreground uppercase font-semibold">Executed Stages</span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {workflows
                      .find((w) => w.id === activeRun.workflow_id)
                      ?.stages.map((stage) => {
                        const isCompleted = activeRun.stagesCompleted.includes(stage);
                        const isCurrent = activeRun.currentStage === stage;
                        return (
                          <div
                            key={stage}
                            className={`p-3 rounded border flex items-center justify-between font-mono ${
                              isCompleted
                                ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-400'
                                : isCurrent
                                ? 'bg-primary/10 border-primary/40 text-primary'
                                : 'bg-muted/10 border-border/40 text-muted-foreground'
                            }`}
                          >
                            <span className="capitalize">{stage}</span>
                            {isCompleted ? (
                              <CheckCircle className="h-4 w-4 shrink-0 text-emerald-400" />
                            ) : isCurrent ? (
                              <Activity className="h-4 w-4 shrink-0 text-primary animate-spin" />
                            ) : (
                              <Compass className="h-4 w-4 shrink-0 text-muted-foreground/40" />
                            )}
                          </div>
                        );
                      })}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* History */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="p-6 border-b border-border bg-card/50">
          <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
            <History className="h-4 w-4 text-primary" /> Execution History
          </h3>
        </div>
        <div className="overflow-x-auto">
          {historyRuns.length === 0 ? (
            <div className="text-center py-8 text-sm text-muted-foreground">
              No workflow runs in current dashboard session memory. Runs executed will populate here.
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/20 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  <th className="p-4">Workflow Name</th>
                  <th className="p-4">Run ID</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60 text-xs">
                {historyRuns.map((r, idx) => (
                  <tr key={idx} className="hover:bg-muted/10 transition">
                    <td className="p-4 font-semibold text-foreground">{r.workflow_id}</td>
                    <td className="p-4 font-mono text-muted-foreground">{r.run_id}</td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-widest">
                        {r.status}
                      </span>
                    </td>
                    <td className="p-4 text-muted-foreground">Completed successfully</td>
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
