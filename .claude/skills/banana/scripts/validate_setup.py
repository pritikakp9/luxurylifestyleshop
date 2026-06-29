#!/usr/bin/env python3
"""
Validate that the Banana Claude MCP server is properly configured.

Recognizes both supported setups:
  1. User scope    -- ~/.claude/settings.json  (written by setup_mcp.py)
  2. Project scope -- ./.mcp.json               (committed, key via env var)

Checks:
1. An MCP entry for nanobanana-mcp exists in one of those configs
2. An API key is resolvable (literal in config, or GOOGLE_AI_API_KEY env)
3. Node.js/npx is available
4. Output directory exists or can be created

Usage:
    python3 validate_setup.py
"""

import json
import os
import shutil
import sys
from pathlib import Path

def _find_project_mcp() -> Path:
    """Locate the project .mcp.json by walking up from this script's directory,
    then from the current working directory. Falls back to cwd/.mcp.json."""
    starts = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    for start in starts:
        for parent in [start, *start.parents]:
            candidate = parent / ".mcp.json"
            if candidate.exists():
                return candidate
    return Path.cwd() / ".mcp.json"


USER_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
PROJECT_MCP_PATH = _find_project_mcp()
MCP_NAME = "nanobanana-mcp"
OUTPUT_DIR = Path.home() / "Documents" / "nanobanana_generated"


def check(label: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    msg = f"  [{status}] {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    return passed


def _load_servers(path: Path) -> dict:
    """Return the mcpServers mapping from a config file, or {} on any problem."""
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    servers = data.get("mcpServers", {})
    return servers if isinstance(servers, dict) else {}


def _resolve_api_key(env: dict) -> str:
    """Resolve the API key from an MCP env block, expanding ${GOOGLE_AI_API_KEY}."""
    raw = env.get("GOOGLE_AI_API_KEY", "")
    if not raw or raw.startswith("${"):
        # Placeholder or unset -- fall back to the actual environment variable.
        return os.environ.get("GOOGLE_AI_API_KEY", "")
    return raw


def main() -> int:
    print("Banana Claude -- Setup Validation")
    print("=" * 40)
    results = []

    # 1. Locate the MCP entry in either supported config.
    sources = [
        ("project .mcp.json", PROJECT_MCP_PATH),
        ("user settings.json", USER_SETTINGS_PATH),
    ]
    mcp = None
    found_in = None
    for label, path in sources:
        servers = _load_servers(path)
        if MCP_NAME in servers:
            mcp = servers[MCP_NAME]
            found_in = f"{label} ({path})"
            break

    results.append(check(
        f"MCP server '{MCP_NAME}' configured",
        mcp is not None,
        found_in or f"not found in {PROJECT_MCP_PATH} or {USER_SETTINGS_PATH}",
    ))

    if mcp is not None:
        # 2. Command is npx
        results.append(check(
            "Command is 'npx'",
            mcp.get("command") == "npx",
            mcp.get("command", "(missing)"),
        ))

        # 3. Package is correct
        args = mcp.get("args", [])
        results.append(check(
            "Package is @ycse/nanobanana-mcp",
            "@ycse/nanobanana-mcp" in args,
            str(args),
        ))

        # 4. API key resolvable (literal in config or via env var)
        env = mcp.get("env", {})
        if not isinstance(env, dict):
            env = {}
        key = _resolve_api_key(env)
        results.append(check(
            "Google AI API key is resolvable",
            bool(key),
            f"{key[:8]}...{key[-4:]}" if len(key) > 12
            else "(set GOOGLE_AI_API_KEY env var or a literal key in config)",
        ))

        # 5. Model configured (optional -- package has a default)
        model = env.get("NANOBANANA_MODEL", "")
        results.append(check(
            "NANOBANANA_MODEL is set",
            bool(model),
            model or "(not set, will use package default)",
        ))

    # 6. Node.js/npx available
    results.append(check(
        "npx is available in PATH",
        shutil.which("npx") is not None,
        shutil.which("npx") or "not found",
    ))

    # 7. Output directory
    if OUTPUT_DIR.exists():
        results.append(check("Output directory exists", True, str(OUTPUT_DIR)))
    else:
        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            results.append(check("Output directory created", True, str(OUTPUT_DIR)))
        except OSError as e:
            results.append(check("Output directory writable", False, str(e)))

    # Summary
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n{'=' * 40}")
    print(f"Results: {passed}/{total} checks passed")

    if passed == total:
        print("Status: Ready to generate images!")
        return 0
    print("Status: Some checks failed. Fix the issues above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
