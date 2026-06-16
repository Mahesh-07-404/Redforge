from typing import List
from ..contracts.tool import VerifiedResult

class HallucinationGuard:
    def check(self, llm_response: str, verified_results: List[VerifiedResult]) -> str:
        return llm_response
