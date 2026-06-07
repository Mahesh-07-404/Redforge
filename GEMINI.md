# RedForge Project Instructions

## Engineering Standards
- **Autonomy Logic**: When routing tool calls in `langgraph_agent.py`, always use `.value` when comparing `ActionRisk` enum members to strings.
- **Partial Autonomy**: Ensure that both `safe` and `low` risk actions are allowed to execute automatically in Partial mode.
- **Agent Persona**: Maintain a dual-purpose identity. Be capable of both natural conversation and high-intensity, professional pentesting.
