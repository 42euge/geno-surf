// Keep the service worker attachable via CDP: an alarm re-wakes it periodically,
// and touching an API on each wake resets the idle timer. geno-surf drives
// chrome.tabs.group / chrome.tabGroups.* by evaluating in this context over CDP.
chrome.runtime.onInstalled.addListener(() => chrome.alarms.create("ka", { periodInMinutes: 0.4 }));
chrome.runtime.onStartup.addListener(() => chrome.alarms.create("ka", { periodInMinutes: 0.4 }));
chrome.alarms.onAlarm.addListener(() => chrome.tabs.query({}, () => {}));
chrome.runtime.onMessage.addListener(() => true);
