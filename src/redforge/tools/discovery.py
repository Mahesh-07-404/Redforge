import os
import shutil

from .platform import detect_platform


class ToolDiscovery:
    @staticmethod
    def find_binary(binary_name: str) -> str | None:
        path = shutil.which(binary_name)
        if path:
            return path

        plat = detect_platform()
        for p in plat.default_paths:
            full_path = os.path.join(p, binary_name)
            if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                return full_path
        return None

    @staticmethod
    def get_version(binary_path: str) -> str:
        # Avoid execution of tools. Return static version.
        return "1.0.0"
