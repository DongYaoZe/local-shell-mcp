<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# Keamanan

Gunakan OAuth untuk deployment publik. Pastikan `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` dan `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` kuat dan tetap rahasia.

Secara default, operasi path dibatasi pada workspace dan fragmen path sensitif diblokir. Mode Full-container menonaktifkan pembatasan workspace dan path bawaan, sehingga hanya ditujukan untuk container atau VM yang dapat dibuang.

Tautan unduhan file yang dibuat merupakan bearer URL publik. Keamanannya bergantung pada token berentropi tinggi, TTL, batas jumlah unduhan opsional, batas ukuran opsional, dan pencabutan.
