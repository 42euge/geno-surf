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


def _req(url: str, method: str = "GET"):
    r = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(r, timeout=5) as resp:
        body = resp.read().decode("utf-8", "ignore")
    return json.loads(body) if body.strip().startswith(("{", "[")) else body


def _get(url: str):
    return _req(url, "GET")


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


def _browser_ws(port: int) -> str:
    return _get(f"{_base(port)}/json/version")["webSocketDebuggerUrl"]


def _ws_call(method: str, params: dict, port: int = DEFAULT_PORT) -> dict:
    """One browser-level CDP call over websocket (needs the `cdp` extra)."""
    from websocket import create_connection  # lazy: pip install 'geno-surf[cdp]'
    ws = create_connection(_browser_ws(port), timeout=5,
                           suppress_origin=True)
    try:
        ws.send(json.dumps({"id": 1, "method": method, "params": params}))
        return json.loads(ws.recv())
    finally:
        ws.close()


def new_tab(url: str = "about:blank", port: int = DEFAULT_PORT,
            background: bool = True) -> dict:
    """Open a tab. background=True (default) adds it WITHOUT raising/refocusing
    the window (via Target.createTarget). Falls back to the HTTP endpoint —
    which does steal focus — only if the `cdp` extra isn't installed."""
    try:
        r = _ws_call("Target.createTarget", {"url": url, "background": background}, port)
        return {"id": r.get("result", {}).get("targetId", "?"), "url": url}
    except ImportError:
        return _req(f"{_base(port)}/json/new?{url}", "PUT")


def activate_tab(target_id: str, port: int = DEFAULT_PORT) -> None:
    _get(f"{_base(port)}/json/activate/{target_id}")


def close_tab(target_id: str, port: int = DEFAULT_PORT) -> None:
    _get(f"{_base(port)}/json/close/{target_id}")
