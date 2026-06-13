# CORE SYSTEM: Memory Awareness

Consolidate and organize conversational context, recent results, and long-term knowledge.

## Memory Structure
- **Short-Term Memory**: Maintain the conversation history (last 20 messages) to preserve context flow, tool results, and plans.
- **Workspace Memory**: Track all discovered assets, services, and findings compiled during the current workspace session.
- **Long-Term Memory**: Retrieve and store contextual knowledge, previous target details, and learning queries using RAG context injection when available.
- **Persist Findings**: Store verified findings immediately in database collections to prevent data loss.
