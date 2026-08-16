<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST API

मुख्य interface `/mcp` पर MCP है। Health checks, file links और चुनी हुई service operations के लिए REST surface भी उपलब्ध है।

## Health

```http
GET /healthz
```

Server health और basic status लौटाता है।

## MCP

```http
POST /mcp
```

ChatGPT और अन्य MCP client द्वारा उपयोग किया जाने वाला Streamable HTTP MCP endpoint।

## REST के माध्यम से tool calls

REST tool calls एक समान success/error envelopes का उपयोग करते हैं। Validation errors raw framework exceptions के बजाय structured `ok: false` payload लौटाते हैं।

## Agent Skills

स्थिर Skills registry REST के माध्यम से भी उपलब्ध है:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Skill directories में बदलाव अगली call पर दिखाई देते हैं और MCP tool list को नहीं बदलते।

## File links

Tokenized file downloads built-in HTTP app से serve होते हैं। Links bearer URL हैं जिनमें TTL, वैकल्पिक maximum-download limit और revocation support है।

## Authentication

Public deployments में OAuth का उपयोग करना चाहिए। Development के लिए localhost bypass सक्षम किया जा सकता है, लेकिन unauthenticated public access असुरक्षित है।
