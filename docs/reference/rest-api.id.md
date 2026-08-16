<!-- i18n-source-sha256: 87dd7fb66311534dcd5a7217bba8c809f71fe6189e8c39b3e265da923cc82d22 -->
# REST API

Interface utama adalah MCP di `/mcp`. REST surface juga tersedia untuk health check, file link, dan operasi layanan tertentu.

## Kesehatan

```http
GET /healthz
```

Mengembalikan kesehatan server dan status dasar.

## MCP

```http
POST /mcp
```

Endpoint MCP Streamable HTTP yang digunakan ChatGPT dan MCP client lainnya.

## Pemanggilan tool melalui REST

Pemanggilan tool REST menggunakan envelope sukses/error yang konsisten. Error validasi mengembalikan payload terstruktur `ok: false`, bukan exception framework mentah.

## Agent Skills

Registry Skills tetap juga tersedia melalui REST:

```text
GET  /tools/skill_list
POST /tools/skill_load       {"name": "debugging"}
POST /tools/skill_read  {"name": "debugging", "path": "checklist.md"}
```

Perubahan direktori Skill terlihat pada panggilan berikutnya dan tidak mengubah daftar tool MCP.

## Tautan file

Unduhan file bertoken dilayani oleh aplikasi HTTP bawaan. Tautannya berupa bearer URL dengan TTL, batas maksimum unduhan opsional, dan dukungan pencabutan.

## Autentikasi

Deployment publik sebaiknya menggunakan OAuth. Bypass localhost dapat diaktifkan untuk pengembangan, tetapi akses publik tanpa autentikasi tidak aman.
