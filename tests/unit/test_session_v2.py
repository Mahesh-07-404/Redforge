import pytest
import os
import yaml
from pathlib import Path
from redforge.core.session import SessionStore, SessionService
from redforge.memory.manager import MemoryManager
from redforge.contracts.memory import MemoryEntry
from redforge.config.config import load_config, Settings

def test_session_create_returns_session_active_and_namespace(tmp_path):
    db_path = str(tmp_path / "sessions.db")
    store = SessionStore(db_path)
    service = SessionService(store)
    
    session = service.create(mode="bugbounty", target="example.com", autonomy="manual")
    assert session.id is not None
    assert session.status == "active"
    assert session.memory_namespace == f"session_{session.id[:8]}"

def test_session_archive_and_load(tmp_path):
    db_path = str(tmp_path / "sessions.db")
    store = SessionStore(db_path)
    service = SessionService(store)
    
    session = service.create(mode="bugbounty", target="example.com", autonomy="manual")
    service.archive(session.id)
    
    loaded = service.load(session.id)
    assert loaded is not None
    assert loaded.status == "archived"

def test_session_list_active(tmp_path):
    db_path = str(tmp_path / "sessions.db")
    store = SessionStore(db_path)
    service = SessionService(store)
    
    s1 = service.create(mode="bugbounty", target="example1.com", autonomy="manual")
    s2 = service.create(mode="bugbounty", target="example2.com", autonomy="manual")
    
    service.archive(s1.id)
    
    active_sessions = service.list(status="active")
    active_ids = [s["id"] for s in active_sessions]
    
    assert s2.id in active_ids
    assert s1.id not in active_ids

def test_different_memory_namespaces(tmp_path):
    db_path = str(tmp_path / "sessions.db")
    store = SessionStore(db_path)
    service = SessionService(store)
    
    s1 = service.create(mode="bugbounty", target="example1.com", autonomy="manual")
    s2 = service.create(mode="bugbounty", target="example2.com", autonomy="manual")
    
    assert s1.memory_namespace != s2.memory_namespace

def test_memory_session_isolation(tmp_path):
    persist_dir = str(tmp_path / "data")
    os.makedirs(persist_dir, exist_ok=True)
    
    memory_manager = MemoryManager(persist_dir)
    session_a = "sessionA_123456"
    session_b = "sessionB_123456"
    
    entry = MemoryEntry(id="00000000-0000-0000-0000-000000000001", content="secret content for A", metadata={})
    memory_manager.store(session_a, entry)
    
    # Retrieve under session A
    res_a = memory_manager.retrieve(session_a, "secret", top_k=5)
    assert len(res_a) > 0
    assert any("secret content for A" in r.content for r in res_a)
    
    # Retrieve under session B - should not find A's ephemeral memory
    res_b = memory_manager.retrieve(session_b, "secret", top_k=5)
    assert not any("secret content for A" in r.content for r in res_b)

def test_config_loads_without_workspace_in_yaml(tmp_path):
    config_yaml_content = """
autonomy:
  default_level: partial
llm:
  provider: gemini
session:
  data_dir: ./data
  max_active_sessions: 10
  retention_days: 90
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_yaml_content)
    
    settings = load_config(config_file)
    assert settings.session.data_dir == "./data"
    assert settings.session.max_active_sessions == 10
    assert not hasattr(settings, "workspace")
