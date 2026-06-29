from typing import List
from .contracts import RAGResult

class Reranker:
    @staticmethod
    def rerank(results: List[RAGResult], query: str, session_id: str) -> List[RAGResult]:
        scored_results = []
        for res in results:
            score = res.score
            if res.chunk.session_id == session_id:
                score += 0.2
            if res.chunk.timestamp:
                score += 0.05
            query_words = set(query.lower().split())
            content_words = set(res.chunk.content.lower().split())
            overlap = len(query_words.intersection(content_words))
            score += overlap * 0.05
            
            scored_results.append((res, score))
            
        scored_results.sort(key=lambda x: x[1], reverse=True)
        for item, final_score in scored_results:
            item.score = final_score
            
        return [x[0] for x in scored_results]
