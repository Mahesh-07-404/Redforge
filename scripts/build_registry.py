import json
import os
from pathlib import Path

skills_dir = Path("skills")
domain_dir = skills_dir / "domain"

registry = {"skills": []}

def get_skill_id(rel_path):
    # rel_path is e.g. domain/modes/android.md
    parts = rel_path.parts
    # parts[1] is category, parts[2] is filename
    cat = parts[1]
    name = parts[2].replace(".md", "")
    return f"{cat}_{name}"

for root, dirs, files in os.walk(domain_dir):
    for f in files:
        if not f.endswith(".md"): continue
        path = Path(root) / f
        rel_path = path.relative_to(skills_dir)
        
        # Read first line as title
        with open(path) as f_in:
            lines = f_in.readlines()
            title = lines[0].strip("# ").strip() if lines else f
            summary = lines[2].strip() if len(lines) > 2 else ""
        
        skill_id = get_skill_id(rel_path)
        registry["skills"].append({
            "id": skill_id,
            "path": str(rel_path),
            "title": title,
            "summary": summary,
            "tags": [rel_path.parts[1]],
            "mode": [rel_path.parts[1]] if rel_path.parts[1] == "modes" else [],
            "embedding_id": None
        })

# Sort for consistency
registry["skills"].sort(key=lambda x: x["id"])

with open(skills_dir / "registry.json", "w") as f:
    json.dump(registry, f, indent=2)

print("Registry updated.")
