from typing import List
from .contracts import Finding

class Deduplicator:
    @staticmethod
    def deduplicate(findings: List[Finding]) -> List[Finding]:
        seen_keys = set()
        deduped = []
        for f in findings:
            key = (f.title.lower(), f.cve or "")
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(f)
        return deduped
