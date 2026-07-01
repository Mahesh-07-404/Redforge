# RedForge — Implementation Roadmap

**Version**: 2.0  
**Status**: Awaiting approval  
**Source documents**: 01_PROJECT_ANALYSIS.md, 02_NEW_ARCHITECTURE.md, 03_MODULE_BREAKDOWN.md, 04_DEPENDENCY_MAP.md, 05_MIGRATION_PLAN.md

---

## Guiding Rules

1. Every phase ends in a working, importable, runnable system.
2. Existing tests must pass at the end of every phase (unless that test covers code being deleted in that phase — noted explicitly).
3. New code is never added before the contracts it depends on exist.
4. Dead code is removed before new code replaces it — no parallel implementations that both run.
5. No phase modifies more than two architectural layers simultaneously.
6. Every phase has a named git tag as its exit point.

---

## Phase Map

```
Phase 0 → Foundation: Contracts + Dead Code
Phase 1 → Session Model: Workspace → Session
Phase 2 → Kernel: EventBus + SecurityGate + TurnOrchestrator
Phase 3 → Persistence: Repositories + Message/Finding stores
Phase 4 → Intelligence: Intent + Planner + Skills + Memory
Phase 5 → Execution: Tools + Verification + Findings
Phase 6 → Surfaces: Terminal + REST API + SDK
Phase 7 → Hardening: Shim removal + CI enforcement
...
Phase 16 → Unified API Gateway: FastAPI REST & WebSockets
Phase 17 → React Dashboard: React Operations Interface
Phase 18 → Distributed Execution Platform: Workflows Workers
Phase 19 → Observability & Monitoring: Telemetry Metrics
```

---

## Phase 0 — Foundation: Contracts + Dead Code Removal

**Git tag**: `v2.0.0-phase-0`

### Objective

Establish the canonical contract layer that all future phases build on. Remove every dead, duplicate, and orphaned module so no future phase accidentally builds on broken foundations. Zero behavior change to the running system.

---

### Files to Create

```
src/redforge/contracts/finding.py
src/redforge/contracts/events.py
src/redforge/contracts/plan.py
```

**`contracts/finding.py`** — Single canonical Finding definition (consolidates three scattered definitions):
```python
# Enums: Severity, FindingStatus
# Models: Evidence, Finding
# Replaces: core/state.py::Finding, modes/mode_implementations.py::Finding,
#           contracts/report.py::Finding (partial)
```

**`contracts/events.py`** — Typed event models (replaces dict-based events in agent.py):
```python
# Base: KernelEvent(BaseModel) { event_type, session_id, timestamp }
# Events: RunStartEvent, RunEndEvent, AssistantTokenEvent, AssistantEndEvent,
#         ToolStartEvent, ToolEndEvent, FindingEvent, PlanUpdatedEvent,
#         ConfirmationRequiredEvent, MemoryStoredEvent, ErrorEvent
```

**`contracts/plan.py`** — Execution plan models:
```python
# Enums: StepStatus
# Models: PlanStep, Phase, ExecutionPlan
```

---

### Files to Modify

**`src/redforge/contracts/session.py`** — Expand with new types required by other contracts:
- Add `Target(BaseModel)` with `value: str`, `type: TargetType`, `scope: ScopePolicy`
- Add `ScopePolicy(BaseModel)` with `allowed: list[str]`, `excluded: list[str]`
- Add `TargetType(str, Enum)`: Domain, IP, URL, APK, CIDR
- Add `SessionMode(str, Enum)`: BugBounty, CTF, Pentest, Learning, Coding, Android
- Add `SessionStatus(str, Enum)`: Active, Paused, Completed, Archived
- Expand `SessionState` → rename to `Session`; add `status`, `metadata`, `memory_namespace` fields
- Keep `SessionState` as a type alias for backward compatibility: `SessionState = Session`

**`src/redforge/contracts/intent.py`** — Minor updates:
- Add `Chat = "chat"` to `IntentType`
- Add `Critical = "critical"` to `RiskLevel`
- Add `is_chat: bool` field to `ParsedIntent`
- Keep `ParsedIntent` name (used in active tests)

**`src/redforge/contracts/tool.py`** — Add UUID fields and new status values:
- Add `id: UUID` to `ToolCall`
- Add `id: UUID`, `tool_call_id: UUID` to `ToolResult`
- Add `ToolExecution(BaseModel)` with `call`, `result`, `verified` fields
- Add `FailedHallucination = "failed_hallucination"` to `VerificationStatus`

**`src/redforge/contracts/memory.py`** — Expand:
- Add `MemoryTier(str, Enum)`: Short, Long
- Add `tier: MemoryTier`, `session_id: UUID`, `created_at: datetime` to `MemoryEntry`
- Add `MemoryContext(BaseModel)` with `entries`, `formatted`, `total_tokens`

**`src/redforge/contracts/report.py`** — Slim down (Finding moves to `contracts/finding.py`):
- Remove `Finding` class (now in `contracts/finding.py`)
- Keep `Report`, `ReportRequest`, `Severity` → `Severity` moves to `contracts/finding.py`
- Add `ReportFormat(str, Enum)`: Markdown, JSON, PDF, HTML
- Add `ReportSummary(BaseModel)` with severity counts

**`src/redforge/contracts/__init__.py`** — Re-export all contract types from one place

---

### Files to Remove

```
src/redforge/memory/workspace.py         ← WorkspaceManager, WorkspaceMemory (dead)
src/redforge/memory/memory_manager.py    ← legacy MemoryManager, WorkspaceMemoryManager (dead)
src/redforge/memory/vector.py            ← VectorStore, create_vector_store (only used by dead files)
src/redforge/memory/skill_index.py       ← SkillIndex (never called from active pipeline)
src/redforge/database/database.py        ← orphaned, zero imports
src/redforge/database/                   ← remove entire directory
src/redforge/modes/base.py               ← duplicate BaseMode (second copy in mode_implementations.py)
src/redforge/reports/generators.py       ← CVE/report generators, not imported by engine.py
```

**Remove duplicate class definitions (not whole files):**
- `core/state.py::Finding` dataclass — replaced by `contracts/finding.py::Finding`
- `core/state.py::Message` dataclass — replaced by existing `providers/base.py::Message`
- `core/state.py::ToolCall` dataclass — replaced by `contracts/tool.py::ToolCall`
- `modes/mode_implementations.py::Finding` dataclass — replaced by `contracts/finding.py::Finding`

**Gitignore additions:**
```
workspaces/
data/
*.db
logs/
```

---

### Interfaces

All interfaces in this phase are pure data contracts (Pydantic models). No executable logic. No abstract base classes yet.

The one structural rule enforced from this phase forward:
```
contracts/* MUST NOT import from any redforge module.
contracts/* MAY import from: pydantic, datetime, uuid, enum, typing (stdlib only).
```

---

### Tests

**Keep and verify passing** (these must still pass after Phase 0):
- `tests/unit/test_intent_engine.py` — imports `contracts/intent.py`; passes if `ParsedIntent` keeps its name
- `tests/unit/test_session_manager.py` — imports `contracts/session.py`; passes if `SessionState` alias kept
- `tests/unit/test_tool_executor.py` — imports `contracts/tool.py`; passes if `ToolCall` keeps its fields
- `tests/unit/test_verifier.py` — imports `contracts/tool.py`
- `tests/unit/test_report_engine.py` — imports `contracts/report.py`
- `tests/unit/test_skill_loader.py`
- `tests/unit/test_memory_manager.py` — **may break** if memory_manager.py import is tested directly; update import path
- `tests/integration/test_full_session.py`

**New tests to add** (`tests/unit/test_contracts.py`):
```python
# test: contracts/finding.py imports cleanly (no redforge imports)
# test: contracts/events.py imports cleanly
# test: contracts/plan.py imports cleanly
# test: Finding has all required fields (id, session_id, title, severity, status, evidence)
# test: SessionState is a valid alias for Session
# test: ToolExecution model validates correctly
```

---

### Acceptance Criteria

- [ ] `python -c "from redforge.contracts import finding, events, plan, session, intent, tool, memory, report"` succeeds with no errors
- [ ] `from redforge.contracts.finding import Finding` produces the canonical Finding class
- [ ] `from redforge.contracts.session import Session, SessionState` both work (alias preserved)
- [ ] No `redforge` import appears inside any `contracts/*.py` file
- [ ] `python -c "from redforge.memory import workspace"` raises `ImportError` (file deleted)
- [ ] `python -c "from redforge.database import database"` raises `ImportError` (dir deleted)
- [ ] All pre-existing passing tests still pass
- [ ] `git tag v2.0.0-phase-0`

---

## Phase 1 — Session Model: Workspace → Session

**Git tag**: `v2.0.0-phase-1`

### Objective

Make `Session` the sole state primitive throughout the active pipeline. Remove all `Workspace` references from config, pipeline, agent, and memory. Memory becomes session-isolated (no more hardcoded `workspace_id = "default"`). No new packages — only the existing `core/` and `memory/` modules are modified.

---

### Files to Create

```
data/.gitkeep                   ← replaces workspaces/ as the runtime data directory
```

---

### Files to Modify

**`config/config.py`**:
- Remove `WorkspaceConfig` class
- Add `SessionConfig(BaseModel)` with: `data_dir: str = "./data"`, `max_active_sessions: int = 10`, `retention_days: int = 90`
- Remove `workspace: WorkspaceConfig` from `Settings`
- Add `session: SessionConfig` to `Settings`
- Update `find_config_file()` — no changes needed

**`config.yaml`**:
- Remove `workspace:` section entirely
- Add:
  ```yaml
  session:
    data_dir: ./data
    max_active_sessions: 10
    retention_days: 90
  ```
- Update `memory.persist_dir` default from `./workspaces` to `./data`

**`src/redforge/core/session.py`** — Expand `SessionService` and `SessionStore`:
- `SessionStore._init_db()`: add columns `status TEXT DEFAULT 'active'`, `metadata TEXT DEFAULT '{}'`, `memory_namespace TEXT` to `sessions` table. Use `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` for migration safety.
- `SessionService.create()`: compute `memory_namespace = f"session_{sid[:8]}"` and persist it; use `contracts/session.py::Session` as return type (the expanded model). `session_id` parameter becomes `name: str = ""` optional (not breaking — existing call sites pass positional mode/target/autonomy).
- `SessionService.load()`: return `Session` (expanded model) with `status`, `metadata`, `memory_namespace` populated.
- `SessionService.archive()`: new method — sets `status = "archived"` in DB.
- `SessionService.list()`: new method — returns `list[dict]` ordered by `updated_at DESC`. Accepts optional `status` filter.
- `SessionService.set_target()`: no change in signature, update to write `Target` object JSON to metadata column if target is complex.

**`src/redforge/memory/manager.py`** — Fix session isolation:
- Remove `self.workspace_id = "default"` line from `__init__`
- Change `get_context_for_llm(self, query)` → `get_context_for_llm(self, query, session_id: str)` — passes `session_id` to `retrieve()`
- `store(self, session_id, entry)`: already takes `session_id`; remove the internal override
- `retrieve(self, session_id, query)`: already takes `session_id`; pass it through to `QdrantAdapter`
- `QdrantAdapter.store()` and `retrieve()`: use `session_id` as part of collection name (`f"redforge_{session_id[:8]}"`) — this was already the intent but `workspace_id` was overriding it

**`src/redforge/core/pipeline.py`** — Clean up workspace references:
- Remove `workspace_id` parameter from `process_turn()` signature (it was aliased to `session_id` anyway)
- Change `memory_manager.get_context_for_llm(raw_input)` → `memory_manager.get_context_for_llm(raw_input, session_id)`
- The `MemoryEntry` store call already uses `session_id`; verify and leave

**`src/redforge/core/agent.py`** — Clean up:
- `run()`: remove `workspace_id: Optional[str] = None` parameter
- Change `sid = session_id or workspace_id or "default"` → `sid = session_id or "default"`
- No other changes

---

### Files to Remove

None in this phase. The `workspaces/` directory is runtime data — it is gitignored but not force-deleted. Any existing `workspaces/` data simply stops being read (because `data_dir` now points to `./data`).

---

### Interfaces

**`SessionService` public interface after Phase 1**:
```python
class SessionService:
    def create(self, mode: str, target: str | None, autonomy: str,
               session_id: str | None = None, name: str = "") -> Session
    def load(self, session_id: str) -> Session | None
    def save(self, session: Session) -> None
    def set_target(self, session_id: str, new_target: str | None) -> None
    def archive(self, session_id: str) -> None        # NEW
    def list(self, status: str | None = None) -> list[dict]  # NEW
    def delete(self, session_id: str) -> None
    def list_sessions(self) -> list[dict]             # kept for backward compat
```

**`MemoryManager` public interface after Phase 1**:
```python
class MemoryManager:
    def store(self, session_id: str, entry: MemoryEntry, long_term: bool = False) -> None
    def retrieve(self, session_id: str, query: str, top_k: int = 5) -> list[MemoryEntry]
    def flush_session(self, session_id: str) -> None
    def get_context_for_llm(self, query: str, session_id: str) -> str   # session_id now required
    def add_finding(self, ...) -> None
```

---

### Tests

**Update existing** (argument changes):
- `tests/integration/test_full_session.py` — remove `memory_manager.workspace_id = session.id` line; `get_context_for_llm` now takes `session_id`
- `tests/unit/test_memory_manager.py` — add `session_id` argument to `get_context_for_llm` calls

**New tests** (`tests/unit/test_session_v2.py`):
```python
# test: session.create() returns Session with status="active", memory_namespace set
# test: session.archive() sets status="archived"; load() reflects it
# test: session.list(status="active") returns only active sessions
# test: two sessions have different memory_namespace values
# test: memory stored under session A is NOT retrieved under session B
# test: config loads without workspace: section in yaml
```

---

### Acceptance Criteria

- [ ] `from redforge.config.config import Settings` — `Settings` has no `workspace` attribute
- [ ] `SessionService.create()` returns a `Session` with `memory_namespace` set to `f"session_{sid[:8]}"`
- [ ] `SessionService.archive("some-id")` sets `status = "archived"` in the DB
- [ ] `SessionService.list(status="active")` returns only non-archived sessions
- [ ] Memory stored in session A is not returned by `retrieve(session_B_id, ...)`
- [ ] `agent.run(user_input, session_id="abc")` works without `workspace_id` argument
- [ ] `pipeline.process_turn("scan x.com", "abc")` works without `workspace_id` argument
- [ ] All existing passing tests still pass
- [ ] `git tag v2.0.0-phase-1`

---

## Phase 2 — Kernel: EventBus + SecurityGate + TurnOrchestrator

**Git tag**: `v2.0.0-phase-2`

### Objective

Extract the orchestration layer into a clean `kernel/` package. Create a typed `EventBus` to replace the dict-based `_event_handlers` in `RedForgeAgent`. Create `SecurityGate` as the single mandatory checkpoint for all tool actions (unifying safety scope checks and autonomy control). Create `TurnOrchestrator` that holds the agentic loop. `RedForgeAgent` and `Pipeline` become thin compatibility shims — their external behavior is unchanged.

---

### Files to Create

```
src/redforge/kernel/__init__.py
src/redforge/kernel/kernel.py
src/redforge/kernel/event_bus.py
src/redforge/kernel/security_gate.py
src/redforge/kernel/turn_orchestrator.py
src/redforge/kernel/session_service.py
```

**`kernel/event_bus.py`**:
```python
# EventHandler = Callable[[KernelEvent], Awaitable[None]]
class EventBus:
    async def publish(self, event: KernelEvent) -> None
    def subscribe(self, event_type: type[KernelEvent], handler: EventHandler) -> None
    def subscribe_all(self, handler: EventHandler) -> None
    def unsubscribe(self, event_type: type[KernelEvent], handler: EventHandler) -> None
```

**`kernel/security_gate.py`**:
```python
class GateDecision(str, Enum): Allow, Confirm, Block

class GateResult(BaseModel):
    decision: GateDecision
    reason: str
    violation_type: str | None

class SecurityGate:
    def check(self, tool_name: str, command: list[str],
              target: str, risk_level: RiskLevel,
              session: Session) -> GateResult
    def check_command(self, command: str) -> GateResult
    def check_scope(self, target: str, session: Session) -> GateResult
    def check_autonomy(self, risk: RiskLevel, autonomy: AutonomyLevel) -> GateDecision
```

Consolidates logic from `core/safety.py::SafetyService.check_target()`, `core/safety.py::SafetyService.check_command()`, and the inline autonomy check in `core/pipeline.py::process_turn()`.

**`kernel/turn_orchestrator.py`**:

Extracts and cleans the `for i in range(max_iterations)` loop from `core/pipeline.py`. Receives all dependencies via constructor injection. Does not import from `core/`.

**`kernel/session_service.py`**:

Thin re-export: `from redforge.core.session import SessionService, SessionStore`. This establishes the correct import path for future phases without touching anything yet.

**`kernel/kernel.py`**:
```python
class RedForgeKernel:
    def __init__(self, config: Settings): ...
    def on(self, event_type: type[KernelEvent] | str, handler: Callable) -> None
    def off(self, event_type: type[KernelEvent] | str, handler: Callable) -> None
    async def run(self, user_input: str, session_id: str) -> dict
    async def confirm(self, session_id: str, pending_id: str) -> None
    async def deny(self, session_id: str, pending_id: str) -> None
    async def create_session(self, mode: str, target: str | None,
                              autonomy: str, name: str = "") -> Session
    async def load_session(self, session_id: str) -> Session | None
    async def list_sessions(self, status: str | None = None) -> list[dict]
```

`RedForgeKernel` builds all dependencies internally (replaces `core/factory.py`'s `create_redforge_agent`).

---

### Files to Modify

**`src/redforge/core/agent.py`** — Becomes a shim:
- Replace the entire constructor body with: `self._kernel = RedForgeKernel.from_kwargs(**kwargs)` (or keep pipeline construction for backward compat — either way, `agent.run()` delegates to kernel)
- `on()` / `off()` delegate to `self._kernel.on()` / `self._kernel.off()`
- `run()` delegates to `self._kernel.run()`
- Keep `llm`, `skill_loader`, `tool_executor` properties (used by tests) — they delegate to kernel internals
- Keep `get_status()` method

**`src/redforge/core/pipeline.py`** — Becomes a shim:
- `process_turn()` delegates to `TurnOrchestrator.run_turn()`
- Constructor kept for `test_full_session.py` compatibility

**`src/redforge/core/safety.py`** — No deletion yet; `SafetyService` is kept. `SecurityGate` calls `SafetyService` internally in this phase — consolidation happens in Phase 7.

**`src/redforge/core/factory.py`** — Add `create_kernel()` factory function that returns `RedForgeKernel`. Keep `create_redforge_agent()` as a shim that calls `create_kernel()`.

---

### Files to Remove

None. Shims kept for test compatibility.

---

### Interfaces

**`RedForgeKernel` event subscription** — supports both old-style string events and new-style typed events:
```python
# New style (typed):
kernel.on(AssistantTokenEvent, lambda e: print(e.token))

# Old style (string, for backward compat):
kernel.on("token", lambda payload: print(payload["token"]))
```

EventBus internally normalizes: when publishing `AssistantTokenEvent`, it also fires string `"token"` handlers with the event as a dict.

**`SecurityGate.check()` return values**:
- `GateDecision.Allow` → tool executes immediately
- `GateDecision.Confirm` → `ConfirmationRequiredEvent` is published; execution pauses
- `GateDecision.Block` → `ErrorEvent` published with reason; tool does not execute

---

### Tests

**Existing tests must still pass** (shims protect them):
- All unit tests in `tests/unit/`
- `tests/integration/test_full_session.py`
- `tests/test_backend_events.py`

**New tests** (`tests/unit/test_kernel.py`):
```python
# test: EventBus.publish(AssistantTokenEvent) calls subscribed handler
# test: EventBus.publish fires both typed and wildcard ("*") handlers
# test: EventBus.unsubscribe removes handler correctly
# test: SecurityGate.check() returns Allow for safe command + Manual autonomy
# test: SecurityGate.check() returns Confirm for high-risk command + Partial autonomy
# test: SecurityGate.check() returns Block for out-of-scope target
# test: SecurityGate.check() returns Block for dangerous command (rm -rf /)
# test: RedForgeKernel.run() publishes RunStartEvent and RunEndEvent
# test: RedForgeKernel.create_session() returns Session with correct mode
```

**New tests** (`tests/unit/test_security_gate.py`):
```python
# test: scope check blocks target not in allowed list
# test: scope check allows target in allowed list
# test: command check blocks "rm -rf /"
# test: command check allows "nmap -sV target.com"
# test: autonomy=Manual + risk=Safe → Confirm (user must approve everything in Manual)
# test: autonomy=Partial + risk=Medium → Allow
# test: autonomy=Partial + risk=High → Confirm
# test: autonomy=Full + risk=High → Allow
# test: autonomy=Full + risk=Critical → Confirm
```

---

### Acceptance Criteria

- [ ] `from redforge.kernel import RedForgeKernel` imports cleanly
- [ ] `kernel.on(AssistantTokenEvent, handler)` calls `handler` when token is published
- [ ] `kernel.on("token", handler)` (old-style string) still calls `handler` for backward compat
- [ ] `SecurityGate.check()` for a blocked command returns `GateDecision.Block`
- [ ] `SecurityGate.check()` for out-of-scope target returns `GateDecision.Block`
- [ ] `RedForgeAgent.run()` still works identically to before (shim test: `test_full_session.py` passes)
- [ ] `create_redforge_agent()` still works (factory shim)
- [ ] `kernel.run("hello", session_id)` emits `RunStartEvent` and `RunEndEvent`
- [ ] All pre-existing tests pass
- [ ] `git tag v2.0.0-phase-2`

---

## Phase 3 — Persistence: Repository Layer

**Git tag**: `v2.0.0-phase-3`

### Objective

Create the `persistence/` package with clean repository interfaces and SQLite implementations for sessions, findings, messages, and reports. Move findings and message persistence out of the pipeline's in-memory state into proper durable stores. Memory store (Qdrant) gets a proper abstract interface. No pipeline logic changes.

---

### Files to Create

```
src/redforge/persistence/__init__.py
src/redforge/persistence/session_store.py
src/redforge/persistence/findings_store.py
src/redforge/persistence/message_store.py
src/redforge/persistence/report_store.py
src/redforge/persistence/memory_store.py
```

**`persistence/session_store.py`**:
```python
class SessionStore(Protocol):
    async def create(self, session: Session) -> Session
    async def load(self, session_id: str) -> Session | None
    async def save(self, session: Session) -> None
    async def list(self, status: str | None = None) -> list[dict]
    async def delete(self, session_id: str) -> None
    async def archive(self, session_id: str) -> None

class SQLiteSessionStore:
    """Async wrapper around core/session.py::SessionStore (sync)."""
    # Delegates to core/session.py::SessionService using asyncio.to_thread
```

**`persistence/findings_store.py`**:
```python
class FindingsStore(Protocol):
    async def add(self, finding: Finding) -> None
    async def list(self, session_id: str, severity: str | None = None) -> list[Finding]
    async def get(self, finding_id: str) -> Finding | None
    async def update(self, finding: Finding) -> None

class SQLiteFindingsStore:
    # SQLite table: findings (id, session_id, title, severity, status,
    #               description, target, evidence_json, cvss_score,
    #               cve_ids_json, cwe_id, remediation, created_at, tool_execution_id)
```

**`persistence/message_store.py`**:
```python
class MessageStore(Protocol):
    async def append(self, session_id: str, role: str, content: str) -> None
    async def load(self, session_id: str, limit: int = 50) -> list[dict]
    async def flush(self, session_id: str) -> None

class SQLiteMessageStore:
    # SQLite table: messages (id, session_id, role, content, created_at)
    # Uses same DB file as sessions (data/redforge.db)
```

**`persistence/report_store.py`**:
```python
class ReportStore:
    def __init__(self, reports_dir: Path)
    async def generate(self, session: Session, findings: list[Finding],
                       format: ReportFormat) -> Report
    async def save(self, report: Report) -> Path
    async def list(self, session_id: str) -> list[dict]
    # Markdown formatter: existing ReportFormatter logic moved here
    # JSON formatter: existing to_json logic moved here
```

**`persistence/memory_store.py`**:
```python
class MemoryStore(Protocol):
    async def store(self, entry: MemoryEntry) -> None
    async def search(self, embedding: list[float], session_id: str,
                     top_k: int) -> list[MemoryEntry]
    async def flush(self, session_id: str) -> None
    async def is_available(self) -> bool

class QdrantMemoryStore:
    # Wraps existing memory/vector_store.py::QdrantAdapter
    # Uses session_id for collection namespacing
    
class FallbackMemoryStore:
    # JSON file fallback when Qdrant unavailable
    # Wraps existing fallback logic in QdrantAdapter
```

---

### Files to Modify

**`src/redforge/kernel/session_service.py`** — Replace the re-export shim with real implementation:
- Import from `persistence/session_store.py::SQLiteSessionStore`
- `SessionService` in kernel now delegates to `SQLiteSessionStore`

**`src/redforge/kernel/kernel.py`** — Wire persistence stores:
- Constructor creates `SQLiteSessionStore`, `SQLiteFindingsStore`, `SQLiteMessageStore`, `ReportStore`, `QdrantMemoryStore`
- Pass stores to `TurnOrchestrator`

**`src/redforge/kernel/turn_orchestrator.py`** — Add persistence calls:
- After each assistant message: `await message_store.append(session_id, "assistant", content)`
- After user message: `await message_store.append(session_id, "user", raw_input)`
- After verified finding: `await findings_store.add(finding)`
- Load history on turn start: `messages = await message_store.load(session_id, limit=20)`

**`src/redforge/reports/engine.py`** — Add delegation to `ReportStore`:
- `ReportService.generate()` now optionally calls `report_store.save()` if store is injected
- Keep `ReportCollector.findings` list for in-memory use during a session

---

### Files to Remove

None this phase.

---

### Interfaces

**SQLite database schema** (`data/redforge.db`):
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    name TEXT DEFAULT '',
    mode TEXT,
    status TEXT DEFAULT 'active',
    target_json TEXT,
    autonomy TEXT,
    memory_namespace TEXT,
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT,
    content TEXT,
    created_at TEXT
);

CREATE TABLE findings (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    title TEXT,
    severity TEXT,
    status TEXT DEFAULT 'open',
    description TEXT,
    target TEXT,
    evidence_json TEXT,
    cvss_score REAL,
    cve_ids_json TEXT,
    cwe_id TEXT,
    remediation TEXT,
    tool_execution_id TEXT,
    created_at TEXT
);
```

---

### Tests

**New tests** (`tests/unit/test_persistence.py`):
```python
# All tests use tmp_path with in-memory or temp SQLite

# SessionStore tests:
# test: create() inserts row; load() returns it
# test: archive() sets status=archived; load() reflects it
# test: list(status="active") excludes archived sessions
# test: delete() removes session and cascades to messages/findings

# FindingsStore tests:
# test: add(finding) inserts; list(session_id) returns it
# test: list(session_id, severity="high") filters correctly
# test: get(finding_id) returns correct finding
# test: update(finding) persists changes

# MessageStore tests:
# test: append() adds message; load(session_id) returns ordered list
# test: load(limit=3) returns only last 3 messages
# test: flush(session_id) removes all messages for session

# ReportStore tests:
# test: generate() returns Report with correct finding counts
# test: save() creates .md file at expected path
# test: list(session_id) returns saved report metadata

# MemoryStore tests:
# test: QdrantMemoryStore.is_available() returns True when Qdrant present
# test: FallbackMemoryStore.store() and search() work without Qdrant
# test: search returns entries only from correct session_id
```

**Update existing** (`tests/integration/test_full_session.py`):
- After `pipeline.process_turn()`, assert messages were persisted: `messages = await message_store.load(session.id)`

---

### Acceptance Criteria

- [ ] `from redforge.persistence import SQLiteSessionStore, SQLiteFindingsStore, SQLiteMessageStore, ReportStore, QdrantMemoryStore` imports cleanly
- [ ] `FindingsStore.add(finding)` persists to SQLite; survives process restart
- [ ] `MessageStore.append()` then `MessageStore.load()` returns messages in correct order
- [ ] `ReportStore.generate()` produces a valid markdown string with finding counts
- [ ] `ReportStore.save()` writes a `.md` file to `data/reports/{session_id}/`
- [ ] `FallbackMemoryStore` works when Qdrant is not installed
- [ ] `TurnOrchestrator` persists user and assistant messages to `MessageStore` during a turn
- [ ] All pre-existing tests pass
- [ ] `git tag v2.0.0-phase-3`

---

## Phase 4 — Intelligence: Intent + Planner + Skills + Memory

**Git tag**: `v2.0.0-phase-4`

### Objective

Create the `intelligence/` package. Replace keyword-based intent parsing with LLM-based classification (with keyword fallback). Create real `PlannerEngine` that generates structured AI plans. Move skill loading to `SkillEngine` with startup indexing. Create `MemoryEngine` with real embedding support (local `sentence-transformers`, fallback to hash). Create `PromptBuilder` that assembles the system prompt cleanly. Wire all into `TurnOrchestrator`. Existing `core/intent.py` and `core/planner.py` become shims.

---

### Files to Create

```
src/redforge/intelligence/__init__.py
src/redforge/intelligence/intent_engine.py
src/redforge/intelligence/planner_engine.py
src/redforge/intelligence/skill_engine.py
src/redforge/intelligence/memory_engine.py
src/redforge/intelligence/prompt_builder.py
src/redforge/infrastructure/__init__.py
src/redforge/infrastructure/embedding_provider.py
```

**`infrastructure/embedding_provider.py`**:
```python
class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
    @property
    def dimensions(self) -> int: ...

class HashEmbeddingProvider(EmbeddingProvider):
    """MD5-based deterministic embeddings. No semantic meaning.
    Used as fallback when no real embedder available.
    dimensions = 384 (padded/truncated to match Qdrant config)"""

class SentenceTransformerProvider(EmbeddingProvider):
    """Local embeddings via sentence-transformers.
    Default model: all-MiniLM-L6-v2 (dimensions=384)
    Loaded lazily on first call."""

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """text-embedding-3-small (dimensions=1536)"""

class GeminiEmbeddingProvider(EmbeddingProvider):
    """embedding-001 (dimensions=768)"""

def get_embedding_provider(config: Settings) -> EmbeddingProvider:
    """Factory: returns best available provider based on config."""
```

**`intelligence/intent_engine.py`**:
```python
class IntentEngine:
    def __init__(self, llm_gateway, use_llm: bool = True): ...
    
    async def analyze(self, raw_input: str, session: Session) -> Intent:
        """
        If use_llm=True: calls llm_gateway.classify() with a structured
        classification prompt. Parses JSON response into Intent.
        
        Falls back to keyword parser if LLM call fails or use_llm=False.
        
        Classification prompt returns JSON:
        {
          "type": "scan|recon|exploit|report|learn|configure|chat|clarify",
          "risk": "safe|low|medium|high|critical",
          "target": "example.com or null",
          "is_chat": true/false,
          "entities": {}
        }
        """
    
    def _keyword_fallback(self, raw_input: str, session: Session) -> Intent:
        """Existing keyword logic from core/intent.py::IntentParser"""
```

**`intelligence/planner_engine.py`**:
```python
class PlannerEngine:
    def __init__(self, llm_gateway): ...
    
    async def create_plan(self, intent: Intent, session: Session) -> ExecutionPlan:
        """LLM generates a structured plan. Prompt instructs model to return JSON:
        { "summary": "...", "phases": [{ "id": "recon", "name": "Reconnaissance",
          "steps": [{"id":"s1","description":"...","tool":"nmap","status":"pending"}] }] }
        Falls back to a static 4-phase template if LLM fails."""
    
    async def update_plan(self, plan: ExecutionPlan,
                          results: list[VerifiedResult]) -> ExecutionPlan:
        """Marks completed steps based on results. No LLM call."""
    
    def get_next_step(self, plan: ExecutionPlan) -> PlanStep | None:
        """Returns first pending step across all phases."""
```

**`intelligence/skill_engine.py`**:
```python
class SkillEngine:
    def __init__(self, skills_dir: Path): ...
    
    def build_index(self) -> None:
        """Called once at startup. Loads all .md files from skills_dir.
        Delegates to existing SkillRegistry + DynamicSkillLoader logic.
        Caches result — no filesystem walk on subsequent calls."""
    
    def select(self, intent: Intent, session: Session) -> SkillSet:
        """Tiered selection: Tier0(system) + Tier1(safety) + Tier2(mode) +
        Tier3(tools) + Tier4(execution). Returns SkillSet dataclass."""
    
    def build_context(self, skill_set: SkillSet) -> str:
        """Formats skills into system prompt block. Existing logic from
        DynamicSkillLoader.build_context()."""

@dataclass
class SkillSet:
    tier0: list  # system skills
    tier1: list  # safety skills
    tier2: list  # mode skill
    tier3: list  # tool skills
    tier4: list  # execution skills
```

**`intelligence/memory_engine.py`**:
```python
class MemoryEngine:
    def __init__(self, embedding_provider: EmbeddingProvider,
                 memory_store: MemoryStore): ...
    
    async def store(self, content: str, session_id: str,
                    tier: MemoryTier = MemoryTier.Short,
                    metadata: dict = {}) -> None:
        """Embeds content, creates MemoryEntry, stores in MemoryStore."""
    
    async def retrieve(self, query: str, session_id: str,
                       top_k: int = 5) -> list[MemoryEntry]:
        """Embeds query, searches MemoryStore by cosine similarity."""
    
    async def get_llm_context(self, query: str, session_id: str) -> MemoryContext:
        """Retrieves top entries, formats as MemoryContext for prompt assembly."""
    
    async def flush_session(self, session_id: str) -> None:
        """Removes short-term entries for session."""
```

**`intelligence/prompt_builder.py`**:
```python
class PromptBuilder:
    def build(self, session: Session, intent: Intent,
              skill_context: str, memory_context: MemoryContext,
              plan: ExecutionPlan | None = None) -> str:
        """Assembles final system prompt. Pure function — no I/O.
        Format:
        ## IDENTITY
        ## ACTIVE SESSION
        ## SKILLS & GUIDELINES
        ## MEMORY CONTEXT
        ## EXECUTION PLAN (if present)
        ## INSTRUCTIONS
        """
```

---

### Files to Modify

**`src/redforge/kernel/turn_orchestrator.py`** — Wire intelligence layer:
- Replace direct `IntentService` import with `IntentEngine`
- Replace direct `PlannerService` import with `PlannerEngine`
- Replace `DynamicSkillLoader` with `SkillEngine`
- Replace `MemoryManager.get_context_for_llm()` with `MemoryEngine.get_llm_context()`
- After each turn: `await memory_engine.store(content=response, session_id=...)`
- Add `intent.is_chat` check: if `True`, skip tool parsing loop; just emit assistant response

**`src/redforge/core/intent.py`** — Becomes a shim:
- `IntentService.process()` delegates to `IntentEngine.analyze()`
- Existing `TargetWatcher`, `TargetStateMachine`, `EventBus` kept for test compatibility

**`src/redforge/core/planner.py`** — Becomes a shim:
- `PlannerService.build_system_prompt()` delegates to `PromptBuilder.build()`
- `PlannerService.generate_plan()` delegates to `PlannerEngine.create_plan()`

**`pyproject.toml`** — Add optional dependency:
```toml
[project.optional-dependencies]
embeddings = ["sentence-transformers>=2.2.0"]
```

**`config/config.py`** — Add `IntelligenceConfig`:
```python
class IntelligenceConfig(BaseModel):
    use_llm_intent: bool = False    # feature flag; True after validation
    embedding_provider: str = "hash"  # "hash" | "sentence-transformers" | "openai" | "gemini"
    embedding_model: str = "all-MiniLM-L6-v2"
```

---

### Files to Remove

None. Shims kept.

---

### Interfaces

**Intent classification LLM prompt** (used by `IntentEngine`):
```
System: You are an intent classifier for a cybersecurity AI agent.
Classify the user input into exactly one JSON object with these fields:
- type: one of [scan, recon, exploit, report, learn, configure, chat, clarify]
- risk: one of [safe, low, medium, high, critical]  
- target: domain/IP/URL if mentioned, else null
- is_chat: true if conversational (no security action), false otherwise
- entities: dict of named entities found

Respond ONLY with JSON. No explanation.
```

**Plan generation LLM prompt** (used by `PlannerEngine`):
```
System: You are an execution planner for a cybersecurity AI agent.
Given the user's intent and session context, generate a structured plan as JSON.
Schema: { "summary": string, "phases": [{ "id": string, "name": string,
  "steps": [{ "id": string, "description": string, "tool": string|null }] }] }
Respond ONLY with JSON.
```

---

### Tests

**New tests** (`tests/unit/test_intelligence.py`):
```python
# IntentEngine tests:
# test: keyword fallback classifies "scan example.com" as IntentType.Scan
# test: keyword fallback classifies "hello" as IntentType.Chat with is_chat=True
# test: keyword fallback extracts "example.com" as target
# test: LLM-based intent parses JSON response correctly
# test: IntentEngine falls back to keyword parser if LLM raises exception

# PlannerEngine tests:
# test: create_plan() with mocked LLM returns ExecutionPlan with phases
# test: fallback plan has 4 phases (Recon, Scan, Exploit, Report)
# test: update_plan() marks steps as done when results passed
# test: get_next_step() returns first pending step

# SkillEngine tests:
# test: build_index() loads all .md files from skills/ directory
# test: select() with mode=bugbounty returns at least one Tier2 skill
# test: select() always returns at least one Tier0 (system) skill
# test: build_context() returns non-empty string

# MemoryEngine tests:
# test: store() then retrieve() returns the stored entry
# test: retrieve() with different session_id returns empty list
# test: get_llm_context() returns MemoryContext with formatted string
# test: flush_session() removes short-term entries

# EmbeddingProvider tests:
# test: HashEmbeddingProvider.embed() returns list of 384 floats
# test: HashEmbeddingProvider.embed("a") != embed("b")
# test: SentenceTransformerProvider.embed() returns correct dimensions (if installed)
```

---

### Acceptance Criteria

- [ ] `from redforge.intelligence import IntentEngine, PlannerEngine, SkillEngine, MemoryEngine, PromptBuilder` imports cleanly
- [ ] `IntentEngine._keyword_fallback("scan example.com", session)` returns `Intent(type=Scan, target="example.com")`
- [ ] `IntentEngine.analyze("hello how are you", session)` returns `Intent(is_chat=True)`
- [ ] `PlannerEngine.create_plan()` with mocked LLM returns `ExecutionPlan` with at least one phase
- [ ] `SkillEngine.build_index()` indexes all 27 skill files without error
- [ ] `SkillEngine.select()` for mode=bugbounty, intent=scan returns ≥ 5 skills across tiers
- [ ] `MemoryEngine.store()` then `MemoryEngine.retrieve()` returns stored content (any embedding backend)
- [ ] `PromptBuilder.build()` returns string containing session target when target is set
- [ ] `HashEmbeddingProvider.embed(text)` returns list of exactly 384 floats
- [ ] `turn_orchestrator` chat-only turns (is_chat=True) do NOT parse TOOL: blocks
- [ ] All pre-existing tests pass
- [ ] `git tag v2.0.0-phase-4`

---

## Phase 5 — Execution: Tools + Verification + Findings

**Git tag**: `v2.0.0-phase-5`

### Objective

Create the `execution/` package with a dynamic `ToolRegistry`, a clean `ToolOrchestrator`, and a proper `VerificationGateway`. Fix `ToolRegistry` from a hardcoded 3-tool list to dynamic PATH discovery. Move tool schemas to a proper location. Fix `VerificationService`'s broken scope check. Create `FindingsEngine` that extracts findings from both LLM text and tool results. Remove `langgraph` and `langchain-core` from dependencies.

---

### Files to Create

```
src/redforge/execution/__init__.py
src/redforge/execution/tool_orchestrator.py
src/redforge/execution/tool_registry.py
src/redforge/execution/tool_runner.py
src/redforge/execution/tool_installer.py
src/redforge/execution/tool_parser.py
src/redforge/execution/verification_gateway.py
src/redforge/execution/findings_engine.py
src/redforge/execution/llm_gateway.py
```

**`execution/tool_registry.py`** — Dynamic discovery (replaces hardcoded list):
```python
class ToolRegistry:
    KNOWN_SECURITY_TOOLS = [
        "nmap", "ffuf", "sqlmap", "nikto", "gobuster", "dirb",
        "hydra", "hashcat", "john", "subfinder", "amass", "nuclei",
        "metasploit", "msfconsole", "burpsuite", "wireshark",
        "gdb", "pwntools", "binwalk", "apktool", "jadx", "frida"
    ]
    
    def __init__(self, extra_paths: list[Path] | None = None): ...
    def discover(self) -> None:
        """Check each KNOWN_SECURITY_TOOL against shutil.which().
        Also walk extra_paths for any executables."""
    def is_available(self, tool_name: str) -> bool: ...
    def list_available(self) -> list[str]: ...
    def get_path(self, tool_name: str) -> Path | None: ...
```

**`execution/tool_runner.py`** — Moved from `tools/runner.py`, no logic change.

**`execution/tool_installer.py`** — Moved from `tools/installer.py`, no logic change.

**`execution/tool_parser.py`** — Moved from `tools/parser.py`, no logic change.

**`execution/verification_gateway.py`** — Replaces broken `core/verifier.py` scope check:
```python
class VerificationGateway:
    def verify(self, result: ToolResult, session: Session) -> VerifiedResult:
        """
        FIX: The old scope check was: session.target not in str(tool_result.command)
        This fails for targets with subdomains or paths.
        
        New check: if session.target is set, verify that the command contains
        a token that is a suffix-match of the target domain, OR the target IP.
        Uses urllib.parse.urlparse for URL targets.
        """
    
    def validate_llm_response(self, response: str, session: Session) -> ValidationResult:
        """Moves HallucinationGuard + ResponseValidator logic from core/verifier.py."""

@dataclass
class ValidationResult:
    valid: bool
    reason: str
```

**`execution/findings_engine.py`**:
```python
class FindingsEngine:
    def extract_from_llm(self, content: str, session: Session) -> list[Finding]:
        """Parses 'FINDING: type | SEVERITY: level | description' lines.
        Moved from findings/engine.py::FindingsService."""
    
    def extract_from_tool(self, verified: VerifiedResult,
                           session: Session) -> list[Finding]:
        """Creates a Finding from a verified tool result.
        Moved from reports/engine.py::ReportCollector.add_from_verified()."""
```

**`execution/llm_gateway.py`**:
```python
class LLMGateway:
    def __init__(self, provider: LLMProvider): ...
    def set_provider(self, provider: LLMProvider) -> None: ...
    
    async def chat(self, messages: list[Message],
                   stream: bool = False) -> ChatResponse | AsyncIterator[str]:
    
    async def classify(self, prompt: str, instruction: str) -> str:
        """Lightweight call. Uses same provider. Returns raw string.
        Used by IntentEngine and PlannerEngine for structured JSON responses."""
    
    def count_tokens(self, text: str) -> int:
        """Approximation: len(text.split()) * 1.3. Provider-specific if available."""
```

**`execution/tool_orchestrator.py`**:
```python
class ToolOrchestrator:
    def __init__(self, registry: ToolRegistry, runner: ToolRunner,
                 installer: ToolInstaller, security_gate: SecurityGate,
                 event_bus: EventBus): ...
    
    async def parse_and_execute(self, llm_response: str,
                                 session: Session) -> list[ToolExecution]:
        """
        1. tool_parser.parse_tool_calls(llm_response) → list[dict]
        2. For each parsed call:
           a. security_gate.check() → GateResult
           b. If Block: log, skip
           c. If Confirm: publish ConfirmationRequiredEvent; return early
           d. If Allow: runner.run(ToolCall) → ToolResult
           e. publish ToolStartEvent before, ToolEndEvent after
        3. Return list[ToolExecution]
        """
```

---

### Files to Modify

**`src/redforge/kernel/turn_orchestrator.py`** — Replace all tool-related imports:
- Import `ToolOrchestrator`, `VerificationGateway`, `FindingsEngine` from `execution/`
- Import `LLMGateway` from `execution/`
- Remove direct `parse_tool_calls` call (now inside `ToolOrchestrator`)
- Remove direct `ToolExecutor` usage (now inside `ToolOrchestrator`)
- Call `verification_gateway.verify()` after each tool execution
- Call `findings_engine.extract_from_llm()` on each LLM response
- Call `findings_engine.extract_from_tool()` on each verified result
- Call `findings_store.add()` for each extracted finding

**`src/redforge/tools/executor.py`** — Becomes shim delegating to `execution/tool_orchestrator.py`

**`src/redforge/tools/runner.py`** — Becomes shim delegating to `execution/tool_runner.py`

**`src/redforge/tools/registry.py`** — Becomes shim delegating to `execution/tool_registry.py`

**`src/redforge/core/verifier.py`** — Becomes shim delegating to `execution/verification_gateway.py`

**`src/redforge/findings/engine.py`** — Becomes shim delegating to `execution/findings_engine.py`

**`pyproject.toml`**:
- Remove `langgraph>=0.0.20` from `dependencies`
- Remove `langchain-core>=0.1.0` from `dependencies`
- These packages are not imported anywhere in the active codebase

---

### Files to Remove

None (shims kept for this phase).

---

### Interfaces

**`ToolRegistry.discover()` behavior**:
- Called once at `RedForgeKernel` startup, not per-turn
- Results cached in `self._available: dict[str, Path]`
- `is_available("nmap")` returns True only if `shutil.which("nmap")` returns a path

**`VerificationGateway.verify()` scope check fix**:

Old (broken): `if session.target not in str(tool_result.command)`
New (correct):
```python
def _target_in_command(self, target: str, command: list[str]) -> bool:
    from urllib.parse import urlparse
    parsed = urlparse(target if "://" in target else f"https://{target}")
    hostname = parsed.hostname or target
    cmd_str = " ".join(command)
    return any(
        hostname in token or token.endswith(f".{hostname}")
        for token in command
    )
```

---

### Tests

**Update existing** (path changes):
- `tests/unit/test_tool_executor.py` — update import if executor becomes a shim
- `tests/unit/test_verifier.py` — add test for the fixed scope check

**New tests** (`tests/unit/test_execution.py`):
```python
# ToolRegistry tests:
# test: discover() finds "echo" (always available on Unix)
# test: is_available("echo") returns True after discover()
# test: is_available("definitely-not-a-real-tool-xyz") returns False
# test: list_available() returns list (may be empty on minimal system)

# ToolRunner tests (integration, uses real subprocess):
# test: run(ToolCall with command=["echo", "hello"]) returns exit_code=0, stdout="hello\n"
# test: run(ToolCall with timeout=0.001) returns timed_out=True

# ToolOrchestrator tests:
# test: parse_and_execute("TOOL: echo\nCOMMAND: echo hello", session) with Allow gate
#       returns list with one ToolExecution, stdout contains "hello"
# test: parse_and_execute with Block gate returns empty list, no subprocess called
# test: parse_and_execute with Confirm gate emits ConfirmationRequiredEvent

# VerificationGateway tests:
# test: verify(result with exit_code=0, target="example.com", command=["nmap","example.com"])
#       returns status=Passed
# test: verify(result with exit_code=1) returns status=FailedError
# test: verify(result with target="example.com", command=["nmap","other.com"])
#       returns status=FailedScope
# test: verify(result with target="sub.example.com", command=["nmap","example.com"])
#       returns status=Passed (subdomain match)

# FindingsEngine tests:
# test: extract_from_llm("FINDING: XSS | SEVERITY: high | stored xss found") returns 1 Finding
# test: extract_from_llm("no findings here") returns empty list
# test: extract_from_tool(verified_passed_result) returns Finding with evidence
# test: extract_from_tool(verified_failed_result) returns empty list

# LLMGateway tests:
# test: classify() with mocked provider returns parsed string
# test: count_tokens("hello world") returns approximately 3
```

---

### Acceptance Criteria

- [ ] `from redforge.execution import ToolRegistry, ToolOrchestrator, VerificationGateway, FindingsEngine, LLMGateway` imports cleanly
- [ ] `ToolRegistry.discover()` runs without error; `is_available("echo")` returns True
- [ ] `ToolOrchestrator.parse_and_execute("TOOL: echo\nCOMMAND: echo hello", session)` executes `echo hello` when gate allows
- [ ] `VerificationGateway.verify()` passes for `nmap sub.example.com` when `session.target = "example.com"`
- [ ] `FindingsEngine.extract_from_llm("FINDING: SQLi | SEVERITY: high | injectable param found")` returns one `Finding` with severity=High
- [ ] `import langgraph` in the venv raises `ImportError` (removed from dependencies)
- [ ] `python -m pytest tests/` passes in full
- [ ] `git tag v2.0.0-phase-5`

---

## Phase 6 — Surfaces: Terminal + REST API + SDK

**Git tag**: `v2.0.0-phase-6`

### Objective

Create the `surfaces/` package. Formalize the terminal surface (currently implicit). Create the REST API surface using FastAPI (the dependency already exists as an optional in `pyproject.toml`). Create a Python SDK surface. All three surfaces use only the `RedForgeKernel` public interface and EventBus subscriptions. Zero business logic in surfaces.

---

### Files to Create

```
src/redforge/surfaces/__init__.py
src/redforge/surfaces/terminal/__init__.py
src/redforge/surfaces/terminal/renderer.py
src/redforge/surfaces/api/__init__.py
src/redforge/surfaces/api/app.py
src/redforge/surfaces/api/routes.py
src/redforge/surfaces/api/sse.py
src/redforge/surfaces/sdk/__init__.py
src/redforge/surfaces/sdk/client.py
```

**`surfaces/terminal/renderer.py`**:
```python
class TerminalRenderer:
    """Subscribes to EventBus; renders events to stdout.
    All current print/stream logic from any existing CLI code moves here."""
    
    def __init__(self, kernel: RedForgeKernel, use_color: bool = True): ...
    def attach(self) -> None:
        """Subscribe to all relevant events."""
    def detach(self) -> None:
        """Unsubscribe all handlers."""
    
    # Internal handlers:
    async def _on_token(self, event: AssistantTokenEvent) -> None  # prints char
    async def _on_tool_start(self, event: ToolStartEvent) -> None  # prints tool name
    async def _on_tool_end(self, event: ToolEndEvent) -> None      # prints result summary
    async def _on_finding(self, event: FindingEvent) -> None       # prints finding box
    async def _on_error(self, event: ErrorEvent) -> None           # prints error
    async def _on_confirm(self, event: ConfirmationRequiredEvent) -> None  # prompts user
```

**`surfaces/api/app.py`**:
```python
def create_app(kernel: RedForgeKernel) -> FastAPI:
    """Factory function. Returns configured FastAPI app."""
```

**`surfaces/api/routes.py`**:
```python
# POST   /sessions              → kernel.create_session()
# GET    /sessions              → kernel.list_sessions()
# GET    /sessions/{id}         → kernel.load_session()
# DELETE /sessions/{id}         → kernel.delete_session()
# POST   /sessions/{id}/chat    → kernel.run(); returns SSE stream
# GET    /sessions/{id}/findings → findings_store.list(session_id)
# POST   /sessions/{id}/confirm → kernel.confirm()
# GET    /sessions/{id}/report  → report_store.generate() → streaming file
```

**`surfaces/api/sse.py`**:
```python
async def session_event_stream(kernel: RedForgeKernel,
                                session_id: str,
                                user_input: str) -> AsyncIterator[str]:
    """Converts EventBus events to SSE (Server-Sent Events) format.
    Each event: 'data: {json}\n\n'"""
```

**`surfaces/sdk/client.py`**:
```python
class RedForgeClient:
    """Async Python SDK. Wraps kernel directly (same-process) or via HTTP."""
    
    def __init__(self, kernel: RedForgeKernel | None = None,
                 base_url: str | None = None): ...
    
    async def create_session(self, mode: str, target: str | None = None,
                              autonomy: str = "manual",
                              name: str = "") -> Session: ...
    
    async def chat(self, session_id: str,
                   message: str) -> AsyncIterator[KernelEvent]: ...
    
    async def get_findings(self, session_id: str) -> list[Finding]: ...
    
    async def get_report(self, session_id: str,
                          format: str = "markdown") -> str: ...
    
    async def confirm(self, session_id: str) -> None: ...
```

---

### Files to Modify

**`pyproject.toml`**:
```toml
[project.optional-dependencies]
web = ["fastapi>=0.109.0", "uvicorn>=0.27.0", "sse-starlette>=1.6.0"]
sdk = []   # no extra deps; sdk uses kernel directly
```

**`config.yaml`** — Add API config (already present but now formally owned by surfaces):
```yaml
api:
  host: 127.0.0.1
  port: 5000
  auth_required: false   # for local single-user
  debug: false
```

---

### Files to Remove

None this phase.

---

### Interfaces

**SSE event format** (for `POST /sessions/{id}/chat`):
```
data: {"event_type": "assistant_token", "token": "Hello"}

data: {"event_type": "tool_start", "tool_name": "nmap", "command": ["nmap", "-sV", "x.com"]}

data: {"event_type": "finding", "finding": {"title": "...", "severity": "high"}}

data: {"event_type": "run_end", "status": "success"}
```

**SDK usage pattern**:
```python
client = RedForgeClient(kernel=my_kernel)
session = await client.create_session(mode="bugbounty", target="example.com")

async for event in client.chat(session.id, "run a port scan"):
    if isinstance(event, AssistantTokenEvent):
        print(event.token, end="", flush=True)
    elif isinstance(event, FindingEvent):
        print(f"\n[FINDING] {event.finding.title}")
```

---

### Tests

**New tests** (`tests/unit/test_surfaces.py`):
```python
# TerminalRenderer tests (with mocked kernel):
# test: attach() subscribes to EventBus; detach() unsubscribes
# test: _on_token handler prints token to stdout (capture with capsys)
# test: _on_finding handler prints finding title

# API tests (using FastAPI TestClient):
# test: POST /sessions returns 201 with session JSON
# test: GET /sessions returns list
# test: GET /sessions/{nonexistent-id} returns 404
# test: POST /sessions/{id}/chat with mocked kernel returns SSE stream
# test: SSE stream contains "run_end" event as final message
# test: GET /sessions/{id}/findings returns list (may be empty)
# test: POST /sessions/{id}/confirm returns 200

# SDK tests:
# test: client.create_session() returns Session object
# test: client.chat() async iterator yields KernelEvent objects
# test: client.get_findings() returns list
```

---

### Acceptance Criteria

- [ ] `from redforge.surfaces.terminal import TerminalRenderer` imports cleanly
- [ ] `from redforge.surfaces.api import create_app` imports cleanly (requires `fastapi` installed)
- [ ] `from redforge.surfaces.sdk import RedForgeClient` imports cleanly
- [ ] `POST /sessions` returns HTTP 201 with valid session JSON
- [ ] `POST /sessions/{id}/chat` returns `Content-Type: text/event-stream`
- [ ] SSE stream last event contains `"event_type": "run_end"`
- [ ] `RedForgeClient.create_session()` returns a `Session` with correct mode
- [ ] `TerminalRenderer` prints assistant tokens to stdout without exceptions
- [ ] No surface module imports from `intelligence/`, `execution/`, or `persistence/`
- [ ] All pre-existing tests pass
- [ ] `git tag v2.0.0-phase-6`

---

## Phase 7 — Hardening: Shim Removal + CI Enforcement

**Git tag**: `v2.0.0-phase-7`

### Objective

Delete all compatibility shims. Remove every piece of dead code that was left in place during the migration. Add import-linter enforcement to CI so the dependency rules from `04_DEPENDENCY_MAP.md` are enforced automatically. Update `pyproject.toml` description to match the new identity. Final state: a clean, shim-free codebase.

---

### Files to Create

```
.github/workflows/architecture-check.yml
.importlinter
tests/test_architecture.py
```

**`.importlinter`**:
```ini
[importlinter]
root_package = redforge

[importlinter:contract:contracts-are-leaf]
name = Contracts must not import from redforge
type = forbidden
source_modules = redforge.contracts
forbidden_modules = redforge.kernel, redforge.intelligence, redforge.execution, redforge.persistence, redforge.infrastructure, redforge.surfaces

[importlinter:contract:no-upward-deps]
name = No upward dependencies
type = layers
layers =
    redforge.surfaces
    redforge.kernel
    redforge.intelligence
    redforge.execution
    redforge.persistence
    redforge.infrastructure

[importlinter:contract:no-execution-to-kernel]
name = Execution cannot import kernel
type = forbidden
source_modules = redforge.execution
forbidden_modules = redforge.kernel

[importlinter:contract:no-intelligence-to-kernel]
name = Intelligence cannot import kernel
type = forbidden
source_modules = redforge.intelligence
forbidden_modules = redforge.kernel
```

**`.github/workflows/architecture-check.yml`**:
```yaml
name: Architecture
on: [push, pull_request]
jobs:
  import-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev]" && pip install import-linter
      - run: lint-imports
```

**`tests/test_architecture.py`**:
```python
# Runs import-linter programmatically as a pytest test
# Fails if any contract is violated
# This catches architecture regressions in the same test run as unit tests
```

---

### Files to Remove

**Shim files** (all logic already moved to new packages):
```
src/redforge/core/agent.py              → replaced by kernel/kernel.py
src/redforge/core/pipeline.py           → replaced by kernel/turn_orchestrator.py
src/redforge/core/factory.py            → replaced by kernel/kernel.py constructor
src/redforge/core/intent.py             → replaced by intelligence/intent_engine.py
src/redforge/core/planner.py            → replaced by intelligence/prompt_builder.py + planner_engine.py
src/redforge/core/safety.py             → replaced by kernel/security_gate.py
src/redforge/core/verifier.py           → replaced by execution/verification_gateway.py
src/redforge/core/skill_loader.py       → replaced by intelligence/skill_engine.py
src/redforge/core/autonomy_controller.py → dead, logic in security_gate.py
src/redforge/core/loop_detector.py      → dead, logic in turn_orchestrator.py
src/redforge/core/state.py              → replaced by contracts/session.py
src/redforge/memory/manager.py          → replaced by intelligence/memory_engine.py
src/redforge/memory/context_budget.py   → absorbed into memory_engine.py
src/redforge/memory/vector_store.py     → replaced by persistence/memory_store.py
src/redforge/tools/executor.py          → replaced by execution/tool_orchestrator.py
src/redforge/tools/manager.py           → replaced by execution/tool_orchestrator.py
src/redforge/tools/registry.py          → replaced by execution/tool_registry.py
src/redforge/tools/runner.py            → replaced by execution/tool_runner.py
src/redforge/tools/installer.py         → replaced by execution/tool_installer.py
src/redforge/tools/parser.py            → replaced by execution/tool_parser.py
src/redforge/tools/schemas/             → move to execution/schemas/ or inline in tool_registry
src/redforge/findings/engine.py         → replaced by execution/findings_engine.py
src/redforge/reports/engine.py          → replaced by persistence/report_store.py
src/redforge/modes/mode_implementations.py → replaced by modes/registry.py
```

**Directories to remove** (if empty after above):
```
src/redforge/core/          (if all files removed)
src/redforge/findings/      (if all files removed)
src/redforge/tools/         (if all files removed)
```

**Modes directory** — keep `modes/registry.py`. Remove `modes/mode_implementations.py`.

---

### Files to Modify

**`pyproject.toml`**:
```toml
description = "RedForge — AI Cybersecurity Operating System"
keywords = ["pentesting", "security", "ai-agent", "bugbounty", "ctf",
            "cybersecurity", "red-team", "vulnerability", "ai-os"]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "black>=24.1.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    "import-linter>=2.0",   # ADD
]
```

**`src/redforge/__init__.py`**:
```python
"""RedForge — AI Cybersecurity Operating System"""
from redforge.kernel.kernel import RedForgeKernel

__version__ = "2.0.0"
__all__ = ["RedForgeKernel"]
```

**`README.md`** — Update to reflect new architecture, new entry point, new directory structure.

---

### Tests

**Update all tests** that imported from now-deleted shim modules:
- `tests/unit/test_intent_engine.py` → import from `redforge.intelligence.intent_engine`
- `tests/unit/test_session_manager.py` → import from `redforge.kernel.session_service`
- `tests/unit/test_tool_executor.py` → import from `redforge.execution.tool_orchestrator`
- `tests/unit/test_verifier.py` → import from `redforge.execution.verification_gateway`
- `tests/unit/test_skill_loader.py` → import from `redforge.intelligence.skill_engine`
- `tests/unit/test_memory_manager.py` → import from `redforge.intelligence.memory_engine`
- `tests/unit/test_report_engine.py` → import from `redforge.persistence.report_store`
- `tests/integration/test_full_session.py` → import from `redforge.kernel.kernel`

**`tests/test_architecture.py`** (new):
```python
# test: lint-imports passes with no contract violations
# test: contracts/* have no redforge imports
# test: execution/* have no kernel imports
# test: intelligence/* have no kernel imports
# test: surfaces/* have no execution imports
```

---

### Acceptance Criteria

- [ ] `from redforge.core.agent import RedForgeAgent` raises `ImportError` (file removed)
- [ ] `from redforge.core.pipeline import Pipeline` raises `ImportError` (file removed)
- [ ] `from redforge.kernel import RedForgeKernel` works as the sole entry point
- [ ] `lint-imports` exits with code 0 (all contracts satisfied)
- [ ] `python -m pytest tests/` passes in full — no tests import deleted shims
- [ ] `python -c "import redforge; print(redforge.__version__)"` prints `2.0.0`
- [ ] `git diff --stat v2.0.0-phase-6 v2.0.0-phase-7` shows only deletions and test updates (no new logic)
- [ ] `git tag v2.0.0-phase-7`

---

## Phase 16 — Unified API Gateway

**Git tag**: `v2.0.0-phase-16`

### Objective

Build a production-ready API Gateway that exposes every RedForge capability through REST APIs and WebSockets. The API Gateway will become the ONLY public interface used by external clients (CLI, Dashboard, Plugins, Mobile/Desktop apps, MCP clients). No client should directly access internal modules.

---

### Files Created

```
src/redforge/api/
  __init__.py
  app.py
  server.py
  config.py
  middleware.py
  dependencies.py
  schemas.py
  response.py
  exceptions.py
  auth.py
  security.py
  rate_limit.py
  websocket.py
  health.py
  metrics.py
  routes/
    chat.py
    conversation.py
    workflow.py
    planner.py
    reasoning.py
    execution.py
    report.py
    memory.py
    sessions.py
    plugins.py
    mcp.py
    system.py
    health.py
```

---

### Key Features Implemented

* **REST APIs**: Full CRUD for sessions, non-streaming chat, workflows, planner triggers, reasoning engines, execution processes, reports, memory querying, plugin installation, MCP tool/resource discovery, and system status metadata.
* **WebSocket Endpoints**: Seven real-time bidirectional sockets (`/ws/chat`, `/ws/workflow`, `/ws/execution`, `/ws/events`, `/ws/reasoning`, and `/ws/report`) featuring clean connection pooling and client events.
* **Middlewares**: Full request/response pipeline handling CORS, security headers, request timing, structured logging, rate limiting (token-bucket), payload size guards, and authentication.
* **Authentication**: JWT token signing/verification (HMAC-SHA256), API key management (creation, listing, revocation), and RBAC role scope verification.
* **Health & Observability**: Active endpoints for `/health`, `/live`, `/ready`, `/version`, and `/metrics`.
* **Standard Envelope**: Envelope wrapping all success and error responses with timing metrics, request IDs, and API versions.

---

### Acceptance Criteria

- [ ] All 221 unit and integration tests pass cleanly (`pytest`)
- [ ] No double-accept ASGI socket exceptions occur during event subscriptions
- [ ] OpenAPI schema `/openapi.json` compiles successfully without unresolved forward references
- [ ] API is fully isolated from direct internal module access
- [ ] Git tag `v2.0.0-phase-16` is applied

---

## Phase 17 — React Dashboard

**Git tag**: `v2.0.0-phase-17`

### Objective

Build a modern, responsive web dashboard for RedForge that communicates exclusively with the API Gateway. Do NOT access internal Python modules directly.

---

### Files Created

```
dashboard/
  tsconfig.json
  vite.config.ts
  index.html
  src/
    main.tsx
    App.tsx
    index.css
    types/
      index.ts
    contexts/
      SettingsContext.tsx
      SessionContext.tsx
    services/
      api.ts
      api.test.ts
    layouts/
      DashboardLayout.tsx
    pages/
      Overview.tsx
      Chat.tsx
      Workflows.tsx
      Sessions.tsx
      Reports.tsx
      Evidence.tsx
      Memory.tsx
      Plugins.tsx
      Settings.tsx
```

---

### Key Features Implemented

* **Overview & Metrics**: Dashboard summary displaying active target specs, workflow progress states, vulnerability breakdown charts, and telemetry.
* **WebSocket Streaming AI Chat**: Token-by-token message streaming chatbot interface using `/ws/chat`.
* **Workflow Template Launcher**: Run templates and monitor stages dynamically using `/ws/workflow`.
* **Tool Scanner Terminal**: Run specific tools and stream live stdout/stderr lines in a custom console using `/ws/execution`.
* **Report Preview & Export**: Compile markdown, html, json, and pdf formats and trigger local downloads.
* **Settings & Auth**: Save custom gateway base URLs, store JWT tokens or API key authentication scopes, and swap Light/Dark mode themes.

### Acceptance Criteria

- [ ] All Vitest unit tests pass cleanly (`npm test`)
- [ ] UI is responsive and styled using Tailwind CSS layers
- [ ] Dashboard communicates only with REST APIs and WebSockets (no Python module imports)
- [ ] Git tag `v2.0.0-phase-17` is applied

---

## Phase 18 — Distributed Execution Platform

**Git tag**: `v2.0.0-phase-18`

### Objective

Transform RedForge from a single-process application into a distributed execution platform capable of running security workflows across multiple workers and machines.

---

### Files Created

```
src/redforge/distributed/
  __init__.py
  contracts.py
  manager.py
  scheduler.py
  dispatcher.py
  queue.py
  worker.py
  heartbeat.py
  registry.py
  autoscaler.py
  lease.py
  coordinator.py
  retry.py
  load_balancer.py
  exceptions.py
```

---

### Key Features Implemented

* **Priority Queue & Backends**: Unified queues supporting InMemory fallbacks, Redis priority ZSets, and RabbitMQ.
* **Resilient Dependency Scheduler**: Evaluates task dependency graphs, schedules ready tasks, and handles failure cascades.
* **Autoscaling Workers Pool**: Regulates local worker node pool sizes dynamically based on system demands.
* **Worker Leases & Retries**: Tracks active leases, handles heartbeat check failures, and reschedules with exponential backoffs.
* **Load Balancer**: Implements Round Robin, Least Loaded, Capability routing, and Weighted algorithms.

---

### Acceptance Criteria

- [ ] All 8 unit tests pass cleanly (`pytest tests/unit/test_distributed.py`)
- [ ] Platform supports Redis, RabbitMQ, and In-Memory Priority Queues
- [ ] Multi-worker execution resolves task graphs and recovers on worker failure
- [ ] Git tag `v2.0.0-phase-18` is applied

---

## Phase 19 — Observability & Monitoring Platform

**Git tag**: `v2.0.0-phase-19`

### Objective

Build a complete observability platform for RedForge that provides metrics, tracing, logging, auditing, and health monitoring across every subsystem.

---

### Files Created

```
src/redforge/observability/
  __init__.py
  contracts.py
  manager.py
  metrics.py
  logger.py
  audit.py
  tracing.py
  health.py
  events.py
  profiler.py
  alerts.py
  dashboard.py
  exceptions.py
```

---

### Key Features Implemented

* **Context JSON Logging**: JSON logger utilizing python `contextvars` to automatically bind trace and process contexts.
* **Prometheus exports**: Tracks counters, gauges, and histograms; exports scrape responses for Grafana integration.
* **Distributed Tracing Spans**: Context-aware parent-child span trace maps tracing Conversation down to Reporting.
* **Immutable Cryptographic Audit**: Cryptographically chained SHA-256 signatures log event hashes, verifying log integrity.
* **Host Resource & Profiler checks**: CPU/memory RSS profiling and alert handlers for CPU and memory usage diagnostics.
* **Grafana Dashboard definitions**: Auto-generates Grafana timeseries and stats JSON layouts.

---

### Acceptance Criteria

- [ ] All 8 unit tests pass cleanly (`pytest tests/unit/test_observability.py`)
- [ ] Platform exports standard Prometheus `/metrics` logs
- [ ] Audit log verify_chain detects tampering
- [ ] Git tag `v2.0.0-phase-19` is applied

---

## Phase Summary Table

| Phase | Name | Layers Touched | New Files | Modified | Deleted | Risk |
|---|---|---|---|---|---|---|
| 0 | Contracts + Dead Code | Contracts only | 3 | 6 | 8 | Low |
| 1 | Session Model | Config, Core, Memory | 1 | 7 | 0 | Medium |
| 2 | Kernel | New kernel/ package | 6 | 4 | 0 | Medium |
| 3 | Persistence | New persistence/ package | 6 | 4 | 0 | Low |
| 4 | Intelligence | New intelligence/, infrastructure/ | 7 | 5 | 0 | Medium |
| 5 | Execution | New execution/ package | 9 | 6 | 0 | Medium |
| 6 | Surfaces | New surfaces/ package | 8 | 2 | 0 | Low |
| 7 | Hardening | All (deletions only) | 3 | 9 | 26 | High |
| 16 | Unified API Gateway | API Gateway REST/WS | 28 | 6 | 0 | Low |
| 17 | React Dashboard | Frontend Web UI | 22 | 4 | 0 | Low |
| 18 | Distributed Execution | Distributed package | 15 | 4 | 0 | Low |
| 19 | Observability | Observability package | 12 | 4 | 0 | Low |

**Total new modules**: 120  
**Total deleted files**: 26 (all shims or dead code)  
**No-return point**: Phase 7 (shim removal). All phases before it are reversible.

---

## Parallel Work Opportunities

Phases 4 and 5 can be developed in parallel by separate engineers after Phase 3 completes:
- **Engineer A**: Phase 4 — Intelligence layer (`intelligence/`, `infrastructure/embedding_provider.py`)
- **Engineer B**: Phase 5 — Execution layer (`execution/`)

Both layers integrate into `kernel/turn_orchestrator.py` which is updated by whichever engineer finishes first.

---

## Risk Register

| Risk | Phase | Mitigation |
|---|---|---|
| `SessionState` alias breaks existing tests | 0 | Keep `SessionState = Session` alias in contracts/session.py |
| Memory isolation change wipes existing test data | 1 | Tests use `tmp_path`; no real data affected |
| LLM-based intent slower than keyword parser | 4 | `use_llm_intent: false` feature flag in config |
| `sentence-transformers` increases startup time | 4 | Lazy load on first embed call; optional dependency |
| Shim removal breaks undiscovered import paths | 7 | Run full test suite before deletion; check with `grep -r` |
| `langgraph` removal breaks something | 5 | Confirmed: zero active imports of `langgraph` in codebase |
| API surface introduces security vulnerabilities | 6 | `auth_required: true` by default; local-only bind by default |
