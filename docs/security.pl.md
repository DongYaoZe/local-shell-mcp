<!-- i18n-source-sha256: 1f30fc9935125c84fb0838d17ec894d78aaa6253fe3903356414aac716ba2adc -->
# Bezpieczeństwo

W publicznych wdrożeniach używaj OAuth. Ustaw silne wartości `LOCAL_SHELL_MCP_OAUTH_ADMIN_PIN` i `LOCAL_SHELL_MCP_OAUTH_JWT_SECRET` oraz zachowuj je w tajemnicy.

Domyślnie operacje na ścieżkach są ograniczone do workspace, a wrażliwe fragmenty ścieżek są blokowane. Tryb Full-container wyłącza wbudowane ograniczenia workspace i ścieżek, dlatego jest przeznaczony wyłącznie do jednorazowych kontenerów lub maszyn wirtualnych.

Wygenerowane łącza do pobierania plików są publicznymi adresami bearer URL. Ich ochrona opiera się na tokenach o wysokiej entropii, TTL, opcjonalnych limitach liczby pobrań, opcjonalnych limitach rozmiaru oraz możliwości unieważnienia.
