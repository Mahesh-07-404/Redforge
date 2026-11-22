import logging

from ..contracts.conversation import ConversationContext
from ..providers.base import LLMProvider, Message

logger = logging.getLogger(__name__)

_LLM_UNAVAILABLE = (
    "I can't reach a language model right now, so I can't answer freely yet. "
    "RedForge needs an LLM provider configured to handle general questions and "
    "security reasoning. Quick options:\n"
    "  • Local & free — install Ollama (https://ollama.com), run "
    "`ollama pull llama3.2`, and set the provider to 'ollama'.\n"
    "  • Cloud — add an API key (Gemini / OpenAI / Groq / Anthropic) to a `.env` "
    "file or `config.yaml`.\n"
    "In the TUI you can also run `/model <provider>` to switch."
)


class ConversationManager:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def get_response(
        self, text: str, context: ConversationContext, token_callback=None, event_callback=None
    ) -> str:
        lower_text = text.lower().strip()

        # Exact greetings fast paths
        if lower_text in ["hi", "hello", "hey", "yo"]:
            response = "Hello! I am RedForge, your autonomous security assistant. How can I help you today?"
            if event_callback:
                await event_callback("assistant_start", content="")
            if token_callback:
                await token_callback(response)
            if event_callback:
                await event_callback("assistant_end", content=response)
            return response

        if lower_text in ["how are you", "how are you?"]:
            response = (
                "I am functioning at full capacity and ready to assist you. How can I help you?"
            )
            if event_callback:
                await event_callback("assistant_start", content="")
            if token_callback:
                await token_callback(response)
            if event_callback:
                await event_callback("assistant_end", content=response)
            return response

        # Dynamically retrieve the best prompt template from prompt_library based on user intent/text
        from redforge.prompt_library.registry import get_prompt_library_registry

        try:
            library = get_prompt_library_registry()
            query_lower = text.lower()

            if any(
                w in query_lower
                for w in ["debug", "error", "exception", "traceback", "fix bug", "crash"]
            ):
                prompt_tmpl = library.get_prompt("debugging_debugger")
                system_prompt = prompt_tmpl.template.format(
                    error_message=text[:300],
                    code_snippet="No snippet provided. Context: " + text,
                    runtime_env="Unknown",
                )
            elif any(
                w in query_lower
                for w in ["architecture", "design", "diagram", "uml", "component", "api design"]
            ):
                prompt_tmpl = library.get_prompt("architecture_designer")
                system_prompt = prompt_tmpl.template.format(
                    requirements=text,
                    constraints="Ensure modularity and clean separation of concerns.",
                )
            elif any(
                w in query_lower
                for w in [
                    "code",
                    "program",
                    "script",
                    "refactor",
                    "function",
                    "class",
                    "write a",
                    "implement",
                ]
            ):
                prompt_tmpl = library.get_prompt("coding_developer")
                system_prompt = prompt_tmpl.template.format(
                    language="Python/Generic", task_description=text, code_context="None provided."
                )
            elif any(
                w in query_lower
                for w in [
                    "document",
                    "readme",
                    "technical writing",
                    "guide",
                    "tutorial",
                    "write a doc",
                ]
            ):
                prompt_tmpl = library.get_prompt("documentation_writer")
                system_prompt = prompt_tmpl.template.format(
                    topic=text, target_audience="Developers / Users", draft_content=""
                )
            else:
                prompt_tmpl = library.get_prompt("chat_general_chat")
                system_prompt = prompt_tmpl.template.format(
                    query=text, history=str(context.previous_messages[-5:])
                )
        except Exception as e:
            logger.debug("Failed to render prompt from library: %s", e)
            system_prompt = (
                "You are RedForge, a friendly, capable, general-purpose AI assistant who is also "
                "an expert in offensive security and penetration testing. Help with anything the "
                "user asks — everyday questions, writing, coding, planning, explanations, casual "
                "conversation — and bring security expertise when the topic calls for it. Never "
                "refuse a normal, non-security request by insisting you only do security work; "
                "answer it directly. Do not request or require a target for general chat. "
                "Use the conversation history to answer follow-up questions. "
            )

        if context.active_target:
            system_prompt += f"\nThe currently active target is {context.active_target}."

        messages = [Message(role="system", content=system_prompt)]

        # Limit history to prevent excessive tokens
        history_msgs = context.previous_messages[-10:]
        messages.extend(history_msgs)

        if event_callback:
            await event_callback("assistant_start", content="")

        use_streaming = False
        try:
            if self.llm_provider.supports_streaming():
                use_streaming = True
        except Exception as exc:  # nosec B110 - best-effort check for streaming support
            logger.debug("Failed to check if LLM provider supports streaming: %s", exc)

        if use_streaming:
            content_chunks = []
            try:
                async for chunk in self.llm_provider.chat_stream(messages):
                    content_chunks.append(chunk)
                    if token_callback:
                        await token_callback(chunk)
                content = "".join(content_chunks)
            except Exception:
                try:
                    resp = await self.llm_provider.chat(messages)
                    content = resp.content
                    if token_callback:
                        await token_callback(content)
                except Exception as exc:
                    logger.warning("LLM unavailable for general chat: %s", exc)
                    content = _LLM_UNAVAILABLE
                    if token_callback:
                        await token_callback(content)
        else:
            try:
                resp = await self.llm_provider.chat(messages)
                content = resp.content
            except Exception as exc:
                logger.warning("LLM unavailable for general chat: %s", exc)
                content = _LLM_UNAVAILABLE

        if event_callback:
            await event_callback("assistant_end", content=content)

        return content
