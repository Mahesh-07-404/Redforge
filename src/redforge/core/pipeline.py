from typing import Dict, Any
from ..session.manager import SessionManager
from ..memory.manager import MemoryManager
from ..skills.loader import DynamicSkillLoader
from ..intent.engine import IntentEngine
from ..tools.executor import ToolExecutor
from ..verifier.verifier import Verifier
from ..report.engine import ReportEngine

class Pipeline:
    def __init__(self, session_manager: SessionManager, memory_manager: MemoryManager,
                 skill_loader: DynamicSkillLoader, intent_engine: IntentEngine,
                 tool_executor: ToolExecutor, verifier: Verifier, report_engine: ReportEngine):
        self.session_manager = session_manager
        self.memory_manager = memory_manager
        self.skill_loader = skill_loader
        self.intent_engine = intent_engine
        self.tool_executor = tool_executor
        self.verifier = verifier
        self.report_engine = report_engine

    def process_turn(self, raw_input: str, session_id: str) -> Dict[str, Any]:
        session = self.session_manager.load(session_id)
        if not session:
            raise ValueError("Invalid session")

        # 1. Parse intent
        intent = self.intent_engine.process(raw_input, session.mode, session_id, session.autonomy)
        
        # 2. Get skills
        skills = self.skill_loader.select_skills(intent.intent_type.value, session.mode, raw_input)
        skill_texts = [s.content for s in skills]

        # 3. Context Budget
        context_bundle = self.memory_manager.build_context(intent.intent_type.value, skill_texts)

        return {"intent": intent, "context": context_bundle}
