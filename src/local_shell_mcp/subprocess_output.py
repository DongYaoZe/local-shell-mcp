from __future__ import annotations

import locale


def _native_text_encoding() -> str:
    """Return the OS text encoding without being overridden by Python UTF-8 mode."""

    getter = getattr(locale, "getencoding", None)
    if getter is not None:
        return str(getter())
    return locale.getpreferredencoding(False)


def decode_subprocess_output(data: bytes) -> str:
    """Decode shell output that may contain UTF-8 and native-code-page lines.

    PowerShell emits UTF-8 through redirected pipes on current Windows builds, while
    cmd.exe and locale-mode Python commonly emit the active ANSI/OEM code page. Decode
    each line independently so a composed shell command can safely contain both.
    """

    if not data:
        return ""

    fallback = _native_text_encoding()
    encodings = ["utf-8"]
    if fallback.casefold().replace("_", "-") not in {"utf-8", "utf8"}:
        encodings.append(fallback)

    decoded: list[str] = []
    for part in data.splitlines(keepends=True):
        for encoding in encodings:
            try:
                decoded.append(part.decode(encoding))
                break
            except (LookupError, UnicodeDecodeError):
                continue
        else:
            decoded.append(part.decode("utf-8", errors="replace"))
    return "".join(decoded)
