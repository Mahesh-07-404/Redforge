# Changelog

All notable changes to RedForge will be documented in this file.

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
