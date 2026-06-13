"""RedForge Planning Engine"""

from typing import Dict, Any, Optional
from redforge.llm.base import Message

class Planner:
    """Creates plans only without executing them"""

    @classmethod
    async def generate_plan(cls, goal: str, context: Dict[str, Any], llm: Any) -> str:
        """Generate a numbered step-by-step plan for a given goal"""
        context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
        
        sys_msg = Message(
            role="system",
            content="""You are a security planning system. Your task is ONLY to write plans. 
Do NOT execute commands, do NOT simulate outputs, and do NOT output results.
Generate a numbered plan following this exact structure:
Step 1: <Description of action>
Step 2: <Description of action>
...
Be precise and clean."""
        )
        
        user_msg = Message(
            role="user",
            content=f"Goal: {goal}\n\nContext:\n{context_str}\n\nGenerate the plan now:"
        )
        
        try:
            response = await llm.chat(messages=[sys_msg, user_msg])
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            return f"Step 1: Execute goal '{goal}'\nStep 2: Verify results"
