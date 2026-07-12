class PluginPermissionManager:
    @staticmethod
    def verify_permissions(required: list[str], granted: list[str]) -> bool:
        for perm in required:
            if perm not in granted:
                return False
        return True
