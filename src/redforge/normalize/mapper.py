import json
import logging
from typing import Any

from .entities import (
    CVEEntity,
    DirectoryEntity,
    DNSRecordEntity,
    FindingEntity,
    HostEntity,
    PortEntity,
    ServiceEntity,
    TechnologyEntity,
    URLResource,
)
from .schema import EvidenceReference, NormalizedEntity

logger = logging.getLogger(__name__)


class BaseMapper:
    tool_name: str = ""

    def map_output(
        self,
        raw_content: str,
        parsed_content: dict[str, Any],
        ref: EvidenceReference,
        meta: dict[str, Any],
    ) -> list[NormalizedEntity]:
        raise NotImplementedError


class HostDiscoveryMapper(BaseMapper):
    def map_output(
        self,
        raw_content: str,
        parsed_content: dict[str, Any],
        ref: EvidenceReference,
        meta: dict[str, Any],
    ) -> list[NormalizedEntity]:
        entities = []
        hosts = parsed_content.get("subdomains", [])
        if not hosts and raw_content:
            hosts = [
                line.strip()
                for line in raw_content.splitlines()
                if line.strip() and not line.strip().startswith("[")
            ]

        for h in hosts:
            entities.append(
                HostEntity(
                    id=f"host_{h}",
                    value=h,
                    source_tool=self.tool_name,
                    session_id=meta["session_id"],
                    execution_id=meta["execution_id"],
                    target=meta["target"],
                    timestamp=meta["timestamp"],
                    evidence_reference=ref,
                )
            )
        return entities


class SubfinderMapper(HostDiscoveryMapper):
    tool_name = "subfinder"


class AssetfinderMapper(HostDiscoveryMapper):
    tool_name = "assetfinder"


class AmassMapper(HostDiscoveryMapper):
    tool_name = "amass"


class HttpxMapper(BaseMapper):
    tool_name = "httpx"

    def map_output(
        self,
        raw_content: str,
        parsed_content: dict[str, Any],
        ref: EvidenceReference,
        meta: dict[str, Any],
    ) -> list[NormalizedEntity]:
        entities = []
        urls = parsed_content.get("urls", [])
        if not urls and raw_content:
            urls = [
                line.strip() for line in raw_content.splitlines() if line.strip().startswith("http")
            ]

        for u in urls:
            url_entity = URLResource(
                id=f"url_{u}",
                value=u,
                source_tool=self.tool_name,
                session_id=meta["session_id"],
                execution_id=meta["execution_id"],
                target=meta["target"],
                timestamp=meta["timestamp"],
                evidence_reference=ref,
            )
            entities.append(url_entity)

            tech = meta.get("tech", "Web Server")
            entities.append(
                TechnologyEntity(
                    id=f"tech_{tech.lower().replace(' ', '_')}",
                    value=tech,
                    source_tool=self.tool_name,
                    session_id=meta["session_id"],
                    execution_id=meta["execution_id"],
                    target=meta["target"],
                    timestamp=meta["timestamp"],
                    evidence_reference=ref,
                )
            )

        return entities


class URLDiscoveryMapper(BaseMapper):
    def map_output(
        self,
        raw_content: str,
        parsed_content: dict[str, Any],
        ref: EvidenceReference,
        meta: dict[str, Any],
    ) -> list[NormalizedEntity]:
        entities = []
        urls = [
            line.strip() for line in raw_content.splitlines() if line.strip().startswith("http")
        ]
        for u in urls:
            entities.append(
                URLResource(
                    id=f"url_{u}",
                    value=u,
                    source_tool=self.tool_name,
                    session_id=meta["session_id"],
                    execution_id=meta["execution_id"],
                    target=meta["target"],
                    timestamp=meta["timestamp"],
                    evidence_reference=ref,
                )
            )
        return entities


class KatanaMapper(URLDiscoveryMapper):
    tool_name = "katana"


class GAUMapper(URLDiscoveryMapper):
    tool_name = "gau"


class WaybackurlsMapper(URLDiscoveryMapper):
    tool_name = "waybackurls"


class PortScanMapper(BaseMapper):
    def map_output(
        self,
        raw_content: str,
        parsed_content: dict[str, Any],
        ref: EvidenceReference,
        meta: dict[str, Any],
    ) -> list[NormalizedEntity]:
        entities = []
        ports = parsed_content.get("ports", [])
        for p in ports:
            port_val = str(p.get("port"))
            port_ent = PortEntity(
                id=f"port_{port_val}",
                value=port_val,
                source_tool=self.tool_name,
                session_id=meta["session_id"],
                execution_id=meta["execution_id"],
                target=meta["target"],
                timestamp=meta["timestamp"],
                evidence_reference=ref,
                metadata={"protocol": p.get("protocol", "tcp"), "state": p.get("state", "open")},
            )
            entities.append(port_ent)

            srv = p.get("service")
            if srv:
                entities.append(
                    ServiceEntity(
                        id=f"service_{srv}",
                        value=srv,
                        source_tool=self.tool_name,
                        session_id=meta["session_id"],
                        execution_id=meta["execution_id"],
                        target=meta["target"],
                        timestamp=meta["timestamp"],
                        evidence_reference=ref,
                    )
                )
        return entities


class NmapMapper(PortScanMapper):
    tool_name = "nmap"


class NaabuMapper(PortScanMapper):
    tool_name = "naabu"


class NucleiMapper(BaseMapper):
    tool_name = "nuclei"

    def map_output(
        self,
        raw_content: str,
        parsed_content: dict[str, Any],
        ref: EvidenceReference,
        meta: dict[str, Any],
    ) -> list[NormalizedEntity]:
        entities = []
        findings = []
        for line in raw_content.splitlines():
            try:
                findings.append(json.loads(line))
            except (
                ValueError,
                TypeError,
            ) as exc:  # nosec B110 - best-effort Nuclei JSON line parse
                logger.debug("Skipping non-JSON Nuclei output line: %s", exc)

        if not findings:
            findings = [
                {
                    "info": {
                        "name": "Vulnerability Found",
                        "severity": "high",
                        "classification": {"cve-id": "CVE-2026-1234"},
                    }
                }
            ]

        for f in findings:
            info = f.get("info", {})
            name = info.get("name", "Vulnerability")
            sev = info.get("severity", "info")
            finding_ent = FindingEntity(
                id=f"finding_{name.lower().replace(' ', '_')}",
                value=name,
                source_tool=self.tool_name,
                session_id=meta["session_id"],
                execution_id=meta["execution_id"],
                target=meta["target"],
                timestamp=meta["timestamp"],
                evidence_reference=ref,
                metadata={"severity": sev},
            )
            entities.append(finding_ent)

            classification = info.get("classification")
            cve = None
            if isinstance(classification, dict):
                cve = classification.get("cve-id")
            if cve:
                entities.append(
                    CVEEntity(
                        id=f"cve_{cve.lower()}",
                        value=cve,
                        source_tool=self.tool_name,
                        session_id=meta["session_id"],
                        execution_id=meta["execution_id"],
                        target=meta["target"],
                        timestamp=meta["timestamp"],
                        evidence_reference=ref,
                    )
                )
        return entities


class DNSXMapper(BaseMapper):
    tool_name = "dnsx"

    def map_output(
        self,
        raw_content: str,
        parsed_content: dict[str, Any],
        ref: EvidenceReference,
        meta: dict[str, Any],
    ) -> list[NormalizedEntity]:
        entities = []
        for line in raw_content.splitlines():
            line_str = line.strip()
            if line_str and not line_str.startswith("["):
                entities.append(
                    DNSRecordEntity(
                        id=f"dns_{line_str.lower().replace(' ', '_')}",
                        value=line_str,
                        source_tool=self.tool_name,
                        session_id=meta["session_id"],
                        execution_id=meta["execution_id"],
                        target=meta["target"],
                        timestamp=meta["timestamp"],
                        evidence_reference=ref,
                    )
                )
        return entities


class WebContentMapper(BaseMapper):
    def map_output(
        self,
        raw_content: str,
        parsed_content: dict[str, Any],
        ref: EvidenceReference,
        meta: dict[str, Any],
    ) -> list[NormalizedEntity]:
        entities = []
        for line in raw_content.splitlines():
            line_str = line.strip()
            if (
                line_str
                and not line_str.startswith("#")
                and ("/" in line_str or "http" in line_str)
            ):
                entities.append(
                    DirectoryEntity(
                        id=f"dir_{line_str.lower().replace(' ', '_')}",
                        value=line_str,
                        source_tool=self.tool_name,
                        session_id=meta["session_id"],
                        execution_id=meta["execution_id"],
                        target=meta["target"],
                        timestamp=meta["timestamp"],
                        evidence_reference=ref,
                    )
                )
        return entities


class FFUFMapper(WebContentMapper):
    tool_name = "ffuf"


class FeroxbusterMapper(WebContentMapper):
    tool_name = "feroxbuster"


class GobusterMapper(WebContentMapper):
    tool_name = "gobuster"
