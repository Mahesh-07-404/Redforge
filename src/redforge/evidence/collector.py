import uuid
from typing import List
from .contracts import EvidenceBundle, Evidence, Artifact
from .artifacts import ArtifactManager
from .timeline import TimelineGenerator
from ..executor.contracts import ExecutionResult
from ..tools import ToolRegistry

class EvidenceCollector:
    def __init__(self):
        self.registry = ToolRegistry()

    def collect(
        self,
        session_id: str,
        exec_result: ExecutionResult,
        target: str,
        platform: str
    ) -> EvidenceBundle:
        execution_id = str(uuid.uuid4())
        timeline = TimelineGenerator.generate_timeline(session_id, execution_id, exec_result)
        evidence_list: List[Evidence] = []
        
        for task_res in exec_result.task_results:
            artifacts: List[Artifact] = []
            tool_name = task_res.task_id
            
            try:
                tool_meta = self.registry.lookup_tool_by_name(tool_name)
                tool_binary = tool_meta.binary
                from ..policy.policy_rules import PolicyRules
                risk = PolicyRules.TOOL_RISK_MAP.get(tool_binary, "LOW")
            except Exception:
                tool_binary = tool_name
                risk = "LOW"
                
            if task_res.raw_output:
                raw_art = ArtifactManager.create_artifact(
                    task_result=task_res,
                    content_type="raw_output",
                    content=task_res.raw_output,
                    session_id=session_id,
                    execution_id=execution_id,
                    tool=tool_binary,
                    target=target,
                    risk=risk,
                    platform=platform
                )
                artifacts.append(raw_art)
                
            if task_res.structured_output:
                import json
                parsed_content = json.dumps(task_res.structured_output)
                parsed_art = ArtifactManager.create_artifact(
                    task_result=task_res,
                    content_type="parsed_output",
                    content=parsed_content,
                    session_id=session_id,
                    execution_id=execution_id,
                    tool=tool_binary,
                    target=target,
                    risk=risk,
                    platform=platform
                )
                artifacts.append(parsed_art)
                
            if task_res.error:
                err_art = ArtifactManager.create_artifact(
                    task_result=task_res,
                    content_type="logs",
                    content=task_res.error,
                    session_id=session_id,
                    execution_id=execution_id,
                    tool=tool_binary,
                    target=target,
                    risk=risk,
                    platform=platform
                )
                artifacts.append(err_art)
                
            evidence_obj = Evidence(
                id=f"evidence_{task_res.task_id}",
                task_id=task_res.task_id,
                status=task_res.status.value,
                duration=task_res.duration,
                exit_code=task_res.exit_code,
                artifacts=artifacts
            )
            evidence_list.append(evidence_obj)
            
        return EvidenceBundle(
            session_id=session_id,
            execution_id=execution_id,
            plan_goal=exec_result.plan_goal,
            timeline=timeline,
            evidence_list=evidence_list
        )
