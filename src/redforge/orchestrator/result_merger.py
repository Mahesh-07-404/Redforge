from typing import List
from .contracts import AgentTaskResult

class ResultMerger:
    @staticmethod
    def merge_results(results: List[AgentTaskResult]) -> str:
        merged_lines = []
        seen_lines = set()
        
        for r in results:
            for line in r.output.splitlines():
                clean_line = line.strip()
                if clean_line and clean_line not in seen_lines:
                    seen_lines.add(clean_line)
                    merged_lines.append(clean_line)
                    
        return "\n".join(merged_lines)
