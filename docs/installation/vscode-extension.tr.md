<!-- i18n-source-sha256: db40797f92f76326aa62db50ac4bb293edb4248791806c2fb46477a65c3e73cc -->
# VS Code extension runtime

VS Code extension aynı `local-shell-mcp` server için launcher ve convenience UI’dır. Geçerli editor workspace için server process başlattığından bir runtime seçimidir.

ChatGPT connector’ın kendisi değildir. Web/app kullanımında ChatGPT yine public HTTPS `/mcp` endpoint’e bağlanır.

## Extension ne yapar

Extension:

- Geçerli VS Code workspace için `local-shell-mcp` başlatır.
- Server’ı stop/restart eder.
- Server output’u VS Code output channel’da gösterir.
- `/healthz` kontrol eder.
- MCP URL’yi copy eder.
- Workspace ve endpoint içeren ChatGPT setup prompt’u copy eder.

Extension server binary bundle etmez. `local-shell-mcp`yi ayrı install edin ve `PATH` içinde değilse extension’a executable path verin.

## Ne zaman kullanılır

Şu durumlarda bu runtime’ı kullanın:

- Genellikle VS Code folder’dan çalışmaya başlıyorsanız.
- Manual terminal command yerine button/command-palette flow istiyorsanız.
- Project dependencies host üzerinde zaten kuruluysa.
- Trusted repositories veya dar workspace üzerinde çalışıyorsanız.
- Modele yalnız bu workspace’i expose etmeyi kabul ediyorsanız.

Şu durumlarda Docker kullanın:

- Repository untrusted ise.
- Task arbitrary packages install edecekse.
- Broad preinstalled toolchain gerekiyorsa.
- Container recreate ile kolay reset istiyorsanız.
- Host account’tan daha temiz boundary istiyorsanız.

## Executable kurulumu

Bir server install method seçin:

```bash
pipx install local-shell-mcp
```

veya OS için release binary indirip `PATH` içine koyun.

Ardından VSIX release asset’i install edin:

```bash
code --install-extension local-shell-mcp-<version>.vsix
```

Alternatif olarak command palette içinde **Extensions: Install from VSIX...** kullanın.

## Extension settings

| Setting | Purpose | Typical value |
|---|---|---|
| `local-shell-mcp.executablePath` | Server executable path | `local-shell-mcp` or an absolute binary path |
| `local-shell-mcp.host` | Local server bind address | `127.0.0.1` for local-only, `0.0.0.0` only behind a controlled network/proxy |
| `local-shell-mcp.port` | Local server port | `8765` |
| `local-shell-mcp.workspaceRoot` | MCP’ye expose edilen workspace | İlk VS Code folder için empty veya explicit path |
| `local-shell-mcp.authMode` | Authentication mode | `oauth` for ChatGPT, `none` only for trusted localhost testing |
| `local-shell-mcp.publicBaseUrl` | Prompt/URL içine copy edilen public HTTPS origin | Tunnel/proxy origin such as `https://mcp.example.com` |
| `local-shell-mcp.oauthAdminPin` | OAuth authorization PIN | Public kullanım için strong random value |
| `local-shell-mcp.allowFullContainer` | Full-container behavior flag | Direct host usage için `false` tutun |
| `local-shell-mcp.extraEnv` | Server process extra environment | Yalnız project-specific safe values |

## Basic flow

1. VS Code’da project folder açın.
2. **local-shell-mcp: Start Server** çalıştırın.
3. Varsa **Show Server Status** veya **Check Health** çalıştırın.
4. Local MCP client için **Copy MCP URL**, ChatGPT için **Copy ChatGPT Setup Prompt** kullanın.
5. Endpoint’i client’a ekleyin.

Local endpoint genellikle:

```text
http://127.0.0.1:8765/mcp
```

Local clients için yararlıdır ancak ChatGPT web/app tarafından reachable değildir.

## ChatGPT ile kullanım

VS Code-launched server’ı ChatGPT’den kullanmak için local port önüne HTTPS tunnel veya reverse proxy ekleyin.

Örnek:

```text
ChatGPT
  -> https://your-public-host.example.com/mcp
  -> tunnel or reverse proxy
  -> 127.0.0.1:8765 on your machine
  -> VS Code-launched local-shell-mcp process
```

Set edin:

```text
local-shell-mcp.publicBaseUrl = https://your-public-host.example.com
local-shell-mcp.authMode = oauth
local-shell-mcp.oauthAdminPin = <strong pin>
```

ChatGPT için copied URL `/mcp` ile bitmeli:

```text
https://your-public-host.example.com/mcp
```

## Host-runtime safety

Extension commands’ı genellikle host user olarak çalıştırır. Bu disposable Docker container’dan önemli ölçüde farklıdır.

Önerilen kurallar:

- Yalnız modelin kontrol etmesini istediğiniz repository’yi açın.
- `allowFullContainer` kapalı tutun.
- Workspace root’u home directory yapmayın.
- Unrelated secrets workspace içinde tutmayın.
- Commit/push öncesi `secret_scan` kullanın.
- Unfamiliar repositories veya package-install-heavy tasks için Docker tercih edin.

## Common prompt

Setup prompt’u copy ettikten sonra read-only task ile başlayın:

```text
local-shell-mcp kullan. Önce environment_get ve workspace üzerinde file_tree çağır. Henüz dosyaları değiştirme.
```

Sonra bounded edit’e geçin:

```text
Bu workspace içindeki failing test’i düzelt. Önce relevant files oku, en küçük patch’i yap, targeted test çalıştır ve git diff göster. Ben onaylamadan commit yapma.
```

## Troubleshooting

| Belirti | Kontrol |
|---|---|
| Extension server başlatamıyor | `local-shell-mcp.executablePath` var ve terminalde `--help` çalışıyor mu doğrulayın |
| ChatGPT ulaşamıyor | Local `127.0.0.1` URL public değil; tunnel/proxy ve `publicBaseUrl` yapılandırın |
| Tools yanlış folder expose ediyor | `local-shell-mcp.workspaceRoot` explicit set edin |
| Restart sonrası auth bozuluyor | `extraEnv` veya runtime configuration ile stable OAuth admin PIN ve JWT secret set edin |
| Commands dependencies bulamıyor | Host üzerinde dependencies install edin veya Docker runtime’a geçin |
