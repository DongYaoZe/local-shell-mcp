<!-- i18n-source-sha256: d758caead1c922385409aceebf498662f25f4cbf252a48d65b29d91f07e5a173 -->
# File links

`local-shell-mcp` controlled workspace की files को high-entropy bearer URL के माध्यम से expose कर सकता है। यह तब उपयोगी है जब AI reports, archives, PDFs, screenshots या अन्य artifacts बनाता है जिन्हें chat से download या उसमें display करना हो।

## File links कब उपयोग करें

File links उपयोग करें:

- Generated PDFs या reports.
- Screenshots और browser artifacts.
- Build outputs.
- ऐसे logs जो paste करने के लिए बहुत बड़े हों।
- Manual inspection के लिए तैयार archives.

Secrets, private keys, credential stores या unrelated personal data के लिए file links उपयोग न करें।

## सामान्य flow

1. `/workspace` के अंदर file generate या locate करें।
2. TTL और वैकल्पिक download limit के साथ `link_create` call करें। जब file को browser या Markdown image में सीधे render करना हो तब `inline=true` सेट करें; default `false` है, जो attachment download force करता है।
3. Returned URL share करें।
4. आवश्यकता समाप्त होने पर link revoke करें।

## संबंधित tools

| Tool | उद्देश्य |
|---|---|
| `link_create` | Workspace file के लिए tokenized URL बनाना। |
| `link_list` | Active links दिखाना। |
| `link_revoke` | Expiry से पहले link disable करना। |

## Controls

Configuration options में शामिल हैं:

- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_ENABLED`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_TTL_S`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_DEFAULT_MAX_DOWNLOADS`
- `LOCAL_SHELL_MCP_FILE_DOWNLOAD_MAX_FILE_BYTES`

Sensitive artifacts के लिए छोटे TTL उपयोग करें और जब link केवल एक recipient के लिए हो तो maximum download count सेट करें।

## Security notes

File links bearer URL होते हैं। URL वाला कोई भी व्यक्ति file को expiry, download limit तक पहुँचने या revocation तक download कर सकता है। इन्हें temporary secrets की तरह मानें। Inline responses में CSP sandbox और `X-Content-Type-Options: nosniff` होते हैं ताकि active formats LSM origin तक न पहुँच सकें या unsandboxed same-origin content की तरह execute न हों।
