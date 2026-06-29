# Changelog

All notable changes to RedForge will be documented in this file.

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
