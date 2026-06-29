from .contracts import EvidenceBundle

class EvidenceSerializer:
    @staticmethod
    def serialize_to_json(bundle: EvidenceBundle) -> str:
        return bundle.model_dump_json(indent=2)

    @staticmethod
    def serialize_to_markdown(bundle: EvidenceBundle) -> str:
        md = f"# Evidence Bundle: {bundle.plan_goal}\n\n"
        md += f"**Session ID:** {bundle.session_id}\n"
        md += f"**Execution ID:** {bundle.execution_id}\n\n"
        
        md += "## Timeline\n"
        for event in bundle.timeline.events:
            md += f"- *[{event.timestamp}]* **{event.event}** - {event.description}\n"
            
        md += "\n## Evidence Items\n"
        for ev in bundle.evidence_list:
            md += f"### Task: {ev.task_id}\n"
            md += f"- **Status:** {ev.status}\n"
            md += f"- **Duration:** {ev.duration:.2f} seconds\n"
            md += f"- **Exit Code:** {ev.exit_code}\n\n"
            
            if ev.artifacts:
                md += "#### Artifacts:\n"
                for art in ev.artifacts:
                    md += f"##### {art.name} ({art.content_type})\n"
                    md += f"- **Hash (SHA256):** `{art.metadata.hash}`\n"
                    md += "```\n"
                    md += art.content
                    md += "\n```\n\n"
                    
        return md

    @staticmethod
    def serialize_to_text(bundle: EvidenceBundle) -> str:
        text = f"Evidence Bundle: {bundle.plan_goal}\n"
        text += f"Session ID: {bundle.session_id}\n"
        text += f"Execution ID: {bundle.execution_id}\n\n"
        
        text += "Timeline:\n"
        for event in bundle.timeline.events:
            text += f"[{event.timestamp}] {event.event}: {event.description}\n"
            
        text += "\nEvidence Items:\n"
        for ev in bundle.evidence_list:
            text += f"Task: {ev.task_id}\n"
            text += f"Status: {ev.status}\n"
            text += f"Duration: {ev.duration:.2f}s\n"
            text += f"Exit Code: {ev.exit_code}\n"
            for art in ev.artifacts:
                text += f"  Artifact: {art.name} ({art.content_type}) - Hash: {art.metadata.hash}\n"
                text += f"  Content:\n{art.content}\n"
                
        return text
