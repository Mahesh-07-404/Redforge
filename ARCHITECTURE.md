# RedForge Architecture

This document describes the architectural layout of RedForge.

## Architectural Layers

### 1. Contracts Layer (`src/redforge/contracts/`)
Data contracts representing the standard model primitives across RedForge.
* **`session.py`**: Defines the `Session` model, target specifications (`Target`, `TargetType`, `ScopePolicy`), and state enums.
* **`intent.py`**: Defines `ParsedIntent`, `IntentType`, and `RiskLevel`.
* **`conversation.py`**: Defines `ConversationContext` which serves as the central context tracking active session, active target, current goal, current intent, previous messages, and summary.

### 2. Core Orchestration (`src/redforge/core/`)
Implements the core logic and workflow execution.
* **`intent.py`**: The Modular Intent Engine. Employs `IntentClassificationStrategy` implementations to categorize user inputs into specific system intents.
* **`conversation.py`**: The Conversation Manager. Generates conversational responses using LLM streaming or fast-path greetings, utilizing the conversational history.
* **`router.py`**: The Intent Router. Responsible for directing intents to their designated subsystems (e.g., routing `GENERAL_CHAT` to the Conversation Manager, `SESSION` to the Session Service) without housing business logic.
* **`pipeline.py`**: Orchestrates turn execution, loads context, updates session metadata, and saves the session state automatically.

### 3. Memory & Persistence Layer
* **`src/redforge/memory/`**: RAG context retrieval and session-isolated vector database management.
* **`src/redforge/core/session.py`**: SQLite session persistence with auto-migration columns for metadata and namespace.

### 4. Planner Layer (`src/redforge/planner/`)
Encapsulates the Planner and Task Graph engine responsible for generating dry-run plans without executing tools.
* **`planner_context.py`**: Definess `PlannerContext` containing active session, target, goal, intent, active mode, and user preferences.
* **`task.py`**: Data structure representing an individual unit of work (`Task`) detailing id, description, dependencies, estimated duration, risk level, status, and required confirmations.
* **`task_graph.py`**: Implements topological sorting to resolve task execution order and perform cycle detection.
* **`plan.py`**: Holds the compiled `Plan` consisting of the target goal, ordered tasks, dependencies, confidence score, and warnings.
* **`strategy.py`**: Implement modular planning strategies (`PassiveReconStrategy`, `WebEnumerationStrategy`, `BugBountyStrategy`, `CTFStrategy`, `LearningStrategy`, `ReportStrategy`) mapping specific user requests to workflows.
* **`validators.py`**: Verifies prerequisites like session existence, target constraints, and intent validity prior to planning.

### 5. Tool Registry Layer (`src/redforge/tools/`)
Implements security tool metadata definition, capability discovery, platform detection, and dry-run installation mapping.
* **`tool.py`**: Pydantic `Tool` model containing ID, name, binary name, platforms, session mode compatibility, categories, description, capability links, required permissions, install methods, documentation, health, and availability. Features backward compatibility properties matching legacy tools format.
* **`registry.py`**: Central registry providing tool registration, lookup by capability (with ranking), lookup by name/ID, and metadata caching. Exposes classmethods to support old tool suite test flows.
* **`resolver.py`**: Resolves execution plan capabilities dynamically against registered tools.
* **`capabilities.py`**: Declares security capability enums (Subdomain Enumeration, Port Scanning, Directory Brute Force, Web Crawling, Fuzzing, etc.).
* **`platform.py`**: Performs detection for platforms (Arch, Kali, Ubuntu, Debian, Fedora, macOS, Windows, WSL) and exposes package managers, install command templates, and default bin search paths.
* **`discovery.py`**: Conducts path check resolution for tools without executing executable files.
* **`validator.py`**: Validates binary path existence and platform compatibility for specified tools.
* **`installer.py`**: Outputs installation dry-run blueprints detailing packages and shell installation strings.
* **`exceptions.py`**: Defines custom domain exceptions like `ToolNotFoundError` and `UnsupportedPlatformError`.

### 6. Policy & Approval Layer (`src/redforge/policy/`)
Sits between the Planner and Execution steps to validate scopes and calculate risk ratings before any execution.
* **`policy_decision.py`**: Declares `PolicyDecision` data model containing status enum (ALLOW/DENY/REQUIRES_APPROVAL), risk level enum (LOW/MEDIUM/HIGH/CRITICAL), reason text, warnings list, and permission listings.
* **`policy_rules.py`**: Dictates rules such as prohibited target lists (e.g. localhost, loopbacks) and tool risk mapping associations.
* **`scope_validator.py`**: Checks if the active target is formatted correctly and doesn't violate loopback constraints.
* **`risk_engine.py`**: Rates active plan risk according to the most invasive requested tool.
* **`permission_validator.py`**: Lists warning advisories for tools that require explicit admin/testing authorization (like sqlmap).
* **`approval_engine.py`**: Applies risk-level policy gates to yield auto-approvals, confirmation triggers, or deny actions.
* **`policy_engine.py`**: Main orchestrator evaluating the `Plan` target and tools to compute the `PolicyDecision`.

### 7. Execution Engine (`src/redforge/executor/`)
Executes task workflows dynamically for approved plan structures.
* **`executor.py`**: Principal coordinator receiving the `ApprovedPlan` structure and triggering task scheduler execution before yielding `ExecutionResult`. Emits lifecycle start/finish execution events.
* **`scheduler.py`**: Directs sequential task runs, handles task dependency tracking, and performs timeouts, retries, and cancellation gates.
* **`runner.py`**: Orchestrates individual task runs by invoking cross-platform subprocess spawning and output parser structures.
* **`process.py`**: Spawns, monitors, terminates, and kills subprocess actions across Linux, macOS, Windows, and WSL.
* **`stream.py`**: Callback-based stream subscriber manager emitting event structures.
* **`parser.py`**: Parses tool stdout (e.g. subfinder, nmap, httpx) into structured formats while retaining raw stdout.
* **`events.py`**: Declares standard data event formats (ExecutionStarted, TaskStarted, OutputReceived, ExecutionFinished, TaskFailed).
* **`state.py`**: Enumerates execution states (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED, TIMED_OUT, SKIPPED).
* **`exceptions.py`**: Defines execution error classes.
* **`contracts.py`**: Encapsulates `ApprovedPlan`, `TaskResult`, and `ExecutionResult` schemas.

### 8. Evidence & Artifact Management Layer (`src/redforge/evidence/`)
Converts task execution outputs into structured evidence, creating a timeline audit trail and storing output artifacts under sessions.
* **`contracts.py`**: Declares Pydantic data schemas representing `Evidence`, `Artifact`, `EvidenceBundle`, `TimelineEvent`, and `ExecutionTimeline`.
* **`metadata.py`**: Defines `ArtifactMetadata` schema containing target, duration, exit code, hash, platform, and tool details.
* **`collector.py`**: Main orchestrator converting `ExecutionResult` inputs into a unified `EvidenceBundle`.
* **`artifacts.py`**: Manages artifact assembly and metadata binding.
* **`timeline.py`**: Compiles chronological execution timeline events.
* **`hashing.py`**: Computes SHA256 integrity hashes for all evidence artifact strings and bytes.
* **`store.py`**: Persists session evidence structures (`evidence.json`, `timeline.json`, and individual artifact JSON files under `data/evidence/{session_id}/`).
* **`serializer.py`**: Serializes evidence bundles to JSON, Markdown, and plain text formats.
* **`exceptions.py`**: Defines evidence-related exceptions like `StoreError`.

### 9. Result Normalization Layer (`src/redforge/normalize/`)
This layer translates raw tool logs and evidence bundles into a universal schema of normalized entities, preparing it for downstream ingestion by Memory, RAG, and Reports.

* **`schema.py`**: Declares base `NormalizedEntity` and `EvidenceReference` properties.
* **`entities.py`**: Defines individual normalized entities (HostEntity, IPAddressEntity, PortEntity, ServiceEntity, URLResource, TechnologyEntity, DirectoryEntity, FindingEntity, CVEEntity, etc.).
* **`mapper.py`**: Contains tool mappers (Subfinder, Amass, Httpx, Nmap, FFUF, Nuclei, DNSX, etc.) translating tool outcomes into entity schemas.
* **`registry.py`**: Automatic registration registry for tool mappers.
* **`resolver.py`**: Resolves relationships between entities (Host->Port, Port->Service, Host->Finding, etc.).
* **`validator.py`**: Validates entities for duplicates, missing fields, or broken references.
* **`normalizer.py`**: Central orchestrator processing `EvidenceBundle` files to compile `NormalizationResult` outputs.
* **`contracts.py`**: Defines normalized output schemas (`NormalizedBundle`, `EntityRelation`, `NormalizationResult`).
* **`exceptions.py`**: Custom normalization exceptions.

#### Normalization Architecture Details
* **Why Normalization Exists**: Instead of letting memory, RAG, or reporting layers parse dozens of raw tool-specific text outputs (e.g. nmap vs. subfinder), the Normalizer converts them into a single, uniform model. This decouples intelligence layers from execution tools.
* **Universal Entity Schema**: Every entity contains:
  * `id`: Unique identifier (e.g., `host_example.com`).
  * `entity_type`: Entity class name (e.g., `Host`, `Port`, `Finding`).
  * `value`: Principal value (e.g., domain string or port number).
  * `source_tool`: Binary that discovered it.
  * `session_id` & `execution_id`: Context links.
  * `evidence_reference`: Original task ID and artifact hash to guarantee auditability.
* **Tool Mapper Architecture**: Extensible mappers register themselves in the registry, consuming raw or parsed artifact logs and yielding a flat list of entity objects.
* **Entity Relationship Model**: Mappers and resolvers automatically map links between entities (e.g. connecting a host to its scanned port, a port to its service, or a finding to its CVE reference) without relying on a full graph database.
* **Future Memory Integration**: The next phase (Memory Engine, Phase 9) will ingest the structured `NormalizedBundle` to populate the vector and relational state stores, updating context memory and establishing cross-session search capability.

### 10. Hybrid RAG & Knowledge Engine (`src/redforge/rag/`)
Implements the Retrieval-Augmented Generation layer mediating between LLMs and structured/unstructured memory sources.

```mermaid
graph TD
    UserQuery["User Query"] --> HybridSearch["Hybrid Search Engine"]
    HybridSearch --> KeywordSearch["Keyword / Metadata Search"]
    HybridSearch --> VectorSearch["Vector DB Search"]
    
    SourceManager["RAG Manager"] --> MemoryProvider["Memory Provider"]
    SourceManager --> SkillProvider["Skill Provider"]
    SourceManager --> DocProvider["Documentation Provider"]
    
    MemoryProvider --> Chunker["Chunk Engine"]
    SkillProvider --> Chunker
    DocProvider --> Chunker
    
    Chunker --> Ingestion["Ingestion Pipeline"]
    Ingestion --> VectorStore["Vector Store Adapter"]
    
    KeywordSearch --> Merge["Merge & Deduplicate"]
    VectorSearch --> Merge
    
    Merge --> Reranker["Relevance Reranker"]
    Reranker --> ContextBuilder["Context Builder & Token Compressor"]
    ContextBuilder --> LLMContext["Optimized LLM Prompt Context"]
```

#### Module Descriptions
* **`engine.py`** (`RAGEngine`): Main entry point orchestrating cache lookups, search coordination, reranking, and context serialization.
* **`manager.py`** (`RAGManager`): Discovers and triggers provider fetching routines, running chunks ingestion.
* **`retriever.py`** (`Retriever`): Accesses the RAGEngine using simplified single-method lookups.
* **`hybrid_search.py`** (`HybridSearch`): Executes side-by-side keyword matching and vector matching.
* **`query.py`**: Model schema for queries.
* **`chunker.py`** (`ChunkEngine`): Implements word-sliding chunking for text/markdown files and logs, generating standard chunk hashes.
* **`embedder.py`** (`EmbeddingProvider`): Pluggable adapters supporting Mock, OpenAI, Gemini, Ollama, Sentence Transformers, and FastEmbed.
* **`reranker.py`** (`Reranker`): Scores hits based on query-word overlap, recency weightings, and active session matching.
* **`vector_store.py`** (`VectorStore`): Abstract vector adapters supporting memory, SQLite, Qdrant, FAISS, Chroma, Pinecone, and Weaviate.
* **`knowledge_base.py`** (`KnowledgeBase`): Organizes static knowledge libraries (CVEs, OWASP guides, Pentesting references).
* **`context_builder.py`** (`ContextBuilder`): Compresses results, deduplicates content blocks, references sources, and formats final context boundaries respecting token limits.
* **`sources.py`** (`SourceProvider`): Pluggable abstract providers pulling from Memory Engine, Session Memory, Entity Memory, Evidence Store, and Skills.
* **`pipeline.py`** (`RAGPipeline`): Runs RAGEngine queries in pipeline steps.
* **`cache.py`** (`RAGCache`): Key-value TTL caching mechanism for retrieval outputs and queries.
* **`exceptions.py`**: Custom RAG exceptions.

### 11. Multi-Agent Orchestrator (`src/redforge/orchestrator/` & `src/redforge/agents/`)
Orchestrates multiple specialized cybersecurity agents, mapping execution plans to agents, scheduling their runs, managing message bus communication, and merging task outcomes.

```mermaid
graph TD
    OrchestratorEngine["Orchestrator Engine"] --> AgentCoordinator["Agent Coordinator"]
    OrchestratorEngine --> AgentScheduler["Agent Scheduler"]
    
    AgentCoordinator --> AgentRegistry["Agent Registry"]
    AgentRegistry --> LoadAgents["Recon, Web, Network, Android, CTF, Learning, Report, Research, BugBounty, Coordinator Agents"]
    
    AgentScheduler --> AgentDispatcher["Agent Dispatcher"]
    AgentDispatcher --> Exec["Agent base.execute(plan)"]
    
    Exec --> CommBus["Communication Bus (internal message bus)"]
    CommBus --> PubSub["Publish TaskAssigned, TaskStarted, TaskCompleted, NeedInformation, ShareEvidence"]
    
    AgentScheduler --> ResultMerger["Result Merger (Deduplicate & Merge)"]
```

#### Module Descriptions
* **`engine.py`** (`OrchestratorEngine`): Main entry point mapping plan files to tasks, invoking coordinators, scheduling tasks, and merging results.
* **`coordinator.py`** (`AgentCoordinator`): Selects the best agent for each plan task based on tool and capability support.
* **`scheduler.py`** (`AgentScheduler`): Coordinates execution order, retries, and task runs.
* **`dispatcher.py`** (`AgentDispatcher`): Directs plans to base execution routines.
* **`agent_registry.py`** (`AgentRegistry`): Stores available agents, supporting capability-based lookup.
* **`agent_loader.py`** (`AgentLoader`): Loads all 10 core agents (Recon, Web, Network, Android, CTF, Learning, Report, Research, BugBounty, Coordinator) into the registry.
* **`communication.py`** (`CommunicationBus`): Internal message bus routing task assignment, completion, evidence sharing, and informational requests.
* **`result_merger.py`** (`ResultMerger`): Cleanly merges distinct agent outputs, removing duplicates and formatting audit logs.
* **`retry.py`** (`AgentRetryStrategy`): Simple retry loop for failed task operations.
* **`context.py`** (`OrchestratorContext`): Stores shared memory values accessible across agents.
* **`contracts.py`**: Declares Pydantic data schemas representing `AgentAssignment`, `AgentTaskResult`, and `OrchestrationResult`.
* **`exceptions.py`**: Custom orchestrator exceptions.

### 12. Autonomous Reasoning Engine (`src/redforge/reasoning/`)
Implements the autonomous thinking layer, managing goals, decomposing plans, analyzing outcomes, updating states, handling tool failures, and replanning dynamically.

```mermaid
graph TD
    GoalManager["Goal Manager"] --> ReasoningEngine["Reasoning Engine"]
    ReasoningEngine --> StrategySelector["Strategy Selector"]
    ReasoningEngine --> TaskDecomposer["Task Decomposer"]
    
    ReasoningEngine --> Reasoner["Reasoner"]
    Reasoner --> SelfEvaluator["Self Evaluator"]
    SelfEvaluator --> WorldState["World State (live model)"]
    
    ReasoningEngine --> SelfReflection["Self Reflection"]
    SelfReflection --> Replanner["Replanner"]
    Replanner --> FailureHandler["Failure Handler"]
    
    ReasoningEngine --> StateMachine["State Machine (planning,executing,reflecting...)"]
```

#### Module Descriptions
* **`engine.py`** (`ReasoningEngine`): Principal coordinator processing goals, running decomposers, and managing state transitions.
* **`goal_manager.py`** (`GoalManager`): Tracks active goals and goal completion states.
* **`task_decomposer.py`** (`TaskDecomposer`): Breaks user goals down into fine-grained tasks.
* **`reasoner.py`** (`Reasoner`): Formulates strategic reasoning decisions (execute, replan, stop).
* **`strategy_selector.py`** (`StrategySelector`): Maps targets and goals to pluggable workflows (Passive Recon, Active Recon, Bug Bounty, CTF, Learning, Research, Android, Network, Cloud, API).
* **`reflection.py`** (`SelfReflection`): Reviews completed task outcomes and decides whether to trigger path modifications.
* **`self_evaluator.py`** (`SelfEvaluator`): Estimates task coverage, confidence scores, and overall goal completion.
* **`replanner.py`** (`Replanner`): Alters execution steps dynamically if the world state changes.
* **`failure_handler.py`** (`FailureHandler`): Decides whether to retry a task, switch tool hints, or fail when tools crash.
* **`world_state.py`** (`WorldState`): Tracks discovered hosts, ports, services, CVEs, credentials, and evidence artifacts.
* **`state_machine.py`** (`ReasoningStateMachine`): Manages engine states (IDLE, PLANNING, WAITING_APPROVAL, EXECUTING, COLLECTING, REASONING, REFLECTING, REPLANNING, FINISHED, FAILED).
* **`contracts.py`**: Declares Pydantic data schemas representing `Goal` and `ReasoningDecision`.
* **`exceptions.py`**: Custom reasoning exceptions.







