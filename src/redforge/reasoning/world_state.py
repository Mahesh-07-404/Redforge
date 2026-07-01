from typing import Set, List, Any

class WorldState:
    def __init__(self):
        self.hosts: Set[str] = set()
        self.ports: Set[int] = set()
        self.services: Set[str] = set()
        self.findings: Set[str] = set()
        self.cves: Set[str] = set()
        self.urls: Set[str] = set()
        self.technologies: Set[str] = set()
        self.endpoints: Set[str] = set()
        self.credentials: Set[str] = set()
        self.evidence: Set[str] = set()

    def update_from_entities(self, entities: List[Any]):
        for e in entities:
            val = e.value
            if e.entity_type == "Host":
                self.hosts.add(val)
            elif e.entity_type == "Port":
                try:
                    self.ports.add(int(val))
                except ValueError:
                    pass  # nosec B110 - port value is non-numeric; silently skip malformed port entity
            elif e.entity_type == "Service":
                self.services.add(val)
            elif e.entity_type == "Technology":
                self.technologies.add(val)
            elif e.entity_type == "Finding":
                self.findings.add(val)
            elif e.entity_type == "CVE":
                self.cves.add(val)
            elif e.entity_type == "URLResource":
                self.urls.add(val)
            elif e.entity_type == "Directory":
                self.endpoints.add(val)
