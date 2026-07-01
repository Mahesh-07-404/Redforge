export type Severity = 'info' | 'low' | 'medium' | 'high' | 'critical';
export type SessionMode = 'bugbounty' | 'ctf' | 'pentest' | 'learning' | 'coding' | 'android';
export type SessionStatus = 'active' | 'paused' | 'completed' | 'archived';
export type AutonomyLevel = 'manual' | 'semi' | 'full';

export interface ScopePolicy {
  allowed: string[];
  excluded: string[];
}

export interface Session {
  id: string;
  name: string;
  mode: SessionMode;
  target?: string;
  autonomy: AutonomyLevel;
  status: SessionStatus;
  created_at: string;
  metadata?: Record<string, any>;
  memory_namespace?: string;
}

export interface Finding {
  id: string;
  title: string;
  severity: Severity;
  description: string;
  evidence?: string;
  status?: string;
  cve?: string[];
  tool?: string;
  timestamp?: string;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  stages: Array<{
    id: string;
    name: string;
    description?: string;
    tool?: string;
  }>;
}

export interface WorkflowRun {
  workflow_id: string;
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  session_id: string;
  started_at: string;
  error?: string;
}

export interface Report {
  report_id: string;
  format: 'markdown' | 'json' | 'html' | 'pdf';
  title: string;
  content: string;
  finding_count: number;
  severity_summary: Record<Severity, number>;
}

export interface Plugin {
  plugin_id: string;
  name: string;
  version: string;
  description?: string;
  enabled: boolean;
  installed: boolean;
  author?: string;
  permissions?: string[];
}

export interface MCPTool {
  name: string;
  description: string;
  input_schema?: Record<string, any>;
}

export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mime_type?: string;
}

export interface MemoryEntry {
  id: string;
  content: string;
  session_id: string;
  timestamp: string;
  tier: 'short' | 'long';
  metadata?: Record<string, any>;
}

export interface APIResponse<T> {
  request_id: string;
  timestamp: string;
  status: 'success' | 'error';
  version: string;
  duration_ms: number;
  payload: T;
  errors: string[];
}
