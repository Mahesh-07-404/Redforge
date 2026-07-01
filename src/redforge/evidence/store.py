import json
import os

from .contracts import EvidenceBundle
from .exceptions import StoreError


class EvidenceStore:
    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir

    def store_bundle(self, bundle: EvidenceBundle):
        session_dir = os.path.join(self.base_dir, "evidence", bundle.session_id)
        artifacts_dir = os.path.join(session_dir, "artifacts")

        try:
            os.makedirs(artifacts_dir, exist_ok=True)

            timeline_path = os.path.join(session_dir, "timeline.json")
            with open(timeline_path, "w", encoding="utf-8") as f:
                f.write(bundle.timeline.model_dump_json(indent=2))

            for ev in bundle.evidence_list:
                for art in ev.artifacts:
                    art_path = os.path.join(artifacts_dir, f"{art.id}.json")
                    with open(art_path, "w", encoding="utf-8") as f:
                        f.write(art.model_dump_json(indent=2))

            evidence_path = os.path.join(session_dir, "evidence.json")
            with open(evidence_path, "w", encoding="utf-8") as f:
                f.write(bundle.model_dump_json(indent=2))

        except Exception as e:
            raise StoreError(f"Failed to store evidence bundle: {str(e)}") from e

    def load_bundle(self, session_id: str) -> EvidenceBundle:
        session_dir = os.path.join(self.base_dir, "evidence", session_id)
        evidence_path = os.path.join(session_dir, "evidence.json")
        if not os.path.exists(evidence_path):
            raise StoreError(f"Evidence for session {session_id} not found.")

        try:
            with open(evidence_path, encoding="utf-8") as f:
                data = json.load(f)
            return EvidenceBundle(**data)
        except Exception as e:
            raise StoreError(f"Failed to load evidence bundle: {str(e)}") from e
