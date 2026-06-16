import re

with open("src/redforge/core/agent.py", "r") as f:
    content = f.read()

# Replace LangGraph usage with a simple while loop
graph_loop = """
        result = initial_state
        try:
            is_approved = user_input.strip().startswith("[APPROVED]")
            if is_approved:
                next_step = "execute_node"
            else:
                result = self._merge_state(result, await self.plan_node(result))
                next_step = self._route_after_plan(result)

            while True:
                if next_step == "await_confirmation":
                    result = self._merge_state(result, await self.await_confirmation_node(result))
                    break

                if next_step == "execute_node":
                    result = self._merge_state(result, await self.execute_node(result))
                    next_step = self._route_after_execute(result)
                    continue

                if next_step == "verify_node":
                    result = self._merge_state(result, await self.verify_node(result))
                    next_step = self._route_after_verify(result)
                    continue

                if next_step == "store_node":
                    result = self._merge_state(result, await self.store_node(result))
                    next_step = "report_node"
                    continue

                if next_step == "report_node":
                    result = self._merge_state(result, await self.report_node(result))
                    break

                if next_step == "handle_error":
                    result = self._merge_state(result, await self.handle_error_node(result))
                    break

                # Fallback break to prevent infinite loop
                break
        except Exception as exc:
            error_state = result.model_dump()
            error_state["error"] = str(exc)
            result = AgentState(**error_state)
            result = self._merge_state(result, await self.handle_error_node(result))
"""

if graph_loop not in content:
    print("Graph loop not found")

