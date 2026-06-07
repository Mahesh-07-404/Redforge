"""
RedForge TUI - OpenCode Style
Modern split-pane terminal interface
"""

import sys
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from redforge.llm.catalog import DEFAULT_MODELS

try:
    from blessed import Terminal
except ImportError:
    print("Error: 'blessed' required. Install: pip install blessed")
    sys.exit(1)


@dataclass
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class OpenCodeStyleTUI:
    """OpenCode-inspired TUI for RedForge"""
    
    def __init__(self):
        self.term = Terminal()
        self.messages: List[Message] = []
        self.input_buffer = ""
        self.running = True
        
        # State
        self.mode = "bugbounty"
        self.autonomy = "manual"
        self.target = ""
        self.llm = f"gemini/{DEFAULT_MODELS['gemini']}"
        self.iteration = 0
        self.findings: List[dict] = []
        self.last_response = ""
        
    def run(self):
        """Run the TUI"""
        self.setup()
        
        try:
            with self.term.cbreak(), self.term.hidden_cursor():
                self.draw()
                
                while self.running:
                    key = self.term.inkey()
                    
                    if key.code == self.term.KEY_ESCAPE:
                        if self.input_buffer:
                            self.input_buffer = ""
                        else:
                            self.running = False
                    elif key.code == self.term.KEY_ENTER:
                        self.handle_enter()
                    elif key.code == self.term.KEY_BACKSPACE:
                        self.input_buffer = self.input_buffer[:-1]
                    elif key.code == self.term.KEY_TAB:
                        self.next_mode()
                    elif hasattr(key, 'char') and key.char and not key.is_sequence:
                        self.input_buffer += key.char
                    elif key.code == self.term.KEY_UP:
                        self.input_buffer = self.last_response
                    elif key == 'a' and self.term.keystate.get('ctrl'):
                        self.input_buffer = ""
                    elif key == 'l' and self.term.keystate.get('ctrl'):
                        self.messages = []
                    
                    self.draw()
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
        except Exception as e:
            print(f"\n\nError: {e}")
    
    def setup(self):
        """Initialize"""
        self.messages = [
            Message("system", "RedForge v1.0 - Autonomous Pentesting"),
            Message("system", f"Mode: {self.mode} | Autonomy: {self.autonomy} | Tab to switch mode"),
        ]
    
    def next_mode(self) -> str:
        """Cycle to next mode"""
        modes = ["bugbounty", "ctf", "learning", "android", "coding"]
        idx = modes.index(self.mode) + 1 if self.mode in modes else 0
        new_mode = modes[idx % len(modes)]
        self.messages.append(Message("system", f"Mode: {new_mode}"))
        return new_mode
    
    def handle_enter(self):
        """Process input"""
        if not self.input_buffer.strip():
            return
        
        user_input = self.input_buffer.strip()
        self.input_buffer = ""
        
        # Commands
        if user_input.lower() in ["exit", "quit", "q"]:
            self.running = False
            return
        
        if user_input.lower() in ["help", "?"]:
            self.show_help()
            return
        
        if user_input.lower() == "clear":
            self.messages = []
            return
        
        if user_input.lower().startswith("mode "):
            new_mode = user_input.split()[1].strip()
            if new_mode in ["bugbounty", "ctf", "learning", "android", "coding"]:
                self.mode = new_mode
                self.messages.append(Message("system", f"Mode: {self.mode}"))
            return
        
        if user_input.lower().startswith("target "):
            self.target = user_input.split()[1].strip()
            self.messages.append(Message("system", f"Target: {self.target}"))
            return
        
        if user_input.lower().startswith("autonomy "):
            level = user_input.split()[1].strip()
            if level in ["manual", "partial", "full"]:
                self.autonomy = level
                self.messages.append(Message("system", f"Autonomy: {self.autonomy}"))
            return
        
        if user_input.lower() == "status":
            self.show_status()
            return
        
        if user_input.lower() == "tools":
            self.show_tools()
            return
        
        if user_input.lower() == "skills":
            self.show_skills()
            return
        
        # Add user message
        self.messages.append(Message("user", user_input))
        
        # Process with agent
        self.process_input(user_input)
    
    def process_input(self, user_input: str):
        """Process user input"""
        self.iteration += 1
        
        # Generate response
        response = self.generate_response(user_input)
        self.last_response = response
        
        self.messages.append(Message("assistant", response))
    
    def generate_response(self, user_input: str) -> str:
        """Generate response based on input"""
        user_lower = user_input.lower()
        
        # Recon
        if "recon" in user_lower or "scan" in user_lower or "enum" in user_lower:
            return self.handle_recon(user_input)
        
        # Vulnerability
        if "vuln" in user_lower or "xss" in user_lower or "sqli" in user_lower or "inject" in user_lower:
            return self.handle_vuln(user_input)
        
        # Exploit
        if "exploit" in user_lower or "pwn" in user_lower:
            return self.handle_exploit(user_input)
        
        # Mode-specific
        if self.mode == "ctf":
            return self.handle_ctf(user_input)
        if self.mode == "android":
            return self.handle_android(user_input)
        if self.mode == "learning":
            return self.handle_learning(user_input)
        if self.mode == "coding":
            return self.handle_coding(user_input)
        
        # Default
        return self.get_default_response(user_input)
    
    def handle_recon(self, user_input: str) -> str:
        return f"""Reconnaissance for {self.target or '<target>'}:

Subdomain Enumeration:
  subfinder -d {{target}}
  amass enum -d {{target}}
  findomain -t {{target}}

Port Scanning:
  nmap -sC -sV -p- {{target}}
  rustscan -b 4500 -t 1500 {{target}}

Web Discovery:
  ffuf -u http://{{target}}/FUZZ -w wordlist
  httpx -l targets.txt

Directory Fuzzing:
  ffuf -u http://{{target}}/FUZZ -w dirb-wordlist"""
    
    def handle_vuln(self, user_input: str) -> str:
        return f"""Vulnerability Scanning for {self.target or '<target>'}:

Web Vulns:
  nuclei -u {{target}} -t templates/
  dalfox url {{target}}
  sqlmap -u {{target}} --batch

Network:
  nmap --script vuln {{target}}

Command Injection:
  commix --url {{target}}"""
    
    def handle_exploit(self, user_input: str) -> str:
        return """Exploitation:

  msfconsole - Metasploit Framework
  searchsploit <keyword> - ExploitDB
  pwntools (CTF)
  ropper --binary <file>

Always test on authorized targets only!"""
    
    def handle_ctf(self, user_input: str) -> str:
        user_lower = user_input.lower()
        if "list" in user_lower or "chall" in user_lower:
            return """CTF Challenges:

  [web]     SQLi, XSS, LFI, SSRF
  [pwn]     Buffer overflow, ROP
  [crypto] RSA, AES, hashing
  [rev]     Binary analysis
  [misc]    Stego, forensics

Commands:
  solve <id> <flag>
  hints <challenge>"""
        return """CTF Mode:

  list challenges - Show all
  solve <id> <flag> - Submit
  hints - Get hints
  scoreboard - View scores"""
    
    def handle_android(self, user_input: str) -> str:
        return f"""Android Pentesting:

  apktool d <app.apk> - Decompile
  jadx <app.apk> - Java source
  frida-ps - List processes
  objection -g <package> run

Static Analysis:
  jadx, jadx-gui, apktool
  
Dynamic Analysis:
  frida, objection, drozer"""
    
    def handle_learning(self, user_input: str) -> str:
        return """Learning Modules:

  1. Web Security (OWASP Top 10)
  2. Network Penetration Testing
  3. Reverse Engineering Basics
  4. Cryptography Fundamentals
  5. Privilege Escalation
  6. CTF Fundamentals

Type: learn <1-6> to start"""
    
    def handle_coding(self, user_input: str) -> str:
        return """Secure Coding:

  • Input Validation
  • SQL Injection Prevention
  • XSS Prevention
  • Auth & Session Management
  • Cryptography Best Practices

Ask: "fix sql injection in python" """
    
    def get_default_response(self, user_input: str) -> str:
        return f"""RedForge - {self.mode} mode

Commands:
  scan <target>    - Reconnaissance
  vuln <target>   - Find vulnerabilities  
  exploit <tgt>   - Exploitation
  mode <name>     - Switch mode
  target <host>  - Set target
  status          - Show status
  tools           - List tools
  skills          - Show skills

Current: {self.mode} | {self.autonomy} | {self.target or 'no target'}"""
    
    def show_help(self):
        self.messages.append(Message("system", """Commands:
  scan <target>    - Run reconnaissance
  vuln <target>   - Scan vulnerabilities
  exploit <tgt>   - Exploitation
  mode <mode>     - Switch mode (bugbounty/ctf/learning/android/coding)
  target <host>   - Set target
  autonomy <lvl>  - manual/partial/full
  status          - Show status
  tools           - List tools
  skills          - Show loaded skills
  clear           - Clear chat

Keys:
  Tab  - Switch mode
  ↑    - Paste last response
  Esc  - Exit"""))
    
    def show_status(self):
        self.messages.append(Message("system", f"""Status:
  Mode:      {self.mode}
  Autonomy:  {self.autonomy}
  Target:    {self.target or '(none)'}
  LLM:       {self.llm}
  Iteration: {self.iteration}
  Findings:  {len(self.findings)}"""))
    
    def show_tools(self):
        self.messages.append(Message("system", f"""Tools ({self.mode} mode):
  nmap, subfinder, ffuf, nuclei, sqlmap
  amass, httpx, dalfox, commix
  
Installed: 11/28"""))
    
    def show_skills(self):
        skills = {
            "bugbounty": "27 skills loaded",
            "ctf": "17 skills loaded", 
            "learning": "16 skills loaded",
            "android": "15 skills loaded",
            "coding": "8 skills loaded",
        }
        self.messages.append(Message("system", f"Skills:\n  " + "\n  ".join(f"{k}: {v}" for k, v in skills.items())))
    
    def draw(self):
        """Draw the complete UI"""
        w = self.term.width
        h = self.term.height
        
        print(self.term.home + self.term.clear, end="")
        
        # Header
        self.draw_header(w)
        
        # Main content
        self.draw_main(w, h)
        
        # Input
        self.draw_input(w)
    
    def draw_header(self, w: int):
        """Header bar"""
        # Logo and mode
        left = f"\033[1;38;5;45m⛏\033[0m RedForge "
        left += f"\033[38;5;59m[\033[0m{self.mode.upper()}\033[38;5;59m]\033[0m"
        
        if self.target:
            left += f" \033[38;5;208m◆\033[0m {self.target}"
        
        print(left, end="")
        print(" " * (w - len(left) - 30), end="")
        
        # Right status
        status = f"\033[38;5;244m{self.autonomy}\033[0m | iter:\033[38;5;76m{self.iteration}\033[0m"
        print(status)
    
    def draw_main(self, w: int, h: int):
        """Main content area"""
        msg_h = h - 3
        
        # Calculate visible messages
        visible = self.messages[-msg_h:] if len(self.messages) > msg_h else self.messages
        
        for msg in visible:
            self.draw_message(msg, w - 2)
    
    def draw_message(self, msg: Message, w: int):
        """Draw a message"""
        if msg.role == "user":
            print(f"\033[1;38;5;45m➜\033[0m {msg.content[:w-2]}")
        elif msg.role == "assistant":
            lines = self.wrap(msg.content, w - 4)
            for line in lines:
                print(f"  {line}")
        else:  # system
            print(f"\033[38;5;244m●\033[0m {msg.content[:w-4]}")
    
    def draw_input(self, w: int):
        """Input area"""
        print("─" * (w - 1))
        print(f"\033[1;38;5;45m➜\033[0m {self.input_buffer}", end="", flush=True)
    
    def wrap(self, text: str, width: int) -> list:
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


def launch_tui():
    """Launch TUI"""
    app = OpenCodeStyleTUI()
    app.run()


if __name__ == "__main__":
    launch_tui()
