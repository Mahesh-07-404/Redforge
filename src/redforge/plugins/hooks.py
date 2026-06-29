from typing import Callable, Dict, List

class PluginHooks:
    def __init__(self):
        self.hooks: Dict[str, List[Callable]] = {
            "before_plan": [],
            "after_plan": [],
            "before_execution": [],
            "after_execution": [],
            "before_report": [],
            "after_report": []
        }

    def register_hook(self, hook_name: str, callback: Callable):
        if hook_name in self.hooks:
            self.hooks[hook_name].append(callback)

    def trigger_hook(self, hook_name: str, *args, **kwargs):
        if hook_name in self.hooks:
            for cb in self.hooks[hook_name]:
                try:
                    cb(*args, **kwargs)
                except Exception:
                    pass
