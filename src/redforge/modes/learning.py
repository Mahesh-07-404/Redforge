"""Learning Mode - Interactive security education"""

from typing import Dict, Any, List, Optional
from redforge.modes.base import BaseMode, ModeResult


class LearningMode(BaseMode):
    """Learning and education mode"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.topic: str = config.get("topic", "general") if config else "general"
        self.difficulty: str = config.get("difficulty", "beginner") if config else "beginner"
    
    async def execute(self, task: str, **kwargs) -> ModeResult:
        """Execute learning session"""
        topic = kwargs.get("topic", self.topic)
        difficulty = kwargs.get("difficulty", self.difficulty)
        action = kwargs.get("action", "explain")
        
        if action == "quiz":
            return ModeResult(
                success=True,
                message=f"Quiz generated for {topic}",
                data={"topic": topic, "difficulty": difficulty, "type": "quiz"}
            )
        elif action == "explain":
            return ModeResult(
                success=True,
                message=f"Explanation of {topic}",
                data={"topic": topic, "difficulty": difficulty, "type": "explanation"}
            )
        elif action == "practice":
            return ModeResult(
                success=True,
                message=f"Practice exercise for {topic}",
                data={"topic": topic, "difficulty": difficulty, "type": "exercise"}
            )
        
        return ModeResult(success=True, message="Learning session ready")
    
    def get_prompt(self) -> str:
        return """You are RedForge in Learning mode. Your goal is to teach security concepts effectively.

Teaching Approach:
- Start with fundamentals before advanced topics
- Use clear, jargon-free explanations
- Provide concrete examples
- Include hands-on exercises
- Test understanding with quizzes

Topics:
- Networking basics (TCP/IP, DNS, HTTP)
- Linux fundamentals
- Web security (OWASP Top 10)
- Cryptography basics
- Binary exploitation
- Mobile security
- Cloud security
- CTF writeups and techniques

Always:
- Ask about the user's current knowledge level
- Adapt explanations to the user's experience
- Encourage hands-on practice
- Provide resources for further learning"""
    
    def get_default_context(self) -> Dict[str, Any]:
        return {
            "mode": "learning",
            "topic": self.topic,
            "difficulty": self.difficulty,
        }
