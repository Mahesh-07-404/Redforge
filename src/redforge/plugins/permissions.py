from typing import List

class PluginPermissionManager:
    @staticmethod
    def verify_permissions(required: List[str], granted: List[str]) -> bool:
        for perm in required:
            if perm not in granted:
                return False
        return True
