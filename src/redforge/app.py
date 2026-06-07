"""
RedForge Main Application
Central orchestrator for all RedForge functionality
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from redforge.safety import SafetyEngine, SafetyLevel
from redforge.tools import ToolManager, ToolRegistry
from redforge.modes.mode_implementations import (
    BugBountyMode, CTFMode, LearningMode, CodingMode, AndroidMode,
    ModeFactory, Mode, Finding, ModeConfig
)
from redforge.advanced import CVEGenerator, ReportGenerator
from redforge.memory.workspace import WorkspaceManager
from redforge.memory.skill_index import SkillIndexer
from redforge.llm import get_llm
from redforge.llm.catalog import DEFAULT_MODELS

logger = logging.getLogger(__name__)


@dataclass
class RedForgeConfig:
    """RedForge configuration"""
    mode: str = "bugbounty"
    target: Optional[str] = None
    autonomy_level: str = "manual"  # manual, partial, full
    llm_provider: str = "gemini"
    llm_model: str = DEFAULT_MODELS["gemini"]
    llm_api_key: Optional[str] = None
    workspace_dir: Path = Path("./workspaces")
    config_file: Optional[Path] = None


class RedForge:
    """
    Main RedForge application
    
    Orchestrates all components:
    - Safety engine for ethical boundaries
    - Tool manager for security tools
    - Mode handlers for different use cases
    - Memory system for context
    - LLM for AI capabilities
    """
    
    def __init__(self, config: Optional[RedForgeConfig] = None):
        self.config = config or RedForgeConfig()
        
        # Initialize components
        self.safety_engine = SafetyEngine()
        self.tool_manager = ToolManager(auto_install=True)
        self.cve_generator = CVEGenerator()
        self.report_generator = ReportGenerator()
        
        # Initialize memory
        self.workspace_manager = WorkspaceManager(
            persist_dir=str(self.config.workspace_dir)
        )
        self.workspace = self.workspace_manager.get_or_create_workspace(
            name="default",
            mode=self.config.mode
        )
        self.skill_indexer = SkillIndexer()
        
        # Initialize LLM
        self.llm = None
        self._init_llm()
        
        # Initialize modes
        self.modes: Dict[str, Any] = {}
        self.current_mode: Optional[Any] = None
        self._init_modes()
        
        logger.info(f"RedForge initialized in {self.config.mode} mode")
    
    def _init_llm(self):
        """Initialize LLM"""
        try:
            self.llm = get_llm(
                provider=self.config.llm_provider,
                model=self.config.llm_model,
                api_key=self.config.llm_api_key
            )
            logger.info(f"LLM initialized: {self.config.llm_provider}/{self.config.llm_model}")
        except Exception as e:
            logger.warning(f"LLM initialization failed: {e}")
            self.llm = None
    
    def _init_modes(self):
        """Initialize all modes"""
        self.modes = {
            Mode.BUGBOUNTY.value: BugBountyMode(
                ModeConfig(
                    name="bugbounty",
                    description="Bug bounty hunting mode",
                    skills_dir="skills/MODES/BUGBOUNTY",
                    essential_tools=["nmap", "ffuf", "sqlmap", "nuclei", "subfinder"]
                )
            ),
            Mode.CTF.value: CTFMode(
                ModeConfig(
                    name="ctf",
                    description="CTF competition mode",
                    skills_dir="skills/MODES/CTF",
                    essential_tools=["gdb", "pwntools", "python3"]
                )
            ),
            Mode.LEARNING.value: LearningMode(
                ModeConfig(
                    name="learning",
                    description="Learning and skill development",
                    skills_dir="skills/MODES/LEARNING"
                )
            ),
            Mode.CODING.value: CodingMode(
                ModeConfig(
                    name="coding",
                    description="Secure coding practice",
                    skills_dir="skills/MODES/CODING"
                )
            ),
            Mode.ANDROID.value: AndroidMode(
                ModeConfig(
                    name="android",
                    description="Android security testing",
                    skills_dir="skills/MODES/ANDROID",
                    essential_tools=["apktool", "jadx", "frida-tools"]
                )
            )
        }
        
        # Set dependencies
        for mode in self.modes.values():
            mode.set_safety_engine(self.safety_engine)
            mode.set_tool_manager(self.tool_manager)
            mode.set_llm(self.llm)
        
        # Set current mode
        if self.config.mode in self.modes:
            self.current_mode = self.modes[self.config.mode]
    
    def set_mode(self, mode_name: str) -> bool:
        """Switch to a different mode"""
        if mode_name in self.modes:
            self.current_mode = self.modes[mode_name]
            self.config.mode = mode_name
            logger.info(f"Mode switched to: {mode_name}")
            return True
        return False
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a task in the current mode"""
        if not self.current_mode:
            return {"error": "No mode selected"}
        
        ctx = context or {}
        if self.config.target:
            ctx["target"] = self.config.target
        
        # Safety check
        violations = self.safety_engine.validate_action(task, target=self.config.target)
        if self.safety_engine.is_blocked(violations):
            return {
                "error": "Action blocked by safety engine",
                "violations": [v.message for v in violations]
            }
        
        # Execute in mode
        return self.current_mode.execute(task, ctx)
    
    def add_finding(self, finding: Finding) -> None:
        """Add a finding (for bug bounty mode)"""
        if hasattr(self.current_mode, 'add_finding'):
            self.current_mode.add_finding(finding)
    
    def generate_report(self, format: str = "md") -> str:
        """Generate a report"""
        findings = []
        if hasattr(self.current_mode, 'findings'):
            findings = self.current_mode.findings
        
        self.report_generator.create_report({
            "title": f"{self.config.mode.title()} Assessment",
            "target": self.config.target or "Unknown",
            "author": "RedForge",
            "findings": [
                {
                    "title": f.title,
                    "severity": f.severity,
                    "description": f.description,
                    "cvss_score": f.cvss_score,
                    "cwe_id": f.cwe_id
                }
                for f in findings
            ]
        })
        
        if format == "json":
            return self.report_generator.generate_json()
        return self.report_generator.generate_markdown()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "mode": self.config.mode,
            "target": self.config.target,
            "autonomy": self.config.autonomy_level,
            "llm": f"{self.config.llm_provider}/{self.config.llm_model}" if self.llm else "Not configured",
            "tools_installed": sum(
                1 for s in self.tool_manager.installed_tools.values() 
                if s.installed
            ),
            "tools_total": len(self.tool_manager.installed_tools),
            "modes_available": list(self.modes.keys())
        }


def create_redforge(config_path: Optional[Path] = None) -> RedForge:
    """Factory function to create RedForge instance"""
    import yaml
    
    config = RedForgeConfig()
    
    if config_path and config_path.exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        
        config.mode = cfg.get("mode", "bugbounty")
        config.target = cfg.get("target")
        config.autonomy_level = cfg.get("autonomy_level", "manual")
        config.llm_provider = cfg.get("llm", {}).get("provider", "gemini")
        config.llm_model = cfg.get("llm", {}).get("model", DEFAULT_MODELS["gemini"])
        config.llm_api_key = cfg.get("llm", {}).get("api_key")
    
    return RedForge(config)
