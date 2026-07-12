"""RedForge CLI Entry Point.

Provides a simplified command-line interface for the single autonomous agent.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence

from redforge.core.agent import RedForgeAgent


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="RedForge - Autonomous Intent-Based Cybersecurity Agent"
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Natural language request (e.g. 'Scan example.com', 'Analyze this APK')",
    )
    parser.add_argument(
        "--mode",
        "-m",
        help="Deprecated mode selection (for backward compatibility)",
    )
    parser.add_argument(
        "--target",
        "-t",
        help="Target for the operation (for backward compatibility)",
    )

    args = parser.parse_args(argv)

    # Check for deprecated mode options
    if args.mode:
        mode_val = args.mode.lower()
        target_val = args.target or (" ".join(args.query) if args.query else "")

        print(
            "Warning: The '--mode' argument is deprecated. "
            "RedForge now operates as a single autonomous agent.",
            file=sys.stderr,
        )

        if mode_val == "bugbounty":
            new_query = f"Scan {target_val}" if target_val else "Scan target"
        elif mode_val == "ctf":
            new_query = f"Solve CTF challenge {target_val}" if target_val else "Solve CTF challenge"
        elif mode_val == "learning":
            new_query = f"Explain {target_val}" if target_val else "Explain security concept"
        elif mode_val == "research":
            new_query = f"Research {target_val}" if target_val else "Research target"
        elif mode_val == "report":
            new_query = (
                f"Generate a report on {target_val}" if target_val else "Generate security report"
            )
        elif mode_val == "android":
            new_query = f"Analyze APK {target_val}" if target_val else "Analyze APK"
        else:
            new_query = f"Process request {target_val}" if target_val else "Process request"

        print(f"Automatically converting to: '{new_query}'", file=sys.stderr)
        query_str = new_query
    else:
        query_str = " ".join(args.query) if args.query else ""

    if not query_str:
        parser.print_help()
        return 1

    agent = RedForgeAgent()
    try:
        state = asyncio.run(agent.run(query_str))
        if state.error:
            print(f"Error: {state.error}", file=sys.stderr)
            return 1
        # Print final assistant messages
        assistant_msgs = [m for m in state.messages if m.get("role") == "assistant"]
        if assistant_msgs:
            print(assistant_msgs[-1]["content"])
        else:
            print("Execution completed.")
        return 0
    except Exception as e:
        print(f"Execution failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
