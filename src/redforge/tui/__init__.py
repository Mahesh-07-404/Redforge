"""Lazy TUI exports for RedForge."""


def __getattr__(name: str):
    if name in {"RedForgeTUI", "launch", "launch_tui"}:
        from redforge.tui.textual_tui import RedForgeTUI, launch, launch_tui

        exports = {
            "RedForgeTUI": RedForgeTUI,
            "launch": launch,
            "launch_tui": launch_tui,
        }
        return exports[name]
    raise AttributeError(name)


__all__ = ["RedForgeTUI", "launch", "launch_tui"]
