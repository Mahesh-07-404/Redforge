from typing import Dict, Any
from .world_state import WorldState

class SelfEvaluator:
    @staticmethod
    def evaluate_progress(world_state: WorldState, goal_text: str) -> Dict[str, Any]:
        coverage = 0.0
        confidence = 0.5
        completed = False
        
        gt = goal_text.lower()
        if "recon" in gt:
            if world_state.hosts:
                coverage = 0.8
                confidence = 0.7
                completed = True
        elif "scan" in gt:
            if world_state.ports:
                coverage = 0.9
                confidence = 0.8
                completed = True
                
        return {
            "coverage": coverage,
            "confidence": confidence,
            "completed": completed
        }
