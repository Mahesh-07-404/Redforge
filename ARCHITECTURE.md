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

