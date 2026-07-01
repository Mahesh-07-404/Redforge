import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import requests

logger = logging.getLogger(__name__)


class Platform(Enum):
    HACKERONE = "hackerone"
    BUGCROWD = "bugcrowd"
    OPENBB = "openbugbounty"
    INTIGRITI = "intigriti"
    YESECURITY = "yesecurity"


@dataclass
class Program:
    platform: str
    name: str
    handle: str
    url: str
    scope: list[dict] = field(default_factory=list)
    max_bounty: float | None = None
    min_bounty: float | None = None
    categories: list[str] = field(default_factory=list)
    rewards: dict[str, str] = field(default_factory=dict)
    allows_disclosure: bool = True
    patched_at: str | None = None
    archived: bool = False


@dataclass
class Submission:
    title: str
    description: str
    severity: str
    vulnerability_type: str
    impact: str
    steps_to_reproduce: list[str]
    proof_of_concept: str | None = None
    attachments: list[str] = field(default_factory=list)


@dataclass
class Report:
    id: str
    title: str
    status: str
    severity: str
    created_at: str
    updated_at: str
    platform: str
    program_handle: str
    url: str
    state: str = "open"
    researcher_response_required: bool = False


class BasePlatform(ABC):
    def __init__(self, api_key: str, config: dict[str, Any] = None):
        self.api_key = api_key
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )

    @abstractmethod
    def get_programs(self) -> list[Program]:
        pass

    @abstractmethod
    def get_program(self, handle: str) -> Program | None:
        pass

    @abstractmethod
    def submit_report(self, program_handle: str, submission: Submission) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_reports(self, program_handle: str) -> list[Report]:
        pass


class HackerOneAPI(BasePlatform):
    BASE_URL = "https://api.hackerone.com/v1"

    def __init__(self, api_key: str, api_secret: str = None, config: dict = None):
        super().__init__(api_key, config)
        self.api_secret = api_secret
        self.session.headers["Authorization"] = f"Bearer {api_key}:{api_secret}"

    def get_programs(self) -> list[Program]:
        try:
            response = self.session.get(
                f"{self.BASE_URL}/programs", params={"filter[state]": "publicly_disclosable"}
            )
            response.raise_for_status()
            data = response.json()
            programs = []
            for p in data.get("programs", []):
                programs.append(
                    Program(
                        platform="hackerone",
                        name=p.get("name", ""),
                        handle=p.get("handle", ""),
                        url=p.get("url", ""),
                        scope=p.get("scope", []),
                    )
                )
            return programs
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get programs: {e}")
            return []

    def get_program(self, handle: str) -> Program | None:
        try:
            response = self.session.get(f"{self.BASE_URL}/programs/{handle}")
            response.raise_for_status()
            data = response.json()
            return Program(
                platform="hackerone",
                name=data.get("name", ""),
                handle=handle,
                url=data.get("url", ""),
                scope=data.get("scope", []),
            )
        except requests.exceptions.RequestException:
            return None

    def submit_report(self, program_handle: str, submission: Submission) -> dict[str, Any]:
        try:
            payload = {
                "title": submission.title,
                "description": submission.description,
                "severity": submission.severity,
                "vulnerability_type": submission.vulnerability_type,
                "impact": submission.impact,
                "steps_to_reproduce": submission.steps_to_reproduce,
                "proof_of_concept": submission.proof_of_concept,
            }
            response = self.session.post(
                f"{self.BASE_URL}/programs/{program_handle}/submissions", json=payload
            )
            response.raise_for_status()
            return {"success": True, "submission_id": response.json().get("id")}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to submit report: {e}")
            return {"success": False, "error": str(e)}

    def get_reports(self, program_handle: str) -> list[Report]:
        try:
            response = self.session.get(f"{self.BASE_URL}/programs/{program_handle}/submissions")
            response.raise_for_status()
            data = response.json()
            reports = []
            for r in data.get("submissions", []):
                reports.append(
                    Report(
                        id=r.get("id"),
                        title=r.get("title", ""),
                        status=r.get("state", "open"),
                        severity=r.get("severity", ""),
                        created_at=r.get("created_at", ""),
                        updated_at=r.get("updated_at", ""),
                        platform="hackerone",
                        program_handle=program_handle,
                        url=r.get("url", ""),
                    )
                )
            return reports
        except requests.exceptions.RequestException:
            return []


class BugcrowdAPI(BasePlatform):
    BASE_URL = "https://api.bugcrowd.com"

    def get_programs(self) -> list[Program]:
        try:
            response = self.session.get(f"{self.BASE_URL}/programs")
            response.raise_for_status()
            data = response.json()
            programs = []
            for p in data.get("programs", []):
                programs.append(
                    Program(
                        platform="bugcrowd",
                        name=p.get("name", ""),
                        handle=p.get("handle", ""),
                        url=f"https://bugcrowd.com/{p.get('handle', '')}",
                        scope=p.get("targets", {}).get("targets", []),
                        max_bounty=p.get("max_bounty"),
                        min_bounty=p.get("min_bounty"),
                        rewards=p.get("rewards", {}),
                        categories=p.get("categories", []),
                    )
                )
            return programs
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get programs: {e}")
            return []

    def get_program(self, handle: str) -> Program | None:
        try:
            response = self.session.get(f"{self.BASE_URL}/programs/{handle}")
            response.raise_for_status()
            data = response.json()
            p = data.get("program", {})
            return Program(
                platform="bugcrowd",
                name=p.get("name", ""),
                handle=handle,
                url=f"https://bugcrowd.com/{handle}",
                scope=p.get("targets", {}).get("targets", []),
            )
        except requests.exceptions.RequestException:
            return None

    def submit_report(self, program_handle: str, submission: Submission) -> dict[str, Any]:
        try:
            vrt_map = {
                "critical": "P1 - Critical",
                "high": "P2 - High",
                "medium": "P3 - Medium",
                "low": "P4 - Low",
            }
            payload = {
                "title": submission.title,
                "description": submission.description,
                "vrt": vrt_map.get(submission.severity.lower(), "P4 - Low"),
                "vulnerability_subtype": submission.vulnerability_type,
                "impact": submission.impact,
                "steps_to_reproduce": "\n".join(submission.steps_to_reproduce),
                "proof_of_concept": submission.proof_of_concept,
            }
            response = self.session.post(
                f"{self.BASE_URL}/submissions",
                params={"program_handle": program_handle},
                json=payload,
            )
            response.raise_for_status()
            return {"success": True, "submission_id": response.json().get("id")}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to submit report: {e}")
            return {"success": False, "error": str(e)}

    def get_reports(self, program_handle: str) -> list[Report]:
        try:
            response = self.session.get(
                f"{self.BASE_URL}/submissions", params={"program_handle": program_handle}
            )
            response.raise_for_status()
            data = response.json()
            reports = []
            for r in data.get("submissions", []):
                reports.append(
                    Report(
                        id=r.get("id"),
                        title=r.get("title", ""),
                        status=r.get("state", "open"),
                        severity=r.get("vrt", ""),
                        created_at=r.get("created_at", ""),
                        updated_at=r.get("updated_at", ""),
                        platform="bugcrowd",
                        program_handle=program_handle,
                        url=f"https://bugcrowd.com/{program_handle}/submissions/{r.get('id')}",
                    )
                )
            return reports
        except requests.exceptions.RequestException:
            return []


class PlatformManager:
    def __init__(self):
        self.platforms: dict[Platform, BasePlatform] = {}
        self.active_platform: Platform | None = None

    def add_platform(self, platform: Platform, api_key: str, **config):
        if platform == Platform.HACKERONE:
            self.platforms[platform] = HackerOneAPI(api_key, config.get("api_secret"), config)
        elif platform == Platform.BUGCROWD:
            self.platforms[platform] = BugcrowdAPI(api_key, config)
        else:
            logger.warning(f"Platform {platform} not yet implemented")
            return
        logger.info(f"Added {platform.value} integration")

    def set_active(self, platform: Platform):
        if platform in self.platforms:
            self.active_platform = platform
            logger.info(f"Active platform: {platform.value}")
        else:
            logger.error(f"Platform {platform} not configured")

    def get_programs(self, platform: Platform = None) -> list[Program]:
        p = platform or self.active_platform
        if not p or p not in self.platforms:
            return []
        return self.platforms[p].get_programs()

    def get_program(self, handle: str, platform: Platform = None) -> Program | None:
        p = platform or self.active_platform
        if not p or p not in self.platforms:
            return None
        return self.platforms[p].get_program(handle)

    def submit_report(
        self, program_handle: str, submission: Submission, platform: Platform = None
    ) -> dict[str, Any]:
        p = platform or self.active_platform
        if not p or p not in self.platforms:
            return {"success": False, "error": "No platform configured"}
        return self.platforms[p].submit_report(program_handle, submission)

    def get_reports(self, program_handle: str = None, platform: Platform = None) -> list[Report]:
        p = platform or self.active_platform
        if not p or p not in self.platforms:
            return []
        return self.platforms[p].get_reports(program_handle or "")

    def search_programs(self, target: str, platform: Platform = None) -> list[Program]:
        results = []
        platforms_to_search = [platform] if platform else self.platforms.keys()
        for p in platforms_to_search:
            if p not in self.platforms:
                continue
            programs = self.platforms[p].get_programs()
            for prog in programs:
                for scope_item in prog.scope:
                    if target.lower() in str(scope_item).lower():
                        results.append(prog)
                        break
        return results


def create_submission(finding: dict[str, Any], template: str = "hackerone") -> Submission:
    if template == "hackerone":
        description = f"""## Summary
{finding.get("description", "")}

## Vulnerability Details
**Type:** {finding.get("type", "Unknown")}
**Severity:** {finding.get("severity", "Medium")}
**CVSS:** {finding.get("cvss_score", "N/A")}

## Impact
{finding.get("impact", "Demonstrates a security vulnerability that could be exploited.")}

## remediation
{finding.get("remediation", "")}
"""
    else:
        description = f"""**Description:**
{finding.get("description", "")}

**Impact:**
{finding.get("impact", "")}

**Remediation:**
{finding.get("remediation", "")}
"""
    return Submission(
        title=finding.get("title", "Untitled Finding"),
        description=description,
        severity=finding.get("severity", "medium"),
        vulnerability_type=finding.get("type", "Other"),
        impact=finding.get("impact", ""),
        steps_to_reproduce=finding.get("steps", [""]),
        proof_of_concept=finding.get("poc", ""),
        attachments=finding.get("attachments", []),
    )
