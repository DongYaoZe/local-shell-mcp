export const WEB_CLIPBOARD_OSC = 777

const WEB_CLIPBOARD_SET_PREFIX = "local-shell-mcp;clipboard;set;"
const WEB_CLIPBOARD_CLEAR_PAYLOAD = "local-shell-mcp;clipboard;clear"
const MAX_WEB_CLIPBOARD_PAYLOAD = 128_000

export type WebClipboardPayload =
  | { type: "set"; value: string }
  | { type: "clear" }

export function webClipboardSequence(value: string): string {
  return `\u001b]${WEB_CLIPBOARD_OSC};${WEB_CLIPBOARD_SET_PREFIX}${encodeURIComponent(value)}\u0007`
}

export function webClipboardClearSequence(): string {
  return `\u001b]${WEB_CLIPBOARD_OSC};${WEB_CLIPBOARD_CLEAR_PAYLOAD}\u0007`
}

export function parseWebClipboardPayload(data: string): WebClipboardPayload | null {
  if (data === WEB_CLIPBOARD_CLEAR_PAYLOAD) return { type: "clear" }
  if (!data.startsWith(WEB_CLIPBOARD_SET_PREFIX)) return null
  const encoded = data.slice(WEB_CLIPBOARD_SET_PREFIX.length)
  if (!encoded || encoded.length > MAX_WEB_CLIPBOARD_PAYLOAD) return null
  try {
    return { type: "set", value: decodeURIComponent(encoded) }
  } catch {
    return null
  }
}
