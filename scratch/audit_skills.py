import os
import re
from pathlib import Path

SKILLS_DIR = Path("/home/mahesh/RedForge/skills")

def audit_skills():
    if not SKILLS_DIR.exists():
        print(f"Skills directory {SKILLS_DIR} does not exist.")
        return

    all_md_files = []
    for root, dirs, files in os.walk(SKILLS_DIR):
        dirs[:] = [d for d in dirs if not d.startswith(("__", "."))]
        for file in files:
            if file.endswith(".md"):
                all_md_files.append(Path(root) / file)

    print(f"Found {len(all_md_files)} markdown skill files.\n")

    placeholders = ["example.com", "example.org", "localhost", "127.0.0.1", "demo.com", "test.com"]
    simulation_kws = ["simulate", "simulated", "fictional", "example output", "sample output", "placeholder finding"]

    audit_records = []

    for file_path in sorted(all_md_files):
        rel_path = file_path.relative_to(SKILLS_DIR)
        content = file_path.read_text(encoding="utf-8", errors="replace")
        
        # Word count
        words = len(content.split())
        
        # Find first header as title
        title = "Untitled"
        header_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if header_match:
            title = header_match.group(1).strip()

        # Check for placeholders
        found_placeholders = [ph for ph in placeholders if ph in content.lower()]
        
        # Check for simulation/fictional instructions
        found_simulations = [kw for kw in simulation_kws if kw in content.lower()]

        audit_records.append({
            "rel_path": str(rel_path),
            "title": title,
            "words": words,
            "placeholders": found_placeholders,
            "simulations": found_simulations,
            "char_len": len(content)
        })

    # Output stats
    print("## TOP 20 LARGE FILES:")
    for record in sorted(audit_records, key=lambda x: x["words"], reverse=True)[:20]:
        print(f"- {record['rel_path']} ({record['words']} words, Title: {record['title']})")
    
    print("\n## PLACEHOLDER FINDINGS:")
    placeholder_count = 0
    for record in audit_records:
        if record["placeholders"]:
            print(f"- {record['rel_path']}: {record['placeholders']}")
            placeholder_count += 1
    print(f"Total files with placeholder domains/IPs: {placeholder_count}")

    print("\n## SIMULATION FINDINGS:")
    sim_count = 0
    for record in audit_records:
        if record["simulations"]:
            print(f"- {record['rel_path']}: {record['simulations']}")
            sim_count += 1
    print(f"Total files with simulation keywords: {sim_count}")

    # Duplicates & redundancy analysis
    print("\n## REDUNDANCY ANALYSIS (Title-based):")
    titles = {}
    for record in audit_records:
        titles.setdefault(str(record["title"]).lower(), []).append(record["rel_path"])
    
    dup_count = 0
    for title, paths in titles.items():
        if len(paths) > 1:
            print(f"- Title '{title}' is repeated in:")
            for p in paths:
                print(f"  * {p}")
            dup_count += 1
    print(f"Total repeated titles: {dup_count}")

if __name__ == "__main__":
    audit_skills()
