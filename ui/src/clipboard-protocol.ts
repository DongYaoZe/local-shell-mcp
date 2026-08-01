export const WEB_CLIPBOARD_OSC = 777

const WEB_CLIPBOARD_PREFIX = "local-shell-mcp;clipboard;"
const MAX_WEB_CLIPBOARD_PAYLOAD = 128_000

export function webClipboardSequence(value: string): string {
  return `\u001b]${WEB_CLIPBOARD_OSC};${WEB_CLIPBOARD_PREFIX}${encodeURIComponent(value)}\u0007`
}

export function parseWebClipboardPayload(data: string): string | null {
  if (!data.startsWith(WEB_CLIPBOARD_PREFIX)) return null
  const encoded = data.slice(WEB_CLIPBOARD_PREFIX.length)
  if (!encoded || encoded.length > MAX_WEB_CLIPBOARD_PAYLOAD) return null
  try {
    return decodeURIComponent(encoded)
  } catch {
    return null
  }
}
