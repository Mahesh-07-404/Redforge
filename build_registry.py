import json
import os
import shutil
from pathlib import Path

skills_dir = Path("skills")
core_dir = skills_dir / "core"
domain_dir = skills_dir / "domain"

core_dir.mkdir(exist_ok=True)
domain_dir.mkdir(exist_ok=True)

# List of files to go to core
core_files = [
    "SYSTEM/personality.md",
    "SYSTEM/anti_hallucination.md",
    "SYSTEM/response_style.md",
    "SAFETY/legal_and_compliance.md",
    "SAFETY/data_handling_and_privacy.md",
    "SAFETY/scope_and_authorization.md",
    "EXECUTION/execution_workflow.md",
    "EXECUTION/reporting_standards.md",
]

registry = {"skills": []}

for root, dirs, files in os.walk(skills_dir):
    if "core" in root or "domain" in root or "cache" in root or "adaptive" in root or "versions" in root:
        continue
    for f in files:
        if not f.endswith(".md"): continue
        path = Path(root) / f
        rel_path = path.relative_to(skills_dir)
        rel_str = str(rel_path)
        
        # Decide destination
        if rel_str in core_files:
            dest = core_dir / f
            dest_rel = "core/" + f
        else:
            cat = rel_path.parts[0]
            domain_cat_dir = domain_dir / cat.lower()
            domain_cat_dir.mkdir(exist_ok=True)
            dest = domain_cat_dir / f
            dest_rel = f"domain/{cat.lower()}/{f}"
            
            # Read first line as title
            with open(path) as f_in:
                lines = f_in.readlines()
                title = lines[0].strip("# ").strip() if lines else f
                summary = lines[2].strip() if len(lines) > 2 else ""
            
            # Add to registry
            skill_id = f"{cat.lower()}_{f.replace('.md', '')}"
            registry["skills"].append({
                "id": skill_id,
                "path": dest_rel,
                "title": title,
                "summary": summary,
                "tags": [cat.lower()],
                "mode": [cat.lower()] if cat == "MODES" else [],
                "embedding_id": None
            })
            
        shutil.copy(path, dest)

with open(skills_dir / "registry.json", "w") as f:
    json.dump(registry, f, indent=2)

print("Registry created and files organized.")
