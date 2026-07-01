"""Anthropic LLM provider (Claude)"""

from collections.abc import AsyncIterator
from typing import Any

from redforge.providers.base import ChatResponse, LLMProvider, Message
from redforge.providers.catalog import DEFAULT_MODELS, FALLBACK_MODELS, resolve_api_key


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider"""

    def __init__(
        self,
        model: str = DEFAULT_MODELS["anthropic"],
        api_key: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ):
        super().__init__(
            model=model,
            api_key=resolve_api_key("anthropic", api_key),
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
        **kwargs,
    ) -> ChatResponse:
        """Send a chat request to Anthropic"""
        anthropic_messages = [self._convert_message(m) for m in messages if m.role != "system"]
        system_message = next((m.content for m in messages if m.role == "system"), "")

        request_params = {
            "model": self.model,
            "messages": anthropic_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if system_message:
            request_params["system"] = system_message

        if tools:
            request_params["tools"] = tools

        try:
            response = await self.client.messages.create(**request_params)

            content = ""
            raw_response = response.model_dump()

            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            return ChatResponse(
                content=content,
                model=response.model,
                finish_reason=response.stop_reason,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                },
                raw_response=raw_response,
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic request failed: {e}") from e

    async def chat_stream(
        self, messages: list[Message], tools: list[dict] | None = None, **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat response from Anthropic"""
        anthropic_messages = [self._convert_message(m) for m in messages if m.role != "system"]
        system_message = next((m.content for m in messages if m.role == "system"), "")

        request_params = {
            "model": self.model,
            "messages": anthropic_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }

        if system_message:
            request_params["system"] = system_message

        if tools:
            request_params["tools"] = tools

        try:
            async with self.client.messages.stream(**request_params) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise RuntimeError(f"Anthropic stream failed: {e}") from e

    def is_available(self) -> bool:
        """Check if Anthropic API key is configured"""
        return bool(self.api_key)

    async def list_models(self) -> list[str]:
        """List available Claude models"""
        try:
            models = await self.client.models.list()
            return [m.id for m in models.data]
        except Exception:
            return FALLBACK_MODELS["anthropic"]

    def supports_tools(self) -> bool:
        """Claude supports tools (Computer Use, etc.)"""
        return True

    def supports_streaming(self) -> bool:
        return True

    def _convert_message(self, message: Message) -> dict[str, Any]:
        """Convert Message to Anthropic format"""
        return {"role": message.role, "content": message.content}
