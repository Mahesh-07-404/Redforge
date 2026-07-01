class EmbeddingProvider:
    async def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class MockEmbedder(EmbeddingProvider):
    async def embed_text(self, text: str) -> list[float]:
        return [0.1] * 128

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 128 for _ in texts]


class OpenAIEmbedder(EmbeddingProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    async def embed_text(self, text: str) -> list[float]:
        return [0.2] * 128

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.2] * 128 for _ in texts]


class GeminiEmbedder(EmbeddingProvider):
    async def embed_text(self, text: str) -> list[float]:
        return [0.3] * 128

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.3] * 128 for _ in texts]


class OllamaEmbedder(EmbeddingProvider):
    async def embed_text(self, text: str) -> list[float]:
        return [0.4] * 128

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.4] * 128 for _ in texts]


class SentenceTransformersEmbedder(EmbeddingProvider):
    async def embed_text(self, text: str) -> list[float]:
        return [0.5] * 128

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.5] * 128 for _ in texts]


class FastEmbedEmbedder(EmbeddingProvider):
    async def embed_text(self, text: str) -> list[float]:
        return [0.6] * 128

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.6] * 128 for _ in texts]
