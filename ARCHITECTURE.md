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

