import pytest
import sys
import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from redforge.core.database import SessionDatabase
from redforge.tui.palette import CommandRegistry
from redforge.tui.textual_tui import RedForgeTUI
from redforge.tui.renderer import Msg


class MockTUI(RedForgeTUI):
    def __init__(self, db_path, **kwargs):
        super().__init__(**kwargs)
        self.db = SessionDatabase(db_path)
        self.mock_feed = []
        
    def _init_agent(self) -> None:
        self.model_label = "mock/model"
        class MockAgent:
            llm = None
        self._agent = MockAgent()

    def _refresh_transcript(self) -> None:
        pass


@pytest.mark.asyncio
async def test_all_slash_commands():
    with TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_redforge.db")
        app = MockTUI(db_path=db_path)
        
        async with app.run_test() as pilot:
            # 1. Test /help
            await app._slash("/help")
            await pilot.pause()
            
            # 2. Test /mode
            await app._slash("/mode ctf")
            await pilot.pause()
            assert app.mode == "ctf"
            
            # 3. Test /target
            await app._slash("/target 127.0.0.1")
            await pilot.pause()
            assert app.target == "127.0.0.1"
            
            # 4. Test /autonomy
            await app._slash("/autonomy partial")
            await pilot.pause()
            assert app.autonomy == "partial"
            
            # 5. Test /status
            await app._slash("/status")
            await pilot.pause()
            
            # 6. Test /findings (when empty)
            await app._slash("/findings")
            await pilot.pause()
            
            # Add a mock finding
            app.store.append(Msg(role="finding", content="Found SQL injection", severity="high"))
            await app._slash("/findings")
            await pilot.pause()
            
            # 7. Test /files
            await app._slash("/files")
            await pilot.pause()
            
            # 8. Test /session save
            await app._slash("/session save test_save")
            await pilot.pause()
            
            # Test /session current
            await app._slash("/session current")
            await pilot.pause()
            
            # Test /session list
            await app._slash("/session list")
            await pilot.pause()
            
            # Test /session load (load current one)
            current_id = app.session_id
            await app._slash(f"/session load {current_id}")
            await pilot.pause()
            
            # Test /session export
            export_file = str(Path(tmpdir) / "session.json")
            await app._slash(f"/session export {export_file}")
            await pilot.pause()
            assert os.path.exists(export_file)
            
            # Test /session delete
            await app._slash(f"/session delete {current_id}")
            await pilot.pause()
            
            # 9. Test /report generate (needs findings)
            app.store.append(Msg(role="finding", content="Found XSS vulnerability", severity="medium"))
            await app._slash("/report generate")
            await pilot.pause()
            
            # Test /report export
            report_export_file = str(Path(tmpdir) / "report.md")
            await app._slash(f"/report export {report_export_file}")
            await pilot.pause()
            assert os.path.exists(report_export_file)
            
            # Test /report list
            await app._slash("/report list")
            await pilot.pause()
            
            # 10. Test /tools list
            await app._slash("/tools list")
            await pilot.pause()
            
            # Test /tools verify
            await app._slash("/tools verify")
            await pilot.pause()
            
            # Test /tools install (invalid/nonexistent tool should fail gracefully)
            await app._slash("/tools install nonexistent_tool")
            await pilot.pause()
            
            # 11. Test /memory stats
            await app._slash("/memory stats")
            await pilot.pause()
            
            # Test /memory rebuild
            await app._slash("/memory rebuild")
            await pilot.pause()
            
            # Test /memory search
            await app._slash("/memory search test")
            await pilot.pause()
            
            # Test /memory clear
            await app._slash("/memory clear")
            await pilot.pause()
            
            # 12. Test /history
            await app._slash("/history")
            await pilot.pause()
            
            # 13. Test /workspace info
            await app._slash("/workspace info")
            await pilot.pause()
            
            # Test /workspace files
            await app._slash("/workspace files")
            await pilot.pause()
            
            # Test /workspace reset
            await app._slash("/workspace reset")
            await pilot.pause()
            
            # 14. Test /doctor
            await app._slash("/doctor")
            await pilot.pause()
            
            # 15. Test /config
            await app._slash("/config")
            await pilot.pause()
            
            # Test /config autonomy.default_level partial
            await app._slash("/config autonomy.default_level partial")
            await pilot.pause()
            
            # Test /clear
            await app._slash("/clear")
            await pilot.pause()
            assert len(app.store._msgs) == 0
