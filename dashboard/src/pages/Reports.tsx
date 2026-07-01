import React, { useState, useEffect } from 'react';
import { useSession } from '../contexts/SessionContext';
import { useSettings } from '../contexts/SettingsContext';
import { RedForgeAPI } from '../services/api';
import { FileText, Download, Play, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

export const Reports: React.FC = () => {
  const { activeSession } = useSession();
  const { settings } = useSettings();
  
  const [reportFormat, setReportFormat] = useState<'markdown' | 'json' | 'html' | 'pdf'>('markdown');
  const [includeEvidence, setIncludeEvidence] = useState(true);
  const [includeRemediation, setIncludeRemediation] = useState(true);
  
  const [generating, setGenerating] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [markdownContent, setMarkdownContent] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Load existing report on active session change
  useEffect(() => {
    if (!activeSession) {
      setReport(null);
      setMarkdownContent('');
      return;
    }
    
    const loadExisting = async () => {
      setError(null);
      try {
        // Fetch raw markdown report if available
        const raw = await RedForgeAPI.getRawMarkdownReport(
          settings.apiUrl,
          activeSession.id,
          settings.apiKey,
          settings.authToken
        );
        if (raw) {
          setMarkdownContent(raw);
          setReport({
            title: `RedForge Report — ${activeSession.name}`,
            format: 'markdown',
            finding_count: (raw.match(/## Finding/g) || []).length,
          });
        }
      } catch {
        // No existing report generated yet
        setReport(null);
        setMarkdownContent('');
      }
    };
    loadExisting();
  }, [activeSession, settings.apiUrl, settings.apiKey, settings.authToken]);

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSession) return;

    setGenerating(true);
    setError(null);
    try {
      const result = await RedForgeAPI.generateReport(
        settings.apiUrl,
        {
          session_id: activeSession.id,
          format: reportFormat,
          include_evidence: includeEvidence,
          include_remediation: includeRemediation,
        },
        settings.apiKey,
        settings.authToken
      );
      
      setReport(result);
      
      // If we selected markdown, load the preview text
      if (reportFormat === 'markdown' && result.content) {
        setMarkdownContent(result.content);
      } else if (result.content && typeof result.content === 'string') {
        setMarkdownContent(result.content);
      } else {
        setMarkdownContent(JSON.stringify(result, null, 2));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleDownload = () => {
    if (!report || !markdownContent) return;
    const formatExtension = reportFormat === 'json' ? 'json' : reportFormat === 'html' ? 'html' : 'md';
    const mime = reportFormat === 'json' ? 'application/json' : reportFormat === 'html' ? 'text/html' : 'text/markdown';
    downloadFile(markdownContent, `RedForge_Report_${activeSession?.id}.${formatExtension}`, mime);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground m-0">Report Center</h2>
          <p className="text-sm text-muted-foreground">Export findings, evidence logs, and mitigations as audits</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded border border-rose-800/40 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        {/* Form controls */}
        <div className="md:col-span-1 rounded-lg border border-border bg-card overflow-hidden">
          <div className="p-6 border-b border-border bg-card/50">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <FileText className="h-4 w-4 text-primary" /> Compilation parameters
            </h3>
          </div>
          <div className="p-6">
            {!activeSession ? (
              <div className="text-center py-4 text-xs text-muted-foreground">
                Select an active target session to configure report generation.
              </div>
            ) : (
              <form onSubmit={handleGenerateReport} className="space-y-4">
                {/* Format selection */}
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground uppercase font-semibold">Report Format</label>
                  <select
                    value={reportFormat}
                    onChange={(e) => setReportFormat(e.target.value as any)}
                    className="w-full px-3 py-2 rounded border border-border bg-muted/30 focus:outline-none focus:border-primary text-xs text-foreground"
                  >
                    <option value="markdown" className="bg-card">Markdown Summary</option>
                    <option value="json" className="bg-card">JSON Format</option>
                    <option value="html" className="bg-card">HTML Operations View</option>
                    <option value="pdf" className="bg-card">PDF Layout</option>
                  </select>
                </div>

                {/* include evidence */}
                <div className="flex items-center gap-2 py-1">
                  <input
                    type="checkbox"
                    id="include_evidence"
                    checked={includeEvidence}
                    onChange={(e) => setIncludeEvidence(e.target.checked)}
                    className="rounded border-border bg-muted/30 text-primary focus:ring-primary h-4 w-4"
                  />
                  <label htmlFor="include_evidence" className="text-xs text-foreground cursor-pointer select-none">
                    Include raw tool evidence logs
                  </label>
                </div>

                {/* include remediation */}
                <div className="flex items-center gap-2 py-1">
                  <input
                    type="checkbox"
                    id="include_remediation"
                    checked={includeRemediation}
                    onChange={(e) => setIncludeRemediation(e.target.checked)}
                    className="rounded border-border bg-muted/30 text-primary focus:ring-primary h-4 w-4"
                  />
                  <label htmlFor="include_remediation" className="text-xs text-foreground cursor-pointer select-none">
                    Include remediation fixes
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={generating}
                  className="w-full py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold text-xs rounded shadow-[0_0_15px_rgba(170,59,255,0.25)] flex items-center justify-center gap-2 transition disabled:opacity-50"
                >
                  {generating ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" /> Compiling Audit...
                    </>
                  ) : (
                    <>
                      <Play className="h-3.5 w-3.5" /> Compile Report
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Preview pane */}
        <div className="md:col-span-2 rounded-lg border border-border bg-card overflow-hidden flex flex-col h-[550px]">
          <div className="p-6 border-b border-border bg-card/50 flex items-center justify-between">
            <h3 className="font-bold text-xs uppercase tracking-widest text-foreground flex items-center gap-2 m-0">
              <FileText className="h-4 w-4 text-primary" /> Report Preview & Export
            </h3>
            {report && (
              <button
                onClick={handleDownload}
                className="px-3 py-1 bg-muted border border-border rounded text-[10px] uppercase font-bold hover:bg-muted/80 text-foreground flex items-center gap-1.5 transition"
              >
                <Download className="h-3.5 w-3.5" /> Download
              </button>
            )}
          </div>
          <div className="p-6 flex-1 overflow-auto bg-muted/10">
            {!report ? (
              <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                No report loaded. Press "Compile Report" on the left card to compile current findings.
              </div>
            ) : (
              <pre className="text-xs font-mono text-foreground whitespace-pre-wrap leading-normal font-light">
                {markdownContent}
              </pre>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
