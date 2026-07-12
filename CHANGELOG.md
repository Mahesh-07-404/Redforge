# Changelog

All notable changes to RedForge will be documented in this file.

## [3.1.0] - 2026-07-12

### Added
* **Single Autonomous Agent Architecture**: Refactored the entire RedForge orchestrator to merge all user-facing modes into a single autonomous agent `RedForgeAgent`. Added natural language query conversion CLI with deprecation warning.
* **Specialized Cybersecurity Skills Integration**: Uploaded, imported, and integrated a library of 817 specialized cybersecurity skills (covering red-teaming, blue-teaming, cloud-security, industrial-control-systems, zero-trust, IAM, cryptography, secure-development, forensics, malware-analysis, etc.) as the primary knowledge repository.
* **Archived Legacy Skills**: Safely archived the legacy system, safety, and execution skills under `archive/legacy_skills/`.
* **Dynamic Skill Engine**: Upgraded `SkillRegistry` and `SkillIndexer` to automatically discover, validate, cache, and hot-reload skills.
* **RAG & Semantic Retrieval**: Integrated the Skill Engine with RAG (Qdrant semantic search) and keyword relevance lookup, enabling the agent to automatically select the most appropriate skills based on intent and user query.
* **Centralized Prompt Library**: Extracted general prompt engineering patterns from analyzed system prompts, creating 15 reusable YAML prompt templates mapped across reasoning, planning, execution, recon, web, api, network, cloud, mobile, osint, reporting, memory, rag, workflow, and utilities.
* **Automated Intent-Based Prompt Retrieval**: Fully integrated prompt selection and variable rendering into the Intent Engine, Reasoning Engine, Planner, Workflow Engine, Memory manager, RAG retrievers, and Executor.

## [3.0.0] - 2026-07-01

### Added
* **Container Deployments**: Created production `docker/Dockerfile`, `docker-compose.yml`, Kubernetes deployment manifests, and Helm templates.
* **Autonomic installation Scripts**: Added scripts for installation (`install.sh`), uninstallation (`uninstall.sh`), and updating (`update.sh`).
* **Environment Profiles**: Enabled environment loading support for `development`, `testing`, `staging`, and `production`.
* **CI/CD Pipelines**: Configured workflows for code linting, unit testing, building packages, releasing tags, and scanning security parameters.
* **Performance Benchmarks Suite**: Created a performance suite measuring startup latency, memory RSS usage, tracing speed, scheduling, reporting, and RAG retrieval times.
* **Comprehensive Integration Tests**: Created end-to-end integration test validating the entire pipeline.
* **Production Documentation**: Generated installation manuals, deployment guides, security policies, developer contributions rules, API references, and plugin guides.

## [2.0.0-phase-19] - 2026-07-01

### Added
* **Observability Platform** in `src/redforge/observability/` — complete logging, tracing, auditing, and health checking telemetry package.
* **Context-Bound JSON Logger**: JSON logging engine utilizing Python `contextvars` to automatically bind trace and process contexts.
* **Prometheus metrics**: Gathers system counters, gauges, and histograms; exports scrape responses for Grafana integrations.
* **Distributed Tracing Spans**: Manages tracer spans context nesting across async call processes.
* **Cryptographic Immutable Audits**: Implements SHA-256 hash chains preventing log tampering or deletions.
* **Host Resource Profiling**: Measures processing durations, CPU percentage deltas, and process memory RSS deltas.
* **Health & Alerts**: Runs active diagnostics on CPU/memory limits, registers custom checkers, and handles warning callback notifications.
* **Grafana Dashboard Templates**: Exports Grafana import-ready JSON files for telemetry views.

## [2.0.0-phase-18] - 2026-07-01

### Added
* **Distributed Execution Engine** in `src/redforge/distributed/` — transforms RedForge from a single-process application into a distributed scheduling engine.
* **Unified Queue Wrappers**: Implemented InMemory fallback queues, Redis ZSet priority queues, and AMQP RabbitMQ queues.
* **Dependency-Aware Scheduler**: Triggers tasks only when upstream dependencies succeed. Recursively cancels child trees on parent failures.
* **Autoscaling Pools**: Spawns and stops worker nodes dynamically depending on active loads and queue lengths.
* **Task Dispatches & Leases**: Handles worker task assignments, renews, and recovers dead worker states on missed heartbeats.
* **Resilient Retry Policies**: Integrates exponential backoff strategies and Dead-Letter Queue (DLQ) task isolation.
* **Load Balancer algorithms**: Implemented Round Robin, Least Loaded, Capability-based routing, and Weighted scheduling.
* **Full Unit Test suite**: Added tests covering all load balancers, scheduling graphs, heartbeat monitors, and coordinators.

## [2.0.0-phase-17] - 2026-07-01

### Added
* **React Operator Dashboard** in `dashboard/` — clean React 19 + TypeScript + Vite + Tailwind CSS dashboard communicating exclusively with the API Gateway.
* **Overview Page**: System metrics, active sessions list, active workflow run logs, and recent vulnerabilities summaries.
* **AI Copilot Terminal**: WebSocket-based chatbot interface with word-by-word streaming token outputs, scroll management, and markdown previews.
* **Workflow Launcher**: Run multi-stage security templates and monitor active progressions (Recon, Scan, Exploit, etc.) via `/ws/workflow`.
* **Sessions Panel**: Initialize session target, scope variables, switch active context selection, and manage session deletions.
* **Direct Tool Runner**: Execute commands (Nmap, Subfinder, Nuclei) and stream live subprocess outputs in a simulated shell.
* **Report Compiler**: Generate JSON/SARIF/Markdown files, preview outputs, configure evidence scopes, and trigger local downloads.
* **Memory Note Manager**: Store notes in Short Term/Long Term RAG indexes, query logs, and clear active session memory.
* **Plugins Console**: Toggle hook settings, install custom plugins, and list extensions.
* **System Settings**: Modify backend target URLs, load JWT session tokens, authorize static API keys, and swap Light/Dark themes.
* **Vitest Suite**: Unit tests covering API service request wraps and WebSocket connection parameters.

## [2.0.0-phase-16] - 2026-07-01

### Added
* **Unified API Gateway** in `src/redforge/api/` — complete, production-grade FastAPI gateway exposing all RedForge capabilities.
* **REST APIs** for Sessions, Chat, Workflows, Planner, Reasoning, Execution, Reports, Memory, Plugins, MCP, and System.
* **WebSocket Endpoints** for real-time streaming: `/ws/chat`, `/ws/workflow`, `/ws/execution`, `/ws/events`, `/ws/reasoning`, and `/ws/report`.
* **Middlewares** for CORS, Security Headers, Request Timing, Structured Logging, Rate Limiting, Payload Size Guard, and Authentication.
* **Authentication Options** including JWT tokens, API keys, and RBAC roles (admin, operator, analyst, viewer).
* **Health & Observability Probe Endpoints** exposing `/health`, `/live`, `/ready`, `/version`, and `/metrics`.
* **Standard Response Envelope** formatting all success and error responses.
* **Robust Test Suite** verifying REST endpoints, WebSockets, streaming, middlewares, validation, health checks, rate limiting, and exception handlers.

### Fixed
* Fixed double accept ASGI error on the `/ws/events` subscription flow.
* Fixed forward reference unresolved dependencies for `ReadAuth` and `AdminAuth` types in OpenAPI generation.

## [2.0.0-phase-15] - 2026-06-29

### Added
* **Plugin SDK** in `src/redforge/plugins/` — pluggable architecture for Tool, Workflow, Agent, Report, Memory Provider, RAG Provider, and Authentication Provider plugin types.
* **PluginManager** coordinating full plugin lifecycle (install, uninstall, enable, disable, version, dependency resolution).
* **PluginLoader** with dependency graph resolution — fails fast on missing transitive dependencies.
* **PluginRegistry** tracking installed plugins and their enabled/disabled states.
* **PluginHooks** with six lifecycle hook points (`before_plan`, `after_plan`, `before_execution`, `after_execution`, `before_report`, `after_report`).
* **PluginSandbox** preventing plugins from directly modifying core architecture.
* **PluginPermissionManager** validating requested plugin permissions against user-granted scopes.
* **PluginEvents** emitting install, uninstall, enable, disable lifecycle notifications.
* **MCP (Model Context Protocol) Framework** in `src/redforge/mcp/` — JSON-RPC compliant tool and resource discovery.
* **MCPServer** exposing tool and resource registries to connected agents.
* **MCPClient** querying server endpoints for available tools and resources.
* **MCPRegistry** cataloging discoverable tools and local resource URIs.
* **MCPTransport** formatting JSON-RPC 2.0 compliant payloads.
* **MCPManager** coordinating server/client lifecycles.
* Backward-compatible re-export of legacy `PlatformManager`, `HackerOneAPI`, `BugcrowdAPI`, `Submission`, `Report`, `Program`, and `create_submission` from `redforge.plugins`.
* Plugin Developer Guide in `docs/plugin_developer_guide.md`.
* MCP Integration Guide in `docs/mcp_integration_guide.md`.
* Unit tests in `tests/unit/test_plugins_mcp.py` verifying plugin installation, dependency resolution, sandbox execution, permission checks, hook triggers, MCP tool/resource discovery, and transport message formatting.

## [2.0.0-phase-14] - 2026-06-29

### Added
* Modular **Workflow Engine** in `src/redforge/workflow/` orchestrating configurable target tasks.
* Created **BuiltInWorkflows** defining 8 standard workflows (Passive Recon, Active Recon, Web Pentest, Bug Bounty, CTF, Learning, Report Generation, and Research).
* **WorkflowLoader** supporting custom and built-in workflow registrations.
* **WorkflowValidator** and **ConditionValidator** assessing stage configurations and target conditions.
* **WorkflowScheduler** sorting execution sequences according to stage dependencies.
* **WorkflowStateMachine** tracking CREATED, READY, WAITING_APPROVAL, RUNNING, PAUSED, FAILED, COMPLETED, and CANCELLED states.
* **WorkflowEvents** mapping event hooks (started, failed, completed).
* **StageExecutor** executing individual stages.
* Unit tests in `tests/unit/test_workflow.py` verifying loaders, validations, scheduling sequences, state machines, and fail/pass outcomes.

## [2.0.0-phase-13] - 2026-06-29

### Added
* Modular **Knowledge Synthesis & Reporting Engine** in `src/redforge/reporting/` transforming raw evidence, entities, memory, and RAG outputs into security reports.
* **KnowledgeSynthesizer** to compile evidence, host details, and CVE entries into structured Findings.
* **RiskEngine** calculating business risks, technical risks, exploitability rates, impact parameters, and overall risk levels.
* **Severity** classifications mapping findings into Critical, High, Medium, Low, and Info levels.
* **CorrelationEngine** and **Deduplicator** grouping vulnerability assets and removing duplicate entries.
* **ReportRenderer** and **ReportExporter** generating reports in Markdown, JSON, and standard SARIF formats.
* Chronological **ReportTimelineGenerator** mapping milestone execution steps.
* Pluggable **RemediationEngine** providing risk explanations, remediations, fixes, and verification procedures.
* Unit tests in `tests/unit/test_reporting.py` verifying synthesizers, risk scoring, correlations, deduplications, timelines, rendering layouts, and exporters.

## [2.0.0-phase-12] - 2026-06-29

### Added
* Modular **Autonomous Reasoning Engine** in `src/redforge/reasoning/` responsible for thinking, evaluating progress, and self-reflecting on plan goals.
* **GoalManager** to model, track, and update goal completion states.
* **TaskDecomposer** breaking high-level target goals down into individual Task steps.
* Pluggable **StrategySelector** mapping objectives to core workflows (Passive, Active, Bug Bounty, CTF, Learning, Research, Android, Network, Cloud, API).
* **WorldState** tracking live host, port, service, CVE, url, and credentials metadata.
* **SelfReflection** and **Replanner** to dynamically update planning lists based on execution outcomes.
* **SelfEvaluator** assessing confidence levels, coverage percentages, and task completions.
* **FailureHandler** managing tool crash retries and fallback switches.
* **ReasoningStateMachine** managing states (IDLE, PLANNING, EXECUTING, REASONING, Reflecting, etc.).
* Unit tests in `tests/unit/test_reasoning.py` verifying goal decomposition, strategy mappings, world state updates, self evaluation, reflection replanning, failure handlers, and state machine transitions.

## [2.0.0-phase-11] - 2026-06-29

### Added
* Modular **Multi-Agent Orchestrator** in `src/redforge/orchestrator/` coordinates specialized agent tasks.
* Pluggable **BaseAgent** interface under `src/redforge/agents/` modeling agent id, tools, capability requirements, and execution.
* Implemented **10 specialized agents** (Recon, Web, Network, Android, CTF, Learning, Report, Research, BugBounty, and Coordinator).
* **AgentRegistry** automatically registering agents and finding them based on required capability metrics.
* **AgentCoordinator** selecting and mapping plan tasks to compatible agents.
* **AgentScheduler** running assignments sequentially and collecting outputs.
* **CommunicationBus** routing messages (TaskAssigned, NeedInformation, ShareEvidence) between agents.
* **ResultMerger** aggregating and deduplicating distinct agent outcomes.
* **AgentRetryStrategy** providing retry loops for task operations.
* Unit tests in `tests/unit/test_orchestrator.py` verifying coordinators, schedulers, registries, communication, retries, and result merges.

## [2.0.0-phase-10] - 2026-06-29

### Added
* Modular **Hybrid RAG & Knowledge Engine** in `src/redforge/rag/` providing context injection between memory storage and LLMs.
* Pluggable **EmbeddingProvider** adapters for OpenAI, Gemini, Ollama, Sentence Transformers, and FastEmbed.
* **VectorStore** adapters supporting SQLite, Qdrant, FAISS, Chroma, Pinecone, and Weaviate, featuring memory fallbacks.
* Pluggable **SourceProvider** interface to ingest Session Memory, Entity Memory, Timeline, Evidence Store, and Skills.
* **ChunkEngine** providing sliding-word chunking algorithms for text/markdown inputs and session logs.
* **HybridSearch** combining keyword searches and vector queries.
* **Reranker** sorting results by query overlaps, active session matches, and recency multipliers.
* **ContextBuilder** compiling compressed deduplicated results into token-bounded context blocks.
* **KnowledgeBase** organizing libraries for CVEs, OWASP, Pentest notes, and local files.
* **RAGCache** providing TTL key-value caching for search runs.
* Unit tests in `tests/unit/test_rag.py` verifying chunking, hybrid search, embedding adapters, vector stores, knowledge bases, reranking, caching, and pipeline runs.

## [2.0.0-phase-8] - 2026-06-29

### Added
* Modular **Result Normalization** layer in `src/redforge/normalize/` translating raw tool logs to standard entities.
* **NormalizedEntity** base schema representing universal metadata (IDs, values, tools, session & execution links, and hash references).
* Universal entity classes (Host, IPAddress, Port, Service, URLResource, Technology, Directory, Finding, CVE, etc.).
* Built-in mappers for **14 tools** (Subfinder, Assetfinder, Amass, Httpx, Katana, Nmap, Naabu, Nuclei, DNSX, FFUF, Feroxbuster, Gobuster, Waybackurls, GAU) to map log formats to normalized models.
* **MapperRegistry** automatically registering tool-specific normalization maps.
* **RelationshipResolver** extracting relations (Host->Port, Port->Service, Finding->CVE, etc.) without graph databases.
* **NormalizationValidator** verifying duplicates, structural validity, and broken references.
* Unit tests in `tests/unit/test_normalize.py` verifying registry lookups, entity matching, relationship resolver, and pipeline validation.

## [2.0.0-phase-7] - 2026-06-29

### Added
* Modular **Evidence & Artifact Management** layer in `src/redforge/evidence/` converting execution logs to unified auditable evidence.
* **EvidenceCollector** organizing execution parameters, timing details, exit statuses, and artifacts.
* **ArtifactManager** building individual artifacts, generating associated metadata tags, and resolving tool risk.
* **TimelineGenerator** compiling a chronological event trail of the planning, validation, and execution processes.
* **EvidenceStore** persisting session evidence directories containing `evidence.json`, `timeline.json`, and distinct JSON files for each tool artifact.
* **EvidenceSerializer** translating data into JSON, Markdown, and plain text representations.
* **hashing** library implementing SHA256 validation for outputs.
* Unit tests in `tests/unit/test_evidence.py` verifying collector, timeline, hash checks, serialization, and storage operations.

## [2.0.0-phase-6] - 2026-06-29

### Added
* Modular **Execution Engine** in `src/redforge/executor/` executing approved security plan workflows.
* **TaskScheduler** resolving sequential topological sorted execution order, processing task dependencies, handling timeouts, retries, and cancellation requests.
* **Runner** executing individual tasks by spawning processes, tracking durations, and capturing exit codes.
* **ProcessManager** providing cross-platform process lifecycle controls (spawn, wait, terminate, kill, timeout) for Linux, macOS, Windows, and WSL.
* **StreamManager** emitting callback-driven execution events (ExecutionStarted, TaskStarted, OutputReceived, ExecutionFinished, TaskFailed).
* **OutputParser** parsing outputs of `nmap`, `subfinder`, and `httpx` into structured JSON while retaining original raw outputs.
* Execution contracts (`ApprovedPlan`, `TaskResult`, `ExecutionResult`, `ExecutionStatus`, `ExecutionEvent`).
* Unit tests in `tests/unit/test_executor.py` verifying process spawning, scheduling dependencies, cancellation, timeouts, streaming events, output parsing, and tool errors.

## [2.0.0-phase-5] - 2026-06-29

### Added
* New **Policy & Approval Engine** layer in `src/redforge/policy/` sitting between Planner and Executor.
* **PolicyDecision** model indicating ALLOW / REQUIRES_APPROVAL / DENY and risk rating.
* **ScopeValidator** checking target constraints against localhost, loopbacks, and structure.
* **RiskEngine** evaluating overall plan risk levels (LOW/MEDIUM/HIGH/CRITICAL) based on requested tools.
* **PermissionValidator** returning warning advisories for invasive scanner authorizations.
* **ApprovalEngine** routing LOW risk scans to auto-approval and higher risks to confirmation/approval gates.
* **PolicyEngine** main orchestrator assessing plan tools and targets.
* Integration inside `Pipeline.process_turn` appending formatted policy decisions and risk ratings to the execution plan response.
* Unit tests in `tests/unit/test_policy.py` verifying scopes, risk rankings, approvals, denials, and bypass integrations.

## [2.0.0-phase-4] - 2026-06-29

### Added
* Modular **Tool Registry** in `src/redforge/tools/` responsible for discovering, describing, validating, and resolving security tools without executing them.
* Pydantic **Tool** model in `src/redforge/tools/tool.py` containing ID, name, binary name, platform lists, categories, capabilities, and required permissions. Supports backward compatibility with old tools attributes.
* **Capabilities** ranking mapping for subdomain discovery, port scanning, HTTP enumeration, directory brute force, technology detection, web crawling, fuzzing, screenshot, and DNS.
* **PlatformDetector** supporting platform detection for Kali, Arch, Ubuntu, Debian, Fedora, macOS, Windows, and WSL.
* **ToolDiscovery** class implementing PATH checks without running tool processes.
* **ToolValidator** checking binary presence and platform compatibility.
* **ToolInstaller** generating dry-run install command mappings.
* Unit tests in `tests/unit/test_tools_v2.py` verifying registry caching, lookups, ranking, discovery, platform detection, validator, installer, and resolver.

## [2.0.0-phase-3] - 2026-06-29

### Added
* Modular dry-run **Planner Engine** in `src/redforge/planner/` that creates execution plans but never executes tools.
* **PlanningStrategy** classes implementing `PassiveReconStrategy`, `WebEnumerationStrategy`, `BugBountyStrategy`, `CTFStrategy`, `LearningStrategy`, and `ReportStrategy`.
* **TaskGraph** dependency engine resolving task order using topological sort and performing cycle detection.
* **PlannerValidator** verifying session, target, and intent compatibility.
* Integration within `Pipeline.process_turn` to output formatted planning lists for planning intents.
* Comprehensive unit tests in `tests/unit/test_planner.py` covering graph ordering, strategy selection, validation, and bypass paths.

## [2.0.0-phase-2] - 2026-06-29

### Added
* Modular strategy-based **Intent Engine** in `src/redforge/core/intent.py` supporting `GENERAL_CHAT`, `BUG_BOUNTY`, `PENTEST`, `CTF`, `LEARNING`, `REPORT`, `SESSION`, `HELP`, `TOOL`, `CONFIG`, and legacy intents.
* **Conversation Manager** in `src/redforge/core/conversation.py` to maintain casual conversation context, separate security workflows, support streaming, and output event callbacks.
* **Intent Router** in `src/redforge/core/router.py` to route parsed intents to their correct subsystem without enclosing business logic.
* **Conversation Context** model in `src/redforge/contracts/conversation.py`.
* Comprehensive unit tests in `tests/unit/test_conversation_v2.py` verifying classification, routing, and session-integration.
* New `ARCHITECTURE.md` file.

### Changed
* Refactored `Pipeline.process_turn` to load `ConversationContext`, route casual queries directly to the Conversation Manager, and automatically save context updates to the active session.
* Removed hard-coded "Target missing" warnings for general conversation.

## [2.0.0-phase-1] - 2026-06-29

### Added
* SessionConfig, replacing WorkspaceConfig in config.
* SQLite migration script adding status, metadata, and memory_namespace columns.
* Data contracts for `Target`, `ScopePolicy`, `TargetType`, `SessionMode`, and `SessionStatus`.
* Unit tests in `test_session_v2.py`.
