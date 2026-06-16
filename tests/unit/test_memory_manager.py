import pytest
from redforge.memory.manager import MemoryManager
from redforge.contracts.memory import MemoryEntry

def test_memory_manager_store_and_retrieve(tmp_path):
    manager = MemoryManager(str(tmp_path))
    session_id = "testsession123"
    
    valid_uuid = "00000000-0000-0000-0000-000000000001"
    entry = MemoryEntry(id=valid_uuid, content="test content", metadata={})
    manager.store(session_id, entry)
    
    results = manager.retrieve(session_id, "test content", top_k=1)
    
    assert len(results) > 0
    assert results[0].id == valid_uuid
    assert "test content" in results[0].content
