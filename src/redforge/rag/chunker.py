import hashlib
from datetime import datetime
from typing import Any

from .contracts import Chunk


class ChunkEngine:
    @staticmethod
    def chunk_text(
        content: str,
        session_id: str,
        source: str,
        metadata: dict[str, Any] = {},
        tags: list[str] = [],
        chunk_size: int = 500,
    ) -> list[Chunk]:
        chunks = []
        words = content.split()
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i : i + chunk_size]
            chunk_content = " ".join(chunk_words)
            if not chunk_content.strip():
                continue

            chash = hashlib.sha256(chunk_content.encode("utf-8")).hexdigest()
            cid = f"{source}_{i}_{chash[:8]}"
            chunks.append(
                Chunk(
                    id=cid,
                    session_id=session_id,
                    source=source,
                    content=chunk_content,
                    metadata=metadata,
                    tags=tags,
                    hash=chash,
                    timestamp=datetime.now().isoformat(),
                )
            )
        return chunks
