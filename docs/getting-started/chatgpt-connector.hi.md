<!-- i18n-source-sha256: 2ad041876ff35987d7fdd66cbcdc7ed3956f427e8d8b185f354555cdc29a1b8a -->
# ChatGPT कनेक्टर

यह पेज ChatGPT को client connection के रूप में बताता है। यह runtime नहीं चुनता। इसे उपयोग करने से पहले Docker, VS Code extension, binary या Python install से server चलाएँ।

`local-shell-mcp` ChatGPT Developer Mode और पूर्ण MCP clients के लिए बनाया गया है। MCP endpoint सामान्य LSM tool surface को सीधे expose करता है।

## Runtime prerequisites

पहले एक runtime चुनकर शुरू करें:

| Runtime | पेज |
|---|---|
| Docker Compose | [Docker Compose runtime](../installation/docker.md) |
| VS Code extension | [VS Code extension runtime](../installation/vscode-extension.md) |
| Standalone binary | [Standalone binary runtime](../installation/binary.md) |
| Python / pipx / source | [Python runtimes](../installation/python.md) |

फिर उस runtime को ऐसे network path पर expose करें जिसे ChatGPT पहुँच सके। देखें [network connectivity](../clients/connectivity.md).

## Public URL

ChatGPT को server तक HTTPS से पहुँचना चाहिए। MCP endpoint है:

```text
https://your-public-host.example.com/mcp
```

सुनिश्चित करें कि `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` public origin से मेल खाता है:

```env
LOCAL_SHELL_MCP_PUBLIC_BASE_URL=https://your-public-host.example.com
```

`LOCAL_SHELL_MCP_PUBLIC_BASE_URL` में `/mcp` शामिल न करें।

## OAuth setup

अनुशंसित public settings:

```env
LOCAL_SHELL_MCP_AUTH_MODE=oauth
LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN=<long random value>
LOCAL_SHELL_MCP_OAUTH_JWT_SECRET=<long random value>
LOCAL_SHELL_MCP_OAUTH_ACCESS_TOKEN_TTL_S=0
```

Access tokens डिफ़ॉल्ट रूप से expire नहीं होते क्योंकि लंबे coding sessions छोटी token lifetime से अधिक हो सकते हैं। जरूरत होने पर JWT secret rotate करके या fresh state के साथ redeploy करके access revoke करें।

## Connector जोड़ना

1. ChatGPT connector या Developer Mode MCP settings खोलें।
2. Custom MCP server जोड़ें।
3. MCP URL डालें: `https://your-public-host.example.com/mcp`.
4. OAuth पूरा करें।
5. Tool surface approve करें।

## Live Workspace MCP App

MCP Apps समर्थित ChatGPT clients `local-shell-mcp` को interactive execution workspace के रूप में render कर सकते हैं। जब real-time visibility या human collaboration उपयोगी हो तो ChatGPT से Live Workspace एक बार खोलने को कहें; इसके बाद app बार-बार `workspace_open` कॉल के बिना खुद reconnect होता है।

Live Workspace जानबूझकर model reasoning से अलग है। यह observable execution state और shared resources दिखाता है:

- **Activity** MCP tool starts, completions, failures और human actions दिखाता है।
- **Terminal** मौजूदा persistent shell backend से जुड़कर live PTY output दिखाता है।
- **Files** local या remote workspace files browse, preview, edit, create और delete करता है।
- **Diff** staged और unstaged Git changes दिखाता है और current diff review के लिए ChatGPT को वापस भेज सकता है।
- **Jobs** managed jobs और persistent sessions दिखाता है।
- **Remotes** workers दिखाता है और remote support चालू होने पर invite, rename और revoke actions देता है।
- **Audit** हाल के structured MCP audit records दिखाता है।

Live Workspace हमेशा collaborative है: ChatGPT और human एक ही workspace को एक साथ बदल सकते हैं। Host समर्थन करे तो यह floating PiP-style window में खुलता है और fullscreen तथा windowed mode के बीच बदल सकता है। कोई अलग observe/takeover state नहीं है।

Files, diff, audit और activity views चुना हुआ operational context MCP Apps bridge के माध्यम से अगले model turn को भेज सकते हैं। यह स्पष्ट रूप से shared context है; UI private model reasoning को expose या reconstruct नहीं करता।

### Networking और security

Rendered MCP App low-latency terminal/event traffic के लिए अपने sandbox से configured service origin पर सीधे connect करता है। इसलिए `LOCAL_SHELL_MCP_PUBLIC_BASE_URL` वही HTTPS origin होना चाहिए जिसे ChatGPT browser पहुँच सके। MCP endpoint स्वयं `https://your-public-host.example.com/mcp` रहता है।

Workspace खोलने पर एक random, short-lived Live Workspace bearer token जारी होता है। Token केवल rendered app के लिए MCP result metadata में लौटता है, model-visible structured content में शामिल नहीं होता, और केवल human/live UI APIs द्वारा स्वीकार किया जाता है। उसी `live_id` पर automatic reattachment वर्तमान credential को reuse करता है ताकि reconnecting views एक-दूसरे को invalidate न करें; यह वर्तमान logical `session_id` भी साथ ले जाता है, इसलिए in-memory Live Workspace state खो जाने पर भी durable Session recover की जा सकती है। एक नया explicit `workspace_open` call credential को rotate करता है। Embedded app browser cookies या ambient credentials उपयोग नहीं करता।

MCP Apps लागू न करने वाले clients UI metadata को ignore कर सकते हैं। सभी सामान्य MCP data tools उपलब्ध रहते हैं और उनका behavior समान रहता है।

## पहला prompt

```text
local-shell-mcp का उपयोग करें। पहले environment_get कॉल करें, फिर workspace root सूचीबद्ध करें। अभी files संशोधित न करें।
```

यह बिना बदलाव connectivity जाँचता है।

## अनुशंसित operating rules

Model को स्पष्ट constraints दें:

- जब तक स्पष्ट रूप से कुछ और न कहा जाए, `/workspace` के अंदर काम करें।
- commit से पहले tests चलाएँ।
- push से पहले `secret_scan` उपयोग करें।
- `link_create` केवल सुरक्षित रूप से share की जा सकने वाली files के लिए उपयोग करें।
- लंबे processes के लिए persistent shell sessions को प्राथमिकता दें।
- Files बदलने वाले सभी commands का सार दें।

## Tool discovery समस्याएँ

यदि ChatGPT authenticate कर सकता है लेकिन अपेक्षित tools नहीं दिखते:

- सुनिश्चित करें endpoint `/mcp` पर समाप्त हो।
- `LOCAL_SHELL_MCP_REQUIRE_AUTH_FOR_MCP_DISCOVERY` जाँचें।
- reverse proxy headers और request body limits जाँचें।
- `docker compose logs --tail=200 local-shell-mcp` देखें।
- सुनिश्चित करें service `mcp` या `both` mode में है।

## सुरक्षा नोट्स

Public deployments में OAuth enabled रखें। Unauthenticated पूर्ण MCP tools को public Internet पर expose न करें। हर approved tool को connected model की effective authority का हिस्सा मानें।
