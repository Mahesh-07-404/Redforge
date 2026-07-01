from .contracts import RAGContext, RAGResult


class ContextBuilder:
    @staticmethod
    def build_context(results: list[RAGResult], token_limit: int = 1000) -> RAGContext:
        context_parts = []
        current_tokens = 0
        used_sources = []

        seen_contents = set()
        for r in results:
            clean_content = r.chunk.content.strip()
            if clean_content in seen_contents:
                continue
            seen_contents.add(clean_content)

            source_ref = f"Source: {r.chunk.source} (Ref: {r.chunk.metadata.get('task_id', 'N/A')})"
            block = f"[{source_ref}]\n{clean_content}\n"

            estimated_tokens = int(len(block.split()) * 1.3)
            if current_tokens + estimated_tokens > token_limit:
                break

            context_parts.append(block)
            current_tokens += estimated_tokens
            used_sources.append(r)

        context_text = "\n".join(context_parts)
        return RAGContext(
            context_text=context_text, sources=used_sources, token_count=current_tokens
        )
