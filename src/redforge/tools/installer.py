"""Verification and installation logic for security tools in RedForge."""

import shutil
import logging
import subprocess
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ToolInstaller:
    """Checks and handles installation of external system tools."""

    def is_installed(self, cmd: str) -> bool:
        """Check if command is available on PATH."""
        return shutil.which(cmd) is not None

    def install(self, tool_name: str) -> bool:
        """Simulate or attempt automated installation of a tool."""
        if self.is_installed(tool_name):
            logger.info(f"Tool {tool_name} is already installed.")
            return True

        # Clean automated installer for common security tools (requires root or fails gracefully)
        logger.info(f"Attempting to install {tool_name}...")
        try:
            # Check for apt (Debian/Ubuntu)
            if shutil.which("apt-get"):
                res = subprocess.run(
                    ["sudo", "apt-get", "update", "-y"], 
                    capture_output=True, 
                    text=True, 
                    timeout=60
                )
                res = subprocess.run(
                    ["sudo", "apt-get", "install", "-y", tool_name], 
                    capture_output=True, 
                    text=True, 
                    timeout=180
                )
                if res.returncode == 0:
                    logger.info(f"Successfully installed {tool_name} via apt.")
                    return True
            logger.warning(f"No compatible package manager found or sudo authorization failed for {tool_name}.")
        except Exception as e:
            logger.error(f"Failed to install tool {tool_name}: {e}")

        return False
