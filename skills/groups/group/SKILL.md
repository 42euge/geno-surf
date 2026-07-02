---
name: geno-surf-groups-group
description: >-
  Group tabs under an object-notation node (native Chrome tab groups — phase 2, extension).
allowed-tools: "Bash(surf *)"
metadata:
  author: 42euge
  version: "0.1.0"
---

# surf groups/group

```
surf group <program.area.aspect> …
```

Groups tabs under an object-notation node. Chrome's native Tab Groups are the `chrome.tabGroups` extension API (not in the DevTools Protocol), so this ships in phase 2 with the bundled geno-surf extension + native-messaging bridge.
