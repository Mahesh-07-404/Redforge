from datetime import datetime

from ..executor.contracts import TaskResult
from .contracts import Artifact
from .hashing import calculate_sha256
from .metadata import ArtifactMetadata


class ArtifactManager:
    @staticmethod
    def create_artifact(
        task_result: TaskResult,
        content_type: str,
        content: str,
        session_id: str,
        execution_id: str,
        tool: str,
        target: str,
        risk: str,
        platform: str,
    ) -> Artifact:
        content_hash = calculate_sha256(content)
        timestamp = datetime.now().isoformat()

        metadata = ArtifactMetadata(
            session_id=session_id,
            execution_id=execution_id,
            task_id=task_result.task_id,
            tool=tool,
            target=target,
            timestamp=timestamp,
            duration=task_result.duration,
            exit_code=task_result.exit_code,
            risk=risk,
            status=task_result.status.value,
            hash=content_hash,
            platform=platform,
        )

        artifact_id = f"{task_result.task_id}_{content_type}"
        return Artifact(
            id=artifact_id,
            name=f"{tool} {content_type}",
            content_type=content_type,
            content=content,
            metadata=metadata,
        )
