# Changelog

All notable changes to RedForge will be documented in this file.

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
