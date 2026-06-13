import os
from pathlib import Path

TOOLS_DIR = Path("/home/mahesh/RedForge/skills/TOOLS")

def optimize_tools():
    if not TOOLS_DIR.exists():
        print("Tools directory not found.")
        return

    all_files = list(TOOLS_DIR.glob("*.md"))
    print(f"Found {len(all_files)} tool files to optimize.")

    rule_footer = """
## TOOL EXECUTION & ANTI-HALLUCINATION RULES
- **No Simulation**: You are strictly forbidden from simulating execution, mocking outputs, or pretending tool execution occurred. Only actual console output returned from a `TOOL:` block execution may be interpreted.
- **Target Binding**: All command arguments, parameters, and targets must be dynamically bound to the active session target `{target}`. Never replace the user target with a dummy placeholder (e.g. `example.com`).
- **No Evidence, No Finding**: If the tool command does not return output confirming a port, service, or vulnerability, do not report it as discovered.
"""

    for file_path in all_files:
        content = file_path.read_text(encoding="utf-8", errors="replace")

        # Replacements
        content = content.replace("target.com", "{target}")
        content = content.replace("example.com", "{target}")
        content = content.replace("example.org", "{target}")
        content = content.replace("demo.com", "{target}")
        content = content.replace("test.com", "{target}")

        # COMMIX / SSRF / HTTP examples
        content = content.replace("127.0.0.1", "{target}")
        content = content.replace("localhost", "{target}")

        # Check if already has rules
        if "## TOOL EXECUTION & ANTI-HALLUCINATION RULES" not in content:
            content += rule_footer

        file_path.write_text(content, encoding="utf-8")
        print(f"Optimized: {file_path.name}")

if __name__ == "__main__":
    optimize_tools()
