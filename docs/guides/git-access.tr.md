<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Git erişimi

`local-shell-mcp`, standart Git CLI’yi `run_shell`, `shell_start` veya `job_start` üzerinden kullanır. Özel Git MCP wrapper’ları kasıtlı olarak sunulmaz: CLI eksiksizdir, coding agent’lara tanıdıktır ve her Git alt komutunu araç listesinde yeniden tanımlamayı önler.

## Yaygın workflow

Mümkün olduğunda sınırlı, etkileşimsiz komutlar kullanın:

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

Tipik agent sırası:

1. `run_shell(command="git status --short --branch")` ile inceleyin.
2. Yalnızca ilgili dosyaları okuyup düzenleyin.
3. Hedefli testleri çalıştırın.
4. `run_shell(command="git diff --check && git diff")` ile gözden geçirin.
5. Commit veya push öncesinde `secret_scan` çalıştırın.
6. Açık Git CLI komutlarıyla stage, commit ve push yapın.

Repository bir remote worker üzerindeyse aynı shell tool içinde `machine` kullanın.

## Kimlik bilgileri

Docker deployments, yaygın Git credential konumlarını `/persist/credentials` altında kalıcı tutabilir. Bu volume’ü hassas kabul edin. Repository-scoped deploy keys, kısa ömürlü GitHub App tokens, izole automation users ve push öncesi manuel review tercih edin.

## Commit hijyeni

Commit’leri odaklı tutun, oluşturulan cache ve build artifact’ları dışarıda bırakın, çalıştırılan testleri kaydedin ve ilgisiz değişiklikleri stage etmeyin. Reset, clean veya force-push gibi yıkıcı komutlarda önce tam hedefi inceleyin.

## Sorun giderme

`git push` başarısız olursa remote URL, credential persistence, branch protection ve token izinlerini kontrol edin. GitHub CLI yüklüyse `gh auth status` yararlıdır.
