from typing import cast

from ..contracts.conversation import ConversationContext
from ..contracts.intent import IntentType, ParsedIntent


class IntentRouter:
    def __init__(self, conversation_mgr, session_service, report_engine, pipeline_runner=None):
        self.conversation_mgr = conversation_mgr
        self.session_service = session_service
        self.report_engine = report_engine
        self.pipeline_runner = pipeline_runner

    async def _respond(self, response: str, token_callback, event_callback) -> str:
        if event_callback:
            await event_callback("assistant_start", content="")
        if token_callback:
            await token_callback(response)
        if event_callback:
            await event_callback("assistant_end", content=response)
        return response

    async def route(
        self,
        intent: ParsedIntent,
        context: ConversationContext,
        token_callback=None,
        event_callback=None,
    ) -> str:
        intent_type = intent.intent_type

        if intent_type == IntentType.GENERAL_CHAT:
            return cast(
                str,
                await self.conversation_mgr.get_response(
                    intent.raw_input, context, token_callback, event_callback
                ),
            )

        elif intent_type == IntentType.SESSION:
            raw_input = intent.raw_input.lower()
            if "continue" in raw_input or "load" in raw_input or "yesterday" in raw_input:
                sessions = self.session_service.list()
                if sessions:
                    last_sess_dict = sessions[0]
                    loaded_session = self.session_service.load(last_sess_dict["id"])
                    context.active_session = loaded_session
                    context.active_target = loaded_session.target
                    response = f"Session {loaded_session.id[:8]} loaded successfully."
                else:
                    new_sess = self.session_service.create(
                        mode="autonomous", target=None, autonomy="manual"
                    )
                    context.active_session = new_sess
                    response = f"No previous session found. Started new session {new_sess.id[:8]}."
            else:
                response = "Session Manager active. Please specify if you want to load, list, or delete a session."
            return await self._respond(response, token_callback, event_callback)

        elif intent_type == IntentType.REPORT:
            if not context.active_target:
                response = "Report generation requires an active target. Please set a target first."
            else:
                response = f"Report subsystem ready for target {context.active_target}."
            return await self._respond(response, token_callback, event_callback)

        elif intent_type in (
            IntentType.PENTEST,
            IntentType.BUG_BOUNTY,
            IntentType.CTF,
            IntentType.SCAN,
            IntentType.RECON,
            IntentType.EXPLOIT,
        ):
            target = intent.target or context.active_target
            if not target:
                response = "Please specify a target for this security task (e.g. 'on example.com')."
                return await self._respond(response, token_callback, event_callback)

            raw_lower = intent.raw_input.lower()
            if "safe command" in raw_lower or "scan the target" in raw_lower:
                if self.pipeline_runner:
                    return cast(str, await self.pipeline_runner(intent))

            response = f"Recognized security task: {intent_type.value.upper()} on {target}. Ready for execution."
            return await self._respond(response, token_callback, event_callback)

        elif intent_type == IntentType.HELP:
            response = "RedForge Help: Supported commands include scanning, reconnaissance, exploiting, session management, and report generation."
            return await self._respond(response, token_callback, event_callback)

        elif intent_type == IntentType.TOOL:
            response = "Tool Manager: Ready to execute safety-checked commands."
            return await self._respond(response, token_callback, event_callback)

        elif intent_type == IntentType.CONFIG:
            response = "Configuration Engine: Access settings via config.yaml."
            return await self._respond(response, token_callback, event_callback)

        else:
            response = "I'm not sure I understood your request. Could you please clarify if you want to run a security task, manage a session, or chat?"
            return await self._respond(response, token_callback, event_callback)
