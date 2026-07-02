---
name: geno-surf-tabs-ls
description: >-
  List the agent Chromium's open tabs (id, title, url) via the DevTools Protocol.
allowed-tools: "Bash(surf *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# surf tabs/ls

```
surf ls
```

Lists open tabs in the agent's Chromium (id · title · url). Requires `surf launch` first (Chromium with remote debugging under its own profile). Safari is not touched.
