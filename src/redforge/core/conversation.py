import logging
from typing import List, Optional
from ..providers.base import Message, LLMProvider
from ..contracts.conversation import ConversationContext

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def get_response(self, text: str, context: ConversationContext, token_callback=None, event_callback=None) -> str:
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
            response = "I am functioning at full capacity and ready to assist you. How can I help you?"
            if event_callback:
                await event_callback("assistant_start", content="")
            if token_callback:
                await token_callback(response)
            if event_callback:
                await event_callback("assistant_end", content=response)
            return response
            
        system_prompt = (
            "You are RedForge, a friendly, professional, and knowledgeable autonomous security assistant. "
            "You are having a casual conversation with the user. "
            "Provide natural, helpful, and concise responses. Do not request or require a target for general chat. "
            "If the user asks follow-up questions, use the conversation history to answer them. "
        )
        if context.active_target:
            system_prompt += f"The currently active target is {context.active_target}. "
            
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
                except Exception:
                    content = "Hello! I'm here to assist you with security testing. What would you like to do?"
        else:
            try:
                resp = await self.llm_provider.chat(messages)
                content = resp.content
            except Exception:
                content = "Hello! I'm here to assist you with security testing. What would you like to do?"
                
        if event_callback:
            await event_callback("assistant_end", content=content)
            
        return content
