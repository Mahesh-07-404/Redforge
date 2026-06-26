"""Findings parsing and management service for RedForge."""

import re
import uuid
from typing import List, Dict, Any, Optional

class FindingsService:
    """Service to parse and manage vulnerability findings discovered during execution."""

    def parse_findings(self, content: str) -> List[Dict[str, Any]]:
        """Parses findings lines formatted like 'FINDING: type | SEVERITY: level | description'."""
        findings = []
        for line in content.splitlines():
            line = line.strip()
            if line.upper().startswith("FINDING:"):
                parts = [p.strip() for p in line[8:].split("|")]
                if len(parts) >= 3:
                    finding_type = parts[0]
                    severity = parts[1].replace("SEVERITY:", "").strip().lower()
                    desc = parts[2]
                    findings.append({
                        "id": str(uuid.uuid4()),
                        "type": finding_type,
                        "severity": severity,
                        "title": f"Vulnerability Finding: {finding_type}",
                        "description": desc,
                        "evidence": None
                    })
                else:
                    findings.append({
                        "id": str(uuid.uuid4()),
                        "type": "finding",
                        "severity": "medium",
                        "title": "Vulnerability Finding",
                        "description": line[8:].strip(),
                        "evidence": None
                    })
        return findings
