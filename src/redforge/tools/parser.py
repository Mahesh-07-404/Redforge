import re
from typing import List, Dict, Any

def parse_tool_calls(text: str) -> List[Dict[str, Any]]:
    """
    Detects TOOL: directives in the LLM response.
    """
    # Strip markdown code blocks if the LLM wrongly wrapped the TOOL block
    text = re.sub(r"```[a-zA-Z]*", "", text)
    text = text.replace("```", "")
    
    calls = []
    blocks = re.split(r"TOOL:\s*", text, flags=re.IGNORECASE)

    for block in blocks[1:]:  # first split is before first TOOL:
        lines = block.strip().splitlines()
        if not lines:
            continue

        tool_name = lines[0].strip().strip('`').lower()
        params: Dict[str, str] = {}
        code_lines: List[str] = []
        in_code = False

        for line in lines[1:]:
            line_stripped = line.strip()
            if re.match(r"^CODE:\s*$", line_stripped, re.IGNORECASE):
                in_code = True
                continue
            if in_code:
                if re.match(r"^(TOOL:|COMMAND:|TARGET:|FLAGS:|ARGS:)", line_stripped, re.IGNORECASE):
                    in_code = False
                else:
                    code_lines.append(line)
                    continue
            m = re.match(r"^([A-Z]+):\s*(.*)", line_stripped, re.IGNORECASE)
            if m:
                key = m.group(1).lower()
                val = m.group(2).strip().strip('`')
                params[key] = val

        if code_lines:
            params["code"] = "\n".join(code_lines).strip('`\n')

        if tool_name:
            calls.append({"tool": tool_name, **params})

    return calls
