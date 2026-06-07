"""TUI screens for RedForge"""

from typing import List, Tuple
from blessed import Terminal


class Screen:
    """Base screen class"""
    
    def __init__(self, term: Terminal):
        self.term = term
    
    def draw(self, height: int, width: int):
        """Draw the screen"""
        raise NotImplementedError
    
    def handle_input(self, key):
        """Handle input"""
        pass


class DashboardScreen(Screen):
    """Dashboard overview screen"""
    
    def __init__(self, term: Terminal, data: dict = None):
        super().__init__(term)
        self.data = data or {}
    
    def draw(self, height: int, width: int):
        """Draw dashboard"""
        lines = []
        
        lines.append(self.term.black_on_cyan(" RedForge Dashboard ".center(width)))
        
        lines.append("")
        lines.append("╔" + "═" * (width - 2) + "╗")
        
        col_width = (width - 4) // 2
        
        left = [
            "║ SYSTEM STATUS",
            "║" + "─" * (width - 2),
            f"║ LLM: {self.data.get('llm', 'N/A')}",
            f"║ Mode: {self.data.get('mode', 'N/A')}",
            f"║ Iterations: {self.data.get('iterations', 0)}",
        ]
        
        right = [
            "║ WORKSPACE",
            "║" + "─" * (width - 2),
            f"║ Name: {self.data.get('workspace', 'N/A')}",
            f"║ Sessions: {self.data.get('sessions', 0)}",
            f"║ Findings: {self.data.get('findings', 0)}",
        ]
        
        for i in range(max(len(left), len(right))):
            left_line = left[i] if i < len(left) else "║"
            right_line = right[i] if i < len(right) else "║"
            lines.append(f"{left_line}{' ' * (col_width - len(left_line) + 2)}{right_line}")
        
        lines.append("╚" + "═" * (width - 2) + "╝")
        
        return lines


class ChatScreen(Screen):
    """Chat interface screen"""
    
    def __init__(self, term: Terminal):
        super().__init__(term)
        self.history: List[Tuple[str, str]] = []
        self.input_buffer = ""
    
    def draw(self, height: int, width: int):
        """Draw chat interface"""
        lines = []
        
        header = f" Chat | Mode: {self.data.get('mode', 'N/A')} | Autonomy: {self.data.get('autonomy', 'N/A')} "
        lines.append(self.term.black_on_cyan(header.ljust(width)))
        
        chat_height = height - 6
        
        visible_history = self.history[-chat_height:] if len(self.history) > chat_height else self.history
        
        for role, msg in visible_history:
            if role == "user":
                lines.append(self.term.bold_cyan(f"[YOU] {msg[:width-10]}"))
            elif role == "assistant":
                for line in self._wrap(msg, width - 8):
                    lines.append(self.term.bold_green(f"[BOT]  {line}"))
            else:
                lines.append(self.term.dim(f"[SYS]  {msg[:width-10]}"))
        
        input_line = f"> {self.input_buffer}"
        lines.append("─" * width)
        lines.append(self.term.black_on_white(input_line.ljust(width)))
        
        return lines
    
    def add_message(self, role: str, message: str):
        """Add message to history"""
        self.history.append((role, message))
    
    def _wrap(self, text: str, width: int) -> List[str]:
        """Wrap text"""
        words = text.split()
        lines = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= width:
                current += (" " if current else "") + word
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines


class WorkspaceScreen(Screen):
    """Workspace management screen"""
    
    def __init__(self, term: Terminal, workspaces: List[dict] = None):
        super().__init__(term)
        self.workspaces = workspaces or []
    
    def draw(self, height: int, width: int):
        """Draw workspace list"""
        lines = []
        
        lines.append(self.term.black_on_cyan(" Workspaces ".center(width)))
        lines.append("")
        
        if not self.workspaces:
            lines.append("  No workspaces found".center(width))
            lines.append("")
            lines.append("  Press 'n' to create a new workspace".center(width))
        else:
            lines.append("╔" + "─" * 8 + "┬" + "─" * (width - 20) + "┬" + "─" * 10 + "╗")
            lines.append("║" + " ID".ljust(8) + "│" + " NAME".ljust(width - 20) + "│" + " CREATED".ljust(10) + "║")
            lines.append("╠" + "═" * 8 + "╪" + "═" * (width - 20) + "╪" + "═" * 10 + "╣")
            
            for ws in self.workspaces[:height - 10]:
                ws_id = ws.get('id', '')[:8]
                ws_name = ws.get('name', 'N/A')[:width - 22]
                ws_created = ws.get('created', '')[:10]
                lines.append("║" + ws_id.ljust(8) + "│" + ws_name.ljust(width - 20) + "│" + ws_created.ljust(10) + "║")
            
            lines.append("╚" + "─" * 8 + "┴" + "─" * (width - 20) + "┴" + "─" * 10 + "╝")
        
        lines.append("")
        lines.append("[n] New  [d] Delete  [s] Switch  [r] Refresh".center(width))
        
        return lines
