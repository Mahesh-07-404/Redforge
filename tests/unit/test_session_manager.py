import pytest
from redforge.core.session import SessionStore
from redforge.core.session import SessionManager

def test_session_manager_create_and_load(tmp_path):
    db_path = str(tmp_path / "sessions.db")
    store = SessionStore(db_path)
    manager = SessionManager(store)
    
    session = manager.create(mode="bugbounty", target="example.com", autonomy="manual")
    assert session.id is not None
    assert session.mode == "bugbounty"
    
    loaded = manager.load(session.id)
    assert loaded is not None
    assert loaded.id == session.id
    assert loaded.target == "example.com"
