<!-- i18n-source-sha256: 3b7d6ab07c5d6bad2bfb22f366893819ac8de8754c7c28bcb35f24ea5695979c -->
# Akses Git

`local-shell-mcp` menggunakan Git CLI standar melalui `run_shell`, `shell_start`, atau `job_start`. Wrapper Git MCP khusus sengaja tidak diekspos: CLI lengkap, familiar bagi coding agent, dan menghindari duplikasi setiap subcommand Git dalam daftar tool.

## Workflow umum

Gunakan perintah terbatas dan non-interaktif bila memungkinkan:

```bash
git status --short --branch
git diff --stat
git diff
git add -- path/to/file
git commit -m "fix: concise description"
git push origin HEAD
```

Urutan agent yang umum:

1. Inspeksi dengan `run_shell(command="git status --short --branch")`.
2. Baca dan edit hanya file yang relevan.
3. Jalankan test yang ditargetkan.
4. Tinjau dengan `run_shell(command="git diff --check && git diff")`.
5. Jalankan `secret_scan` sebelum commit atau push.
6. Lakukan stage, commit, dan push dengan perintah Git CLI eksplisit.

Gunakan `machine` pada shell tool yang sama ketika repository berada di remote worker.

## Credential

Deployment Docker dapat mempertahankan lokasi credential Git umum di `/persist/credentials`. Perlakukan volume tersebut sebagai sensitif. Prioritaskan deploy key dengan cakupan repository, token GitHub App berumur pendek, pengguna automation terisolasi, dan review manual sebelum push.

## Kebersihan commit

Jaga commit tetap fokus, abaikan cache hasil generasi dan build artifact, catat test yang dijalankan, dan hindari stage perubahan yang tidak terkait. Untuk perintah destruktif seperti reset, clean, atau force-push, periksa target persis terlebih dahulu.

## Pemecahan masalah

Ketika `git push` gagal, periksa remote URL, persistensi credential, branch protection, dan izin token. `gh auth status` berguna jika GitHub CLI terpasang.
