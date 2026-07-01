"""Gemini LLM provider for Google AI Studio"""

from collections.abc import AsyncIterator

from redforge.providers.base import ChatResponse, LLMProvider, Message
from redforge.providers.catalog import DEFAULT_MODELS, FALLBACK_MODELS, resolve_api_key


class GeminiProvider(LLMProvider):
    """Google Gemini API provider using google-genai library"""

    def __init__(
        self,
        model: str = DEFAULT_MODELS["gemini"],
        api_key: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ):
        super().__init__(
            model=model,
            api_key=resolve_api_key("gemini", api_key),
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        self._client = None

    def _get_client(self):
        """Get or create Gemini client"""
        if self._client is None:
            from google.genai import Client

            self._client = Client(api_key=self.api_key)
        return self._client

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
        **kwargs,
    ) -> ChatResponse:
        """Send a chat request to Gemini"""
        prompt = self._format_prompt(messages)

        try:
            # Use async client for chat
            from google.genai import Client

            async_client = Client(api_key=self.api_key).aio

            response = await async_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                },
            )

            content = ""
            if hasattr(response, "text"):
                content = response.text
            elif hasattr(response, "parts"):
                content = "".join(p.text for p in response.parts if hasattr(p, "text"))

            return ChatResponse(
                content=content,
                model=self.model,
                finish_reason="stop",
                raw_response={"candidates": [str(response)]},
            )
        except Exception as e:
            raise RuntimeError(f"Gemini request failed: {e}")

    async def chat_stream(
        self, messages: list[Message], tools: list[dict] | None = None, **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from Gemini"""
        prompt = self._format_prompt(messages)

        try:
            # Use async client for streaming
            from google.genai import Client

            async_client = Client(api_key=self.api_key).aio

            stream = await async_client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                },
            )

            async for chunk in stream:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text
                elif hasattr(chunk, "parts"):
                    for p in chunk.parts:
                        if hasattr(p, "text"):
                            yield p.text

        except Exception as e:
            raise RuntimeError(f"Gemini stream failed: {e}")

    def is_available(self) -> bool:
        """Check if Gemini API key is configured"""
        return bool(self.api_key)

    async def list_models(self) -> list[str]:
        """List available Gemini models"""
        try:
            client = self._get_client()
            models = client.models.list()
            return [m.name.replace("models/", "") for m in models]
        except:
            return FALLBACK_MODELS["gemini"]

    def supports_tools(self) -> bool:
        """Gemini supports function calling"""
        return True

    def supports_streaming(self) -> bool:
        return True

    def _format_prompt(self, messages: list[Message]) -> str:
        """Convert messages to Gemini prompt format"""
        parts = []
        for msg in messages:
            if msg.role == "system":
                parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                parts.append(f"Assistant: {msg.content}")
        return "\n\n".join(parts)
