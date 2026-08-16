<!-- i18n-source-sha256: 91695da5acbb82a8550b150249a9b97f17470140a72b27233e2470a93305e7fb -->
# Otomasi browser

Tool browser menggunakan Playwright untuk memeriksa halaman, menangkap bukti, dan menjalankan workflow browser yang dapat direproduksi. Tool surface publik sengaja dibuat kecil.

## Tool

| Tool | Tujuan |
|---|---|
| `browser_session` | Memulai, membuat daftar, menutup, atau membersihkan sesi browser persisten; secara opsional menggunakan ulang profile atau storage state. |
| `browser_snapshot` | Membaca teks halaman terbatas, error page/network, dan elemen interaktif dengan ref pendek seperti `e1`; secara opsional mengambil screenshot. |
| `browser_act` | Menjalankan navigation, click, fill, select, key, wait, dan aksi multi-halaman secara terstruktur menggunakan snapshot ref atau CSS selector. |
| `browser_run_script` | Menjalankan script Python Playwright lengkap ketika kumpulan aksi tingkat tinggi tidak memadai. |

Semua tool browser menerima `machine` opsional. Dependensi browser harus sudah terpasang pada controller atau worker yang dipilih; pemasangan dilakukan dengan perintah shell biasa seperti `python -m playwright install chromium`.

## Alur umum

Untuk pekerjaan interaktif, panggil `browser_session(action="start", url=...)`, lalu `browser_snapshot`. Snapshot mengembalikan referensi singkat seperti `e1` dan `e2`; berikan ref tersebut langsung ke `browser_act`, misalnya `{"action": "click", "target": "e1"}` atau `{"action": "fill", "target": "e2", "value": "..."}`. Ambil snapshot baru setelah navigation karena element ref merupakan referensi state halaman, bukan selector permanen.

Untuk inspeksi biasa dan screenshot, prioritaskan `browser_session` plus `browser_snapshot`; snapshot dapat mengembalikan visible text terbatas dan menyimpan screenshot. Gunakan `browser_run_script` untuk JavaScript evaluation, logika capture/PDF khusus, atau interaksi yang tidak diwakili `browser_act`.

Batasi script, tetapkan timeout eksplisit, simpan artifact di bawah workspace, dan hindari memasukkan credential kecuali lingkungan memang didedikasikan untuk tugas tersebut.
