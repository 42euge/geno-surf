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
# Bundled extension grants tabGroups; geno-surf drives it over CDP.
EXTENSION_DIR = Path(__file__).parent / "extension"
# Stable Google Chrome (137+) blocks --load-extension, so prefer automation
# builds that still allow it: Chrome for Testing (puppeteer install), Chromium, Brave.
CHROME_CANDIDATES = [
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Arc.app/Contents/MacOS/Arc",
]


def _chrome_for_testing() -> str | None:
    """Chrome for Testing installed via `@puppeteer/browsers` (allows extensions)."""
    import glob
    hits = glob.glob(str(Path.home() / "chrome" / "*" / "chrome-mac*" /
                         "Google Chrome for Testing.app" / "Contents" / "MacOS" /
                         "Google Chrome for Testing"))
    hits += glob.glob(str(Path.home() / ".cache" / "puppeteer" / "chrome" / "*" /
                          "chrome-mac*" / "*.app" / "Contents" / "MacOS" / "*"))
    return sorted(hits)[-1] if hits else None


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
    cft = _chrome_for_testing()
    if cft:
        return cft
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
    args = [exe, f"--remote-debugging-port={port}",
            f"--user-data-dir={AGENT_PROFILE}", "--no-first-run",
            "--no-default-browser-check"]
    if EXTENSION_DIR.is_dir():
        args += [f"--load-extension={EXTENSION_DIR}",
                 f"--disable-extensions-except={EXTENSION_DIR}"]
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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


def _sw_eval(expr: str, port: int = DEFAULT_PORT, wake_secs: float = 26.0):
    """Evaluate JS in the geno-surf extension's service worker (has chrome.tabGroups).

    Retries finding the SW target for up to wake_secs (the keepalive alarm wakes a
    dormant MV3 worker within its period). Returns the JS value (returnByValue).
    """
    import time
    from websocket import create_connection
    ver = _get(f"{_base(port)}/json/version")
    ws = create_connection(ver["webSocketDebuggerUrl"], timeout=10, suppress_origin=True)
    _id = 0
    def snd(method, params=None, sid=None):
        nonlocal _id; _id += 1
        m = {"id": _id, "method": method, "params": params or {}}
        if sid: m["sessionId"] = sid
        ws.send(json.dumps(m)); return _id
    def wait(i):
        while True:
            x = json.loads(ws.recv())
            if x.get("id") == i: return x
    try:
        wait(snd("Target.setDiscoverTargets", {"discover": True}))
        sw = None
        deadline = time.monotonic() + wake_secs
        while time.monotonic() < deadline:
            infos = wait(snd("Target.getTargets"))["result"]["targetInfos"]
            hit = [t for t in infos if t["type"] == "service_worker" and t["url"].endswith("sw.js")]
            if hit: sw = hit[0]; break
            time.sleep(0.5)
        if not sw:
            raise SystemExit("geno-surf extension service worker not found. "
                             "Is the agent Chrome for Testing running? (surf launch)")
        sid = wait(snd("Target.attachToTarget", {"targetId": sw["targetId"], "flatten": True}))["result"]["sessionId"]
        snd("Runtime.enable", sid=sid)
        r = wait(snd("Runtime.evaluate", {
            "expression": expr, "awaitPromise": True, "returnByValue": True}, sid=sid))
        det = r["result"].get("exceptionDetails")
        if det:
            raise SystemExit(f"tabGroups eval error: {det.get('text')}")
        return r["result"]["result"].get("value")
    finally:
        ws.close()


def list_groups(port: int = DEFAULT_PORT) -> list[dict]:
    return json.loads(_sw_eval("chrome.tabGroups.query({}).then(JSON.stringify)", port) or "[]")


def groups_with_tabs(port: int = DEFAULT_PORT) -> list[dict]:
    """Every native tab group with its member URLs: [{title, color, urls[]}]."""
    js = ("(async () => {"
          "  const gs = await chrome.tabGroups.query({});"
          "  const out = [];"
          "  for (const g of gs) {"
          "    const ts = await chrome.tabs.query({groupId: g.id});"
          "    out.push({title: g.title, color: g.color, urls: ts.map(t => t.url)});"
          "  }"
          "  return JSON.stringify(out);"
          "})()")
    return json.loads(_sw_eval(js, port) or "[]")


def open_in_group(url: str, group_title: str | None = None,
                  color: str = "blue", port: int = DEFAULT_PORT) -> dict:
    """Open a background tab; if group_title given, add it to that native tab group
    (created + titled if it doesn't exist). No window refocus (active:false)."""
    if not group_title:
        return new_tab(url, port)
    js = f"""(async () => {{
      const tab = await chrome.tabs.create({{url: {json.dumps(url)}, active: false}});
      const found = await chrome.tabGroups.query({{title: {json.dumps(group_title)}}});
      let gid;
      if (found.length) {{
        gid = found[0].id;
        await chrome.tabs.group({{groupId: gid, tabIds: [tab.id]}});
      }} else {{
        gid = await chrome.tabs.group({{tabIds: [tab.id]}});
        await chrome.tabGroups.update(gid, {{title: {json.dumps(group_title)}, color: {json.dumps(color)}}});
      }}
      return JSON.stringify({{tabId: tab.id, groupId: gid}});
    }})()"""
    return json.loads(_sw_eval(js, port) or "{}")


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
