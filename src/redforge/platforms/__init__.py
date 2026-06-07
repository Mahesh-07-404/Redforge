"""
RedForge Bug Bounty Platform Integration
HackerOne, Bugcrowd, and OpenBugBounty API integrations
"""
import requests
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class Platform(Enum):
    HACKERONE = "hackerone"
    BUGCROWD = "bugcrowd"
    OPENBB = "openbugbounty"
    INTIGRITI = "intigriti"
    YESECURITY = "yesecurity"


@dataclass
class Program:
    """Bug bounty program"""
    platform: str
    name: str
    handle: str
    url: str
    scope: List[Dict] = field(default_factory=list)
    max_bounty: Optional[float] = None
    min_bounty: Optional[float] = None
    categories: List[str] = field(default_factory=list)
    rewards: Dict[str, str] = field(default_factory=dict)
    allows_disclosure: bool = True
    patched_at: Optional[str] = None
    archived: bool = False


@dataclass
class Submission:
    """Report submission"""
    title: str
    description: str
    severity: str
    vulnerability_type: str
    impact: str
    steps_to_reproduce: List[str]
    proof_of_concept: Optional[str] = None
    attachments: List[str] = field(default_factory=list)


@dataclass
class Report:
    """Bug bounty report"""
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
    """Base class for platform integrations"""
    
    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        self.api_key = api_key
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    @abstractmethod
    def get_programs(self) -> List[Program]:
        """Get available programs"""
        pass
    
    @abstractmethod
    def get_program(self, handle: str) -> Program:
        """Get specific program"""
        pass
    
    @abstractmethod
    def submit_report(self, program_handle: str, submission: Submission) -> Dict[str, Any]:
        """Submit a report"""
        pass
    
    @abstractmethod
    def get_reports(self, program_handle: str) -> List[Report]:
        """Get reports for a program"""
        pass


class HackerOneAPI(BasePlatform):
    """HackerOne API integration"""
    
    BASE_URL = "https://api.hackerone.com/v1"
    
    def __init__(self, api_key: str, api_secret: str = None, config: Dict = None):
        super().__init__(api_key, config)
        self.api_secret = api_secret
        # HackerOne uses different auth
        self.session.headers["Authorization"] = f"Bearer {api_key}:{api_secret}"
    
    def get_programs(self) -> List[Program]:
        """Get all available programs"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/programs",
                params={"filter[state]": "publicly_disclosable"}
            )
            response.raise_for_status()
            data = response.json()
            
            programs = []
            for p in data.get("data", []):
                programs.append(Program(
                    platform="hackerone",
                    name=p.get("attributes", {}).get("name", ""),
                    handle=p.get("attributes", {}).get("handle", ""),
                    url=f"https://hackerone.com/{p.get('attributes', {}).get('handle', '')}",
                    scope=p.get("attributes", {}).get("scope", []),
                    max_bounty=p.get("attributes", {}).get("max_bounty"),
                    min_bounty=p.get("attributes", {}).get("min_bounty"),
                    allows_disclosure=p.get("attributes", {}).get("allows_public_disclosure", True)
                ))
            
            return programs
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get programs: {e}")
            return []
    
    def get_program(self, handle: str) -> Optional[Program]:
        """Get specific program"""
        try:
            response = self.session.get(f"{self.BASE_URL}/programs/{handle}")
            response.raise_for_status()
            data = response.json()
            
            p = data.get("data", {})
            return Program(
                platform="hackerone",
                name=p.get("attributes", {}).get("name", ""),
                handle=handle,
                url=f"https://hackerone.com/{handle}",
                scope=p.get("attributes", {}).get("scope", [])
            )
        
        except requests.exceptions.RequestException:
            return None
    
    def submit_report(self, program_handle: str, submission: Submission) -> Dict[str, Any]:
        """Submit a report to HackerOne"""
        try:
            # Map severity to HackerOne format
            severity_map = {
                "critical": "critical",
                "high": "high",
                "medium": "medium",
                "low": "low",
                "info": "informational"
            }
            
            payload = {
                "data": {
                    "type": "report",
                    "attributes": {
                        "title": submission.title,
                        "description": submission.description,
                        "severity_rating": severity_map.get(submission.severity.lower(), "medium"),
                        "vulnerability_types": [submission.vulnerability_type],
                        "impact": submission.impact,
                        "steps_to_reproduce": submission.steps_to_reproduce,
                        "proof_of_concept": submission.proof_of_concept,
                        "attachments": submission.attachments
                    }
                }
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/reports",
                params={"program_handle": program_handle},
                json=payload
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "report_id": response.json().get("data", {}).get("id"),
                "url": response.json().get("links", {}).get("self")
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to submit report: {e}")
            return {"success": False, "error": str(e)}
    
    def get_reports(self, program_handle: str) -> List[Report]:
        """Get reports for a program"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/reports",
                params={"program_handle": program_handle}
            )
            response.raise_for_status()
            data = response.json()
            
            reports = []
            for r in data.get("data", []):
                reports.append(Report(
                    id=r.get("id"),
                    title=r.get("attributes", {}).get("title", ""),
                    status=r.get("attributes", {}).get("state", "open"),
                    severity=r.get("attributes", {}).get("severity_rating", ""),
                    created_at=r.get("attributes", {}).get("created_at", ""),
                    updated_at=r.get("attributes", {}).get("updated_at", ""),
                    platform="hackerone",
                    program_handle=program_handle,
                    url=f"https://hackerone.com/reports/{r.get('id')}"
                ))
            
            return reports
        
        except requests.exceptions.RequestException:
            return []


class BugcrowdAPI(BasePlatform):
    """Bugcrowd API integration"""
    
    BASE_URL = "https://api.bugcrowd.com"
    
    def get_programs(self) -> List[Program]:
        """Get all available programs"""
        try:
            response = self.session.get(f"{self.BASE_URL}/programs")
            response.raise_for_status()
            data = response.json()
            
            programs = []
            for p in data.get("programs", []):
                programs.append(Program(
                    platform="bugcrowd",
                    name=p.get("name", ""),
                    handle=p.get("handle", ""),
                    url=f"https://bugcrowd.com/{p.get('handle', '')}",
                    scope=p.get("targets", {}).get("targets", []),
                    rewards=p.get("rewards", {}),
                    categories=p.get("categories", [])
                ))
            
            return programs
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get programs: {e}")
            return []
    
    def get_program(self, handle: str) -> Optional[Program]:
        """Get specific program"""
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
                scope=p.get("targets", {}).get("targets", [])
            )
        
        except requests.exceptions.RequestException:
            return None
    
    def submit_report(self, program_handle: str, submission: Submission) -> Dict[str, Any]:
        """Submit a report to Bugcrowd"""
        try:
            # Bugcrowd VRT severity mapping
            vrt_map = {
                "critical": "P1 - Critical",
                "high": "P2 - High",
                "medium": "P3 - Medium",
                "low": "P4 - Low"
            }
            
            payload = {
                "title": submission.title,
                "description": submission.description,
                "vrt": vrt_map.get(submission.severity.lower(), "P4 - Low"),
                "vulnerability_subtype": submission.vulnerability_type,
                "impact": submission.impact,
                "steps_to_reproduce": "\n".join(submission.steps_to_reproduce),
                "proof_of_concept": submission.proof_of_concept
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/submissions",
                params={"program_handle": program_handle},
                json=payload
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "submission_id": response.json().get("id")
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to submit report: {e}")
            return {"success": False, "error": str(e)}
    
    def get_reports(self, program_handle: str) -> List[Report]:
        """Get submissions for a program"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/submissions",
                params={"program_handle": program_handle}
            )
            response.raise_for_status()
            data = response.json()
            
            reports = []
            for r in data.get("submissions", []):
                reports.append(Report(
                    id=r.get("id"),
                    title=r.get("title", ""),
                    status=r.get("state", "open"),
                    severity=r.get("vrt", ""),
                    created_at=r.get("created_at", ""),
                    updated_at=r.get("updated_at", ""),
                    platform="bugcrowd",
                    program_handle=program_handle,
                    url=f"https://bugcrowd.com/{program_handle}/submissions/{r.get('id')}"
                ))
            
            return reports
        
        except requests.exceptions.RequestException:
            return []


class PlatformManager:
    """
    Manage multiple bug bounty platform integrations
    """
    
    def __init__(self):
        self.platforms: Dict[Platform, BasePlatform] = {}
        self.active_platform: Optional[Platform] = None
    
    def add_platform(self, platform: Platform, api_key: str, **config):
        """Add a platform integration"""
        if platform == Platform.HACKERONE:
            self.platforms[platform] = HackerOneAPI(
                api_key,
                config.get("api_secret"),
                config
            )
        elif platform == Platform.BUGCROWD:
            self.platforms[platform] = BugcrowdAPI(api_key, config)
        else:
            logger.warning(f"Platform {platform} not yet implemented")
            return
        
        logger.info(f"Added {platform.value} integration")
    
    def set_active(self, platform: Platform):
        """Set active platform"""
        if platform in self.platforms:
            self.active_platform = platform
            logger.info(f"Active platform: {platform.value}")
        else:
            logger.error(f"Platform {platform} not configured")
    
    def get_programs(self, platform: Platform = None) -> List[Program]:
        """Get programs from platform"""
        p = platform or self.active_platform
        if not p or p not in self.platforms:
            return []
        
        return self.platforms[p].get_programs()
    
    def get_program(self, handle: str, platform: Platform = None) -> Optional[Program]:
        """Get specific program"""
        p = platform or self.active_platform
        if not p or p not in self.platforms:
            return None
        
        return self.platforms[p].get_program(handle)
    
    def submit_report(self, program_handle: str, submission: Submission,
                     platform: Platform = None) -> Dict[str, Any]:
        """Submit report to platform"""
        p = platform or self.active_platform
        if not p or p not in self.platforms:
            return {"success": False, "error": "No platform configured"}
        
        return self.platforms[p].submit_report(program_handle, submission)
    
    def get_reports(self, program_handle: str = None,
                   platform: Platform = None) -> List[Report]:
        """Get reports"""
        p = platform or self.active_platform
        if not p or p not in self.platforms:
            return []
        
        return self.platforms[p].get_reports(program_handle or "")
    
    def search_programs(self, target: str, platform: Platform = None) -> List[Program]:
        """Search programs by target"""
        results = []
        
        platforms_to_search = [platform] if platform else self.platforms.keys()
        
        for p in platforms_to_search:
            if p not in self.platforms:
                continue
            
            programs = self.platforms[p].get_programs()
            
            # Filter by target in scope
            for prog in programs:
                for scope_item in prog.scope:
                    if target.lower() in str(scope_item).lower():
                        results.append(prog)
                        break
        
        return results


def create_submission(finding: Dict[str, Any], template: str = "hackerone") -> Submission:
    """Create a submission from a finding"""
    
    if template == "hackerone":
        description = f"""## Summary
{finding.get('description', '')}

## Vulnerability Details
**Type:** {finding.get('type', 'Unknown')}
**Severity:** {finding.get('severity', 'Medium')}
**CVSS:** {finding.get('cvss_score', 'N/A')}

## Impact
{finding.get('impact', 'Demonstrates a security vulnerability that could be exploited.')}

## remediation
{finding.get('remediation', '')}
"""
    else:
        description = f"""**Description:**
{finding.get('description', '')}

**Impact:**
{finding.get('impact', '')}

**Remediation:**
{finding.get('remediation', '')}
"""
    
    return Submission(
        title=finding.get('title', 'Untitled Finding'),
        description=description,
        severity=finding.get('severity', 'medium'),
        vulnerability_type=finding.get('type', 'Other'),
        impact=finding.get('impact', ''),
        steps_to_reproduce=finding.get('steps', ['']),
        proof_of_concept=finding.get('poc', ''),
        attachments=finding.get('attachments', [])
    )
