from typing import Any


class WorldState:
    def __init__(self):
        self.hosts: set[str] = set()
        self.ports: set[int] = set()
        self.services: set[str] = set()
        self.findings: set[str] = set()
        self.cves: set[str] = set()
        self.urls: set[str] = set()
        self.technologies: set[str] = set()
        self.endpoints: set[str] = set()
        self.credentials: set[str] = set()
        self.evidence: set[str] = set()

    def update_from_entities(self, entities: list[Any]):
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
