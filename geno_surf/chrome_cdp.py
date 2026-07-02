"""Chromium control via the DevTools Protocol HTTP endpoints (stdlib only).

Talks to a Chromium launched with --remote-debugging-port=<PORT>. The HTTP
endpoints cover the MVP (list/open/close/focus tabs) with zero dependencies;
deeper control (navigation events, window arrangement) and native Tab Groups
(chrome.tabGroups — extension-only) are layered on later.
"""

import json
import subprocess
import urllib.request
from pathlib import Path

DEFAULT_PORT = 9222
# A dedicated agent profile keeps geno-surf's Chromium separate from human Safari.
AGENT_PROFILE = Path.home() / ".geno" / "surf" / "chrome-profile"
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Arc.app/Contents/MacOS/Arc",
]


def _base(port: int) -> str:
    return f"http://127.0.0.1:{port}"


def _get(url: str):
    with urllib.request.urlopen(url, timeout=5) as r:
        body = r.read().decode("utf-8", "ignore")
    return json.loads(body) if body.strip().startswith(("{", "[")) else body


def is_up(port: int = DEFAULT_PORT) -> bool:
    try:
        _get(f"{_base(port)}/json/version")
        return True
    except OSError:
        return False


def find_chrome() -> str | None:
    for p in CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def launch(port: int = DEFAULT_PORT) -> str:
    """Launch the agent's Chromium with remote debugging (idempotent)."""
    if is_up(port):
        return f"already up on :{port}"
    exe = find_chrome()
    if not exe:
        raise SystemExit(
            "No Chromium-family browser found. Install Chrome/Chromium/Brave/Arc.")
    AGENT_PROFILE.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(
        [exe, f"--remote-debugging-port={port}",
         f"--user-data-dir={AGENT_PROFILE}", "--no-first-run",
         "--no-default-browser-check"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return f"launched {Path(exe).stem} on :{port} (profile {AGENT_PROFILE})"


def list_tabs(port: int = DEFAULT_PORT) -> list[dict]:
    tabs = _get(f"{_base(port)}/json/list")
    return [t for t in tabs if t.get("type") == "page"]


def new_tab(url: str = "about:blank", port: int = DEFAULT_PORT) -> dict:
    return _get(f"{_base(port)}/json/new?{url}")


def activate_tab(target_id: str, port: int = DEFAULT_PORT) -> None:
    _get(f"{_base(port)}/json/activate/{target_id}")


def close_tab(target_id: str, port: int = DEFAULT_PORT) -> None:
    _get(f"{_base(port)}/json/close/{target_id}")
