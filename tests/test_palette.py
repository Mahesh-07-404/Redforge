import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from textual.app import App, ComposeResult
from textual.widgets import Input, OptionList
from redforge.tui.palette import CommandPalette, CommandRegistry


class PaletteTestApp(App[None]):
    """Helper Textual app to run pilot tests on CommandPalette."""
    
    def __init__(self):
        super().__init__()
        self.selected_cmd = None

    def compose(self) -> ComposeResult:
        yield Input(id="dummy-input")

    def open_palette(self, initial_query: str = ""):
        palette = CommandPalette(initial_query=initial_query)
        palette.on_select = self.on_select
        self.mount(palette)

    def on_select(self, cmd: str):
        self.selected_cmd = cmd


def test_command_registry():
    """Verify CommandRegistry functionality (builtin, dynamic, and exists checking)."""
    # Check built-in commands
    assert CommandRegistry.exists("/mode")
    assert CommandRegistry.exists("/session list")
    assert CommandRegistry.exists("/session save")
    assert not CommandRegistry.exists("/nonexistentcmd")
    
    # Register dynamic command
    CommandRegistry.register("exploit_active", "Trigger exploitation workflow")
    assert CommandRegistry.exists("/exploit_active")
    assert CommandRegistry.exists("exploit_active")
    
    commands = CommandRegistry.get_commands()
    assert any(c["cmd"] == "/exploit_active" for c in commands)


@pytest.mark.asyncio
async def test_palette_open_close():
    """Verify CommandPalette opens and closes correctly on escape."""
    app = PaletteTestApp()
    async with app.run_test() as pilot:
        # Check initial state
        assert len(app.query(CommandPalette)) == 0
        
        # Open palette
        app.open_palette("/")
        await pilot.pause()
        assert len(app.query(CommandPalette)) == 1
        
        # Focus cp-input
        palette = app.query_one(CommandPalette)
        cp_input = palette.query_one("#cp-input")
        assert cp_input.has_focus
        
        # Close palette via escape key
        await pilot.press("escape")
        await pilot.pause()
        assert len(app.query(CommandPalette)) == 0


@pytest.mark.asyncio
async def test_palette_filtering_and_navigation():
    """Verify filtering (fuzzy search) and key navigation in the option list."""
    app = PaletteTestApp()
    async with app.run_test() as pilot:
        app.open_palette("/")
        await pilot.pause()
        
        palette = app.query_one(CommandPalette)
        ol = palette.query_one("#cp-option-list", OptionList)
        
        # Initially there should be multiple commands
        assert ol.option_count > 0
        
        # Type "mo" to filter down
        await pilot.press("m", "o")
        await pilot.pause()
        
        # Matches should list "/mode" and "/model"
        assert ol.option_count > 0
        first_option = ol.get_option_at_index(0)
        assert "/mode" in str(first_option.prompt)
        
        # Highlight navigation with down arrow
        highlighted_before = ol.highlighted
        await pilot.press("down")
        await pilot.pause()
        assert ol.highlighted != highlighted_before
        
        # Highlight navigation with up arrow
        await pilot.press("up")
        await pilot.pause()
        assert ol.highlighted == highlighted_before
        
        # Highlight navigation with tab
        await pilot.press("tab")
        await pilot.pause()
        assert ol.highlighted != highlighted_before
        
        # Highlight navigation with shift+tab
        await pilot.press("shift+tab")
        await pilot.pause()
        assert ol.highlighted == highlighted_before


@pytest.mark.asyncio
async def test_palette_selection():
    """Verify selecting an option confirmed by enter closes and triggers callback."""
    app = PaletteTestApp()
    async with app.run_test() as pilot:
        app.open_palette("/")
        await pilot.pause()
        
        # Type "help"
        await pilot.press("h", "e", "l", "p")
        await pilot.pause()
        
        # Confirm selection by pressing enter
        await pilot.press("enter")
        await pilot.pause()
        
        # Verify command palette is removed and callback was triggered
        assert len(app.query(CommandPalette)) == 0
        assert app.selected_cmd == "/help"
