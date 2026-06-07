"""Configuration management for RedForge"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from redforge.llm.catalog import DEFAULT_MODELS, resolve_api_key


class LLMConfig(BaseModel):
    provider: str = "gemini"
    model: str = DEFAULT_MODELS["gemini"]
    api_key: str = Field(default_factory=lambda: resolve_api_key("gemini"))
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7
    max_tokens: int = 4096
    streaming: bool = True

    @model_validator(mode="after")
    def resolve_provider_defaults(self) -> "LLMConfig":
        provider = self.provider.lower()
        if not self.model or (provider != "gemini" and self.model == DEFAULT_MODELS["gemini"]):
            self.model = DEFAULT_MODELS.get(provider, DEFAULT_MODELS["gemini"])
        if not self.api_key:
            self.api_key = resolve_api_key(provider)
        return self


class AutonomyConfig(BaseModel):
    default_level: str = "manual"
    max_level: str = "partial"
    require_consent: bool = True
    legal_warning: bool = True
    max_iterations: int = 50
    loop_threshold: int = 10
    destructive_threshold: int = 3
    rate_limit_actions: int = 100
    no_internet_attack: bool = False
    scope_strict: bool = True


class MemoryConfig(BaseModel):
    vector_db: str = "qdrant"
    persist_dir: str = "./workspaces"
    skill_index: str = "./skills/skills_index.json"
    collection_name: str = "redforge_memory"


class WorkspaceConfig(BaseModel):
    auto_save: bool = True
    backup_enabled: bool = True
    retention_days: int = 90
    default_workspace: str = "default"


class ToolsConfig(BaseModel):
    auto_detect: bool = True
    install_missing: bool = False
    installation_method: str = "auto"
    timeout: int = 300
    custom_paths: Dict[str, str] = Field(default_factory=dict)
    required_tools: Dict[str, list] = Field(default_factory=dict)


class IntegrationsConfig(BaseModel):
    hackerone: Dict[str, Any] = Field(default_factory=lambda: {"api_token": "", "enabled": False})
    bugcrowd: Dict[str, Any] = Field(default_factory=lambda: {"api_key": "", "enabled": False})
    openbugbounty: Dict[str, Any] = Field(default_factory=lambda: {"enabled": False})


class WebConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 5000
    auth_required: bool = True
    secret_key: str = ""
    debug: bool = False


class UIConfig(BaseModel):
    theme: str = "dark"
    streaming: bool = True
    color_output: bool = True
    verbose: bool = False


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "./logs/redforge.log"
    max_size: int = 10 * 1024 * 1024
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class SecurityConfig(BaseModel):
    encrypt_workspaces: bool = False
    secure_api_keys: bool = True
    audit_log_enabled: bool = True
    audit_log_file: str = "./logs/audit.log"


class Settings(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    autonomy: AutonomyConfig = Field(default_factory=AutonomyConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    integrations: IntegrationsConfig = Field(default_factory=IntegrationsConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)


def find_config_file() -> Optional[Path]:
    """Find config.yaml in common locations"""
    search_paths = [
        Path.cwd() / "config.yaml",
        Path.cwd() / "config.yml",
        Path.home() / ".config" / "redforge" / "config.yaml",
        Path.home() / ".redforge" / "config.yaml",
        Path("/etc/redforge/config.yaml"),
    ]
    
    for path in search_paths:
        if path.exists():
            return path
    return None


def load_config(config_path: Optional[Path] = None) -> Settings:
    """Load configuration from YAML file"""
    if config_path is None:
        config_path = find_config_file()
    
    if config_path and config_path.exists():
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
        return Settings(**config_data)
    
    return Settings()


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return load_config()


def save_config(settings: Settings, config_path: Path) -> None:
    """Save configuration to YAML file"""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(settings.model_dump(), f, default_flow_style=False)


class ConfigManager:
    """Runtime configuration manager"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or find_config_file()
        self._settings = load_config(self.config_path)
    
    @property
    def settings(self) -> Settings:
        return self._settings
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot notation key"""
        keys = key.split(".")
        value = self._settings.model_dump()
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set config value by dot notation key"""
        keys = key.split(".")
        obj = self._settings.model_dump()
        target = obj
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value
        self._settings = Settings(**obj)
        
        if self.config_path:
            save_config(self._settings, self.config_path)
