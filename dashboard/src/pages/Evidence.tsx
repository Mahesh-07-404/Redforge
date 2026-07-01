import React, { useState, useEffect, useRef } from 'react';
import { useSession } from '../contexts/SessionContext';
import { useSettings } from '../contexts/SettingsContext';
import { RedForgeAPI } from '../services/api';
import { Terminal as TerminalIcon, Play, AlertOctagon, CheckCircle, RefreshCw } from 'lucide-react';

interface LogLine {
  text: string;
  stream: 'stdout' | 'stderr' | 'system';
}

interface TimelineItem {
  id: string;
  tool: string;
  command: string[];
  status: 'running' | 'completed' | 'failed';
  timestamp: string;
}

export const Evidence: React.FC = () => {
  const { activeSession } = useSession();
  const { settings } = useSettings();

  const [selectedTool, setSelectedTool] = useState('nmap');
  const [commandArgs, setCommandArgs] = useState('-sV');
  const [executing, setExecuting] = useState(false);
  const [logLines, setLogLines] = useState<LogLine[]>([]);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logLines]);

  const handleRunCommand = (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSession || executing) return;

    const target = activeSession.target || '127.0.0.1';
    // Construct command arguments list
    const parsedArgs = commandArgs.split(' ').filter(Boolean);
    const finalCommand = [selectedTool, ...parsedArgs, target];

    setExecuting(true);
    setError(null);
    setLogLines([
      { text: `[System] Dispatching command: ${finalCommand.join(' ')}`, stream: 'system' },
    ]);

    const runItem: TimelineItem = {
      id: `run-${Date.now()}`,
      tool: selectedTool,
      command: finalCommand,
      status: 'running',
      timestamp: new Date().toLocaleTimeString(),
    };
    setTimeline((prev) => [runItem, ...prev]);

    try {
      // Connect to tool execution WebSocket endpoint
      const socket = RedForgeAPI.createWebSocket(settings.apiUrl, '/ws/execution', settings.authToken);
      wsRef.current = socket;

      socket.onopen = () => {
        socket.send(
          JSON.stringify({
            session_id: activeSession.id,
            tool: selectedTool,
            command: finalCommand,
          })
        );
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.event_type === 'output') {
            setLogLines((prev) => [
              ...prev,
              { text: data.line || '', stream: data.stream || 'stdout' },
            ]);
          } else if (data.event_type === 'execution_done') {
            setLogLines((prev) => [
              ...prev,
              { text: `[System] Execution finished with exit code ${data.exit_code}. Status: ${data.status}`, stream: 'system' },
            ]);
            setTimeline((prevList) =>
              prevList.map((item) =>
                item.id === runItem.id
                  ? { ...item, status: data.status === 'completed' ? 'completed' : 'failed' }
                  : item
              )
            );
            socket.close();
            setExecuting(false);
          } else if (data.event_type === 'error') {
            setError(data.message || 'Tool execution failure');
            setLogLines((prev) => [
              ...prev,
              { text: `[System Error] ${data.message}`, stream: 'stderr' },
            ]);
            setTimeline((prevList) =>
              prevList.map((item) =>
                item.id === runItem.id ? { ...item, status: 'failed' } : item
              )
            );
            socket.close();
            setExecuting(false);
          }
        } catch (err) {
          console.error('Failed to parse output token:', err);
        }
      };

      socket.onerror = () => {
        setError('Tool execution WebSocket encountered an error.');
        setExecuting(false);
      };

      socket.onclose = () => {
        setExecuting(false);
      };

    } catch (err: any) {
      setError(err.message || 'Failed to start execution socket');
      setExecuting(false);
    }
  };

  const getLogLineColor = (stream: string) => {
    switch (stream) {
      case 'stderr':
        return 'text-rose-400';
      case 'system':
        return 'text-primary font-bold';
      default:
        return 'text-foreground';
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground m-0">Live Tool Runner & Evidence</h2>
          <p className="text-sm text-muted-foreground">Run target probes directly and view streamed output logs</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded border border-rose-800/40 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertOctagon className="h-4 w-4 shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        {/* Launcher parameters */}
        <div className="md:col-span-1 rounded-lg border border-border bg-card overflow-hidden">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <TerminalIcon className="h-4 w-4 text-primary" /> Command Parameters
            </h3>
          </div>
          <div className="p-6">
            {!activeSession ? (
              <div className="text-center py-4 text-xs text-muted-foreground">
                Please select an active target session to invoke tools.
              </div>
            ) : (
              <form onSubmit={handleRunCommand} className="space-y-4">
                {/* Select tool */}
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground uppercase font-semibold">Select Security Tool</label>
                  <select
                    value={selectedTool}
                    onChange={(e) => setSelectedTool(e.target.value)}
                    disabled={executing}
                    className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground"
                  >
                    <option value="nmap" className="bg-card">nmap (Port Scanner)</option>
                    <option value="subfinder" className="bg-card">subfinder (Subdomains)</option>
                    <option value="nuclei" className="bg-card">nuclei (Vulnerability Scanner)</option>
                    <option value="ffuf" className="bg-card">ffuf (Fuzzer)</option>
                    <option value="nikto" className="bg-card">nikto (Web Scanner)</option>
                    <option value="gobuster" className="bg-card">gobuster (Dir/DNS Buster)</option>
                    <option value="john" className="bg-card">john (Password Cracker)</option>
                  </select>
                </div>

                {/* Command parameters override */}
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground uppercase font-semibold">Command Flags</label>
                  <input
                    type="text"
                    value={commandArgs}
                    onChange={(e) => setCommandArgs(e.target.value)}
                    disabled={executing}
                    placeholder="-sV -T4"
                    className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground font-mono"
                  />
                </div>

                {/* Preview command */}
                <div className="p-3 bg-muted rounded border border-border space-y-1">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold block">Compiled Preview Command</span>
                  <code className="text-xs text-foreground font-semibold break-all">
                    {selectedTool} {commandArgs} {activeSession.target || '127.0.0.1'}
                  </code>
                </div>

                <button
                  type="submit"
                  disabled={executing}
                  className="w-full py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold text-xs rounded shadow-[0_0_15px_rgba(170,59,255,0.25)] flex items-center justify-center gap-2 transition disabled:opacity-50"
                >
                  {executing ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" /> Stream executing...
                    </>
                  ) : (
                    <>
                      <Play className="h-3.5 w-3.5" /> Execute Tool
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Live Terminal Log Output Console */}
        <div className="md:col-span-2 rounded-lg border border-border bg-card overflow-hidden flex flex-col h-[400px]">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <TerminalIcon className="h-4 w-4 text-primary" /> Live Stream console
            </h3>
          </div>
          <div className="p-4 flex-1 overflow-y-auto bg-black font-mono text-xs select-text space-y-1.5">
            {logLines.length === 0 ? (
              <div className="h-full flex items-center justify-center text-muted-foreground select-none">
                No active execution. Command output logs stream here.
              </div>
            ) : (
              logLines.map((line, idx) => (
                <div key={idx} className={getLogLineColor(line.stream)}>
                  {line.text}
                </div>
              ))
            )}
            <div ref={logEndRef} />
          </div>
        </div>
      </div>

      {/* Execution Timeline history list */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="p-6 border-b border-border bg-card/50">
          <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
            Execution Timeline (Recent Runs)
          </h3>
        </div>
        <div className="overflow-x-auto">
          {timeline.length === 0 ? (
            <div className="text-center py-8 text-sm text-muted-foreground">
              No executions logged in dashboard context. Run commands on the top panel.
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/20 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  <th className="p-4">Time</th>
                  <th className="p-4">Tool</th>
                  <th className="p-4">Command</th>
                  <th className="p-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60 text-xs">
                {timeline.map((item) => (
                  <tr key={item.id} className="hover:bg-muted/10 transition">
                    <td className="p-4 text-muted-foreground">{item.timestamp}</td>
                    <td className="p-4 font-semibold text-foreground">{item.tool}</td>
                    <td className="p-4 font-mono text-muted-foreground select-all">{item.command.join(' ')}</td>
                    <td className="p-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-widest ${
                          item.status === 'completed'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : item.status === 'failed'
                            ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse'
                        }`}
                      >
                        {item.status}
                      </span>
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
