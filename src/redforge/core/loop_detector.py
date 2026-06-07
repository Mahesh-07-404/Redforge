"""Loop detection for agent to prevent infinite loops"""

import hashlib
import json
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque


@dataclass
class LoopDetectionResult:
    is_looping: bool
    loop_count: int
    state_hash: str
    message: str
    should_stop: bool
    suggestions: List[str] = field(default_factory=list)


class LoopDetector:
    """Detects when agent is stuck in a loop"""
    
    def __init__(
        self,
        max_iterations: int = 50,
        loop_threshold: int = 10,
        state_history_size: int = 5,
        stagnation_threshold: int = 3
    ):
        self.max_iterations = max_iterations
        self.loop_threshold = loop_threshold
        self.state_history_size = state_history_size
        self.stagnation_threshold = stagnation_threshold
        
        self._state_history: deque = deque(maxlen=state_history_size)
        self._action_history: deque = deque(maxlen=50)
        self._iteration = 0
        self._last_progress_time: datetime = datetime.now()
        self._progress_markers: deque = deque(maxlen=10)
    
    def reset(self) -> None:
        """Reset the loop detector"""
        self._state_history.clear()
        self._action_history.clear()
        self._iteration = 0
        self._last_progress_time = datetime.now()
        self._progress_markers.clear()
    
    def compute_state_hash(self, state: Dict[str, Any]) -> str:
        """Compute a hash of the current state"""
        relevant_keys = ["messages", "context", "tasks", "findings"]
        
        state_subset = {
            k: v for k, v in state.items()
            if k in relevant_keys and v
        }
        
        for key in relevant_keys:
            if key in state_subset and isinstance(state_subset[key], list):
                state_subset[key] = state_subset[key][-3:]
        
        state_str = json.dumps(state_subset, sort_keys=True, default=str)
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def compute_action_hash(self, action: str) -> str:
        """Compute a hash of an action"""
        return hashlib.md5(action.encode()).hexdigest()
    
    def record_state(self, state: Dict[str, Any]) -> None:
        """Record current state for loop detection"""
        state_hash = self.compute_state_hash(state)
        self._state_history.append({
            "hash": state_hash,
            "timestamp": datetime.now(),
            "iteration": self._iteration
        })
        self._iteration += 1
    
    def record_action(self, action: str) -> None:
        """Record an action for loop detection"""
        action_hash = self.compute_action_hash(action)
        self._action_history.append({
            "hash": action_hash,
            "action": action,
            "timestamp": datetime.now(),
            "iteration": self._iteration
        })
    
    def mark_progress(self, message: str) -> None:
        """Mark that progress was made"""
        self._last_progress_time = datetime.now()
        self._progress_markers.append({
            "message": message,
            "timestamp": datetime.now(),
            "iteration": self._iteration
        })
    
    def detect_loop(self, current_state: Optional[Dict[str, Any]] = None) -> LoopDetectionResult:
        """Detect if agent is in a loop"""
        suggestions = []
        is_looping = False
        loop_count = 0
        
        if self._iteration >= self.max_iterations:
            return LoopDetectionResult(
                is_looping=False,
                loop_count=0,
                state_hash="",
                message=f"Maximum iterations ({self.max_iterations}) reached",
                should_stop=True,
                suggestions=["Task completed or max iterations reached"]
            )
        
        if len(self._state_history) >= 2:
            recent_hashes = [s["hash"] for s in self._state_history]
            unique_hashes = set(recent_hashes)
            
            if len(unique_hashes) == 1 and len(recent_hashes) >= 3:
                is_looping = True
                loop_count = len(recent_hashes)
                suggestions.append("State hasn't changed - try a different approach")
                suggestions.append("Consider breaking down the task differently")
        
        if len(self._action_history) >= 3:
            recent_actions = [a["hash"] for a in list(self._action_history)[-10:]]
            unique_actions = set(recent_actions)
            
            if len(unique_actions) <= 2 and len(recent_actions) >= 5:
                is_looping = True
                suggestions.append("Same actions repeated - review approach")
                suggestions.append("Try a different tool or technique")
        
        time_since_progress = datetime.now() - self._last_progress_time
        if time_since_progress > timedelta(seconds=120):
            suggestions.append(f"No progress in {time_since_progress.seconds}s")
            suggestions.append("Consider asking user for guidance")
        
        state_hash = ""
        if current_state:
            state_hash = self.compute_state_hash(current_state)
        
        return LoopDetectionResult(
            is_looping=is_looping,
            loop_count=loop_count,
            state_hash=state_hash,
            message=self._generate_message(is_looping, loop_count, suggestions),
            should_stop=loop_count >= self.loop_threshold,
            suggestions=suggestions
        )
    
    def _generate_message(
        self,
        is_looping: bool,
        loop_count: int,
        suggestions: List[str]
    ) -> str:
        """Generate a human-readable message"""
        if not is_looping:
            return "No loop detected"
        
        msg = f"Loop detected (count: {loop_count})\n"
        if suggestions:
            msg += "Suggestions:\n"
            for s in suggestions:
                msg += f"  - {s}\n"
        
        return msg
    
    def get_status(self) -> Dict[str, Any]:
        """Get current loop detector status"""
        return {
            "iteration": self._iteration,
            "max_iterations": self.max_iterations,
            "loop_threshold": self.loop_threshold,
            "state_history_size": len(self._state_history),
            "action_history_size": len(self._action_history),
            "time_since_progress": (datetime.now() - self._last_progress_time).seconds
        }
