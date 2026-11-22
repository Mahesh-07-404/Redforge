"""RedForge Terminal User Interface (Textual).

Public entry points::

    from redforge.tui import launch_textual
    launch_textual()

or from the shell::

    redforge-tui
    python -m redforge.tui.textual_tui
"""

from __future__ import annotations


def launch_textual() -> int:
    """Launch the RedForge Textual TUI. Returns a process exit code."""
    from .textual_tui import RedForgeTUI

    RedForgeTUI().run()
    return 0


__all__ = ["launch_textual"]
