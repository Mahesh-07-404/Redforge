# CORE SYSTEM: Session Awareness

Ensure strict alignment with the active session state and target immutability rules.

## Session Rules
- **Target Immutability**: The active target is stored in the session state and cannot be overwritten by any agent node. Maintain and verify target consistency at all times.
- **Session Continuity**: Restore chat history, active target, workspace context, and findings list across node steps and agent restarts.
- **Target Propagation**: Ensure all tool parameters, URLs, and commands are automatically bound to the active session target. Never substitute the target.
- **Workspace Context**: Bind all data storage, reports, and scan operations to the current workspace identifier.
