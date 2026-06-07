"""Main agent orchestration module"""

import asyncio
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from redforge.llm.base import LLMProvider, Message, ChatResponse, ProviderFactory
from redforge.core.config import Settings, get_settings


class AgentMode(Enum):
    GOAL_BASED = "goal"
    KNOWLEDGE_BASED = "knowledge"


class AutonomyLevel(Enum):
    MANUAL = "manual"
    PARTIAL = "partial"
    FULL = "full"


@dataclass
class AgentConfig:
    mode: AgentMode = AgentMode.GOAL_BASED
    autonomy_level: AutonomyLevel = AutonomyLevel.MANUAL
    max_iterations: int = 50
    max_time_seconds: int = 3600
    tools_enabled: bool = True
    skills_enabled: bool = True


@dataclass
class AgentState:
    iteration: int = 0
    total_tokens: int = 0
    messages: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    tools_used: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class Agent:
    """Main RedForge agent for autonomous pentesting"""
    
    def __init__(
        self,
        config: Optional[Settings] = None,
        llm_provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.config = config or get_settings()
        self._llm_provider = llm_provider or self.config.llm.provider
        self._model = model or self.config.llm.model
        self._api_key = api_key or self.config.llm.api_key
        self._base_url = base_url or self.config.llm.base_url
        
        self.llm = ProviderFactory.create(
            provider=self._llm_provider,
            model=self._model,
            api_key=self._api_key,
            base_url=self._base_url,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
        )
        
        self.agent_config = AgentConfig()
        self.state = AgentState()
        self._skills: List[str] = []
        self._workspace_context: Dict[str, Any] = {}
    
    @property
    def is_available(self) -> bool:
        """Check if LLM provider is available"""
        return self.llm.is_available()
    
    async def initialize(self, system_prompt: str = "") -> None:
        """Initialize the agent with system prompt"""
        default_prompt = """You are RedForge, an autonomous penetration testing assistant.
You help with bug bounty hunting, CTF challenges, learning, and pentesting tasks.
Always verify scope and authorization before any testing.
Default to safe, conservative actions. Ask for confirmation when uncertain."""
        
        self.state.messages = [
            Message(role="system", content=system_prompt or default_prompt)
        ]
    
    async def chat(
        self,
        user_input: str,
        mode: Optional[AgentMode] = None,
        tools: Optional[List[Dict]] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Send a message and get a response"""
        self.state.messages.append(Message(role="user", content=user_input))
        
        if mode:
            self.agent_config.mode = mode
        
        response_obj: Optional[ChatResponse] = None
        if self.config.llm.streaming and stream_callback:
            response_text = ""
            async for chunk in self.llm.chat_stream(
                messages=self.state.messages,
                tools=tools if self.agent_config.tools_enabled else None
            ):
                response_text += chunk
                stream_callback(chunk)
            response = response_text
        else:
            response_obj = await self.llm.chat(
                messages=self.state.messages,
                tools=tools if self.agent_config.tools_enabled else None
            )
            response = response_obj.content
        
        self.state.messages.append(Message(role="assistant", content=response))
        self.state.iteration += 1
        
        if response_obj and response_obj.usage:
            self.state.total_tokens += response_obj.usage.get("total_tokens", 0)
        else:
            self.state.total_tokens += max(1, len(response.split()))
        
        return response
    
    async def goal_based_execute(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict]] = None,
        on_thought: Optional[Callable[[str], None]] = None,
        on_action: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Execute a goal-based task with planning and verification"""
        self.agent_config.mode = AgentMode.GOAL_BASED
        
        if context:
            self._workspace_context.update(context)
        
        planning_prompt = f"""Planning phase for goal: {goal}

Context: {self._format_context()}
Previous findings: {self.state.findings}

Break down this goal into specific, actionable steps.
Consider:
1. What information do we need?
2. What tools should we use?
3. What are the verification steps?
4. What could go wrong?

Provide a numbered plan."""
        
        self.state.messages.append(Message(role="user", content=planning_prompt))
        if on_thought:
            on_thought("Planning...")
        
        plan_response = await self.llm.chat(messages=self.state.messages)
        plan_text = plan_response.content if hasattr(plan_response, "content") else str(plan_response)
        self.state.messages.append(Message(role="assistant", content=plan_text))
        
        execution_prompt = f"""Execute the plan above. For each step:
1. Describe what you're doing
2. Execute the action
3. Record the result
4. Verify success

Goal: {goal}
Tools available: {list(self._get_available_tools().keys()) if tools else 'none specified'}
"""
        self.state.messages.append(Message(role="user", content=execution_prompt))
        
        final_response = await self.llm.chat(
            messages=self.state.messages,
            tools=tools
        )
        
        return {
            "goal": goal,
            "plan": plan_text,
            "execution": final_response,
            "findings": self.state.findings,
            "iterations": self.state.iteration,
        }
    
    async def knowledge_based_query(
        self,
        query: str,
        knowledge_sources: Optional[List[str]] = None,
        retrieval_context: Optional[str] = None,
    ) -> str:
        """Query with knowledge retrieval augmentation"""
        self.agent_config.mode = AgentMode.KNOWLEDGE_BASED
        
        context_prompt = ""
        if retrieval_context:
            context_prompt = f"\n\nRelevant context from knowledge base:\n{retrieval_context}\n"
        
        if knowledge_sources:
            context_prompt += f"\nKnowledge sources: {', '.join(knowledge_sources)}\n"
        
        full_query = f"{context_prompt}\n\nQuery: {query}"
        self.state.messages.append(Message(role="user", content=full_query))
        
        response_obj = await self.llm.chat(messages=self.state.messages)
        response = response_obj.content if hasattr(response_obj, "content") else str(response_obj)
        self.state.messages.append(Message(role="assistant", content=response))

        return response
    
    def add_skill(self, skill_content: str) -> None:
        """Add a skill to the agent's context"""
        self._skills.append(skill_content)
    
    def set_workspace_context(self, context: Dict[str, Any]) -> None:
        """Set persistent workspace context"""
        self._workspace_context = context
    
    def get_workspace_context(self) -> Dict[str, Any]:
        """Get current workspace context"""
        return self._workspace_context.copy()
    
    def add_finding(self, finding: Dict[str, Any]) -> None:
        """Add a security finding"""
        self.state.findings.append({
            "finding": finding,
            "iteration": self.state.iteration,
        })
    
    def get_findings(self) -> List[Dict[str, Any]]:
        """Get all findings"""
        return self.state.findings.copy()
    
    def reset(self) -> None:
        """Reset agent state"""
        self.state = AgentState()
        self._skills = []
        self._workspace_context = {}
    
    def _format_context(self) -> str:
        """Format workspace context for prompts"""
        if not self._workspace_context:
            return "No context available"
        
        parts = []
        for key, value in self._workspace_context.items():
            if isinstance(value, list):
                parts.append(f"{key}: {', '.join(str(v) for v in value)}")
            else:
                parts.append(f"{key}: {value}")
        
        return "\n".join(parts)
    
    def _get_available_tools(self) -> Dict[str, str]:
        """Get available tools mapping"""
        return {
            "bash": "Execute shell commands",
            "python": "Run Python scripts",
            "nmap": "Network scanning",
            "sqlmap": "SQL injection testing",
            "ffuf": "Web fuzzing",
            "search": "Search workspace memory",
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "provider": self._llm_provider,
            "model": self._model,
            "mode": self.agent_config.mode.value,
            "autonomy": self.agent_config.autonomy_level.value,
            "iteration": self.state.iteration,
            "total_tokens": self.state.total_tokens,
            "messages": len(self.state.messages),
            "findings": len(self.state.findings),
            "tools_used": len(self.state.tools_used),
            "llm_available": self.is_available,
        }
