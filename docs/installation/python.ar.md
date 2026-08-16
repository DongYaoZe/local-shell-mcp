<!-- i18n-source-sha256: 19347ba1d8d3f26f227506397f4093281319e6a2a59833ced1da286c1d46f21a -->
# Python وpipx وsource runtimes

تفيد Python runtimes في التطوير وتصحيح الأخطاء والبيئات التي تكون فيها إدارة حزم Python أسهل من Docker. وهي تشغّل server نفسه الذي تشغله Docker وbinary runtimes.

استخدم هذه الصفحة لثلاث حالات مترابطة:

- `pipx install local-shell-mcp`: تثبيت executable على مستوى المستخدم.
- `pip install local-shell-mcp`: تثبيت داخل virtual environment موجودة.
- Editable source checkout: تطوير المشروع نفسه أو تصحيح أخطائه.

## تثبيت pipx

`pipx` هو أنظف تثبيت قائم على Python للمستخدم العادي لأنه يمنح command بيئة virtual environment خاصة به مع إتاحة executable على `PATH`.

```bash
pipx install local-shell-mcp
local-shell-mcp --help
```

شغّل HTTP MCP server محلياً:

```bash
mkdir -p ~/local-shell-mcp-workspace
export LOCAL_SHELL_MCP_WORKSPACE_ROOT=~/local-shell-mcp-workspace
local-shell-mcp --mode mcp
```

تحقق من الصحة:

```bash
curl -i http://127.0.0.1:8765/healthz
```

## التثبيت في virtual environment

استخدم هذا عندما تدير Python environments بنفسك:

```bash
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install local-shell-mcp
local-shell-mcp --mode mcp
```

يستخدم process الأدوات المثبتة على host. لا تثبّت Python package لك compilers أو Git أو browser system dependencies أو project dependencies.

## Editable source checkout

استخدمه لتطوير المشروع:

```bash
git clone https://github.com/fwerkor/local-shell-mcp.git
cd local-shell-mcp
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev,docs]'
LOCAL_SHELL_MCP_WORKSPACE_ROOT=/tmp/local-shell-mcp-workspace local-shell-mcp --mode mcp
```

شغّل الفحوص:

```bash
ruff check .
pytest -q
mkdocs build --strict
```

## إعداد المتصفح

تعتمد Python package على Playwright، لكن قد تحتاج browser binaries إلى التثبيت على host:

```bash
python -m playwright install chromium
```

تحتاج بعض Linux hosts إلى browser dependencies إضافية. يتجنب Docker معظم ذلك لأن image تبدأ من Playwright base image.

## الاستخدام العام لـ HTTP MCP

لـ ChatGPT أو public HTTP MCP client آخر، اضبط إعدادات public origin وOAuth نفسها كبقية HTTP runtimes، ثم اكشف local port عبر reverse proxy أو tunnel.

MCP endpoint العام هو:

```text
https://your-public-host.example.com/mcp
```

## Development modes

| Mode | Command | الاستخدام |
|---|---|---|
| MCP HTTP | `local-shell-mcp --mode mcp` | MCP clients كاملة عبر HTTP، بما فيها ChatGPT خلف HTTPS |
| REST-style HTTP | `local-shell-mcp --mode http` | Diagnostic أو compatibility endpoints، وليس المسار الرئيسي لـ ChatGPT |
| stdio | `local-shell-mcp --mode stdio` | MCP clients محلية تشغّل process |

`mode=both` محجوز ولا ينبغي حالياً استخدامه كـ mode لعملية واحدة.

## أمان host runtime

تعمل Python installs بصلاحيات host user ما لم تضعها في VM/container. أبقِ workspace ضيقاً وfull-container mode معطلاً، ولا تجعل workspace يشير إلى home directory.

استخدم Docker Compose مع repositories غير الموثوقة أو tasks كثيفة package manager أو workflows التي تكون فيها resetability أهم من host integration.
