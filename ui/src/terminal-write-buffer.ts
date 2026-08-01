export type TerminalWriteChunk = string | Uint8Array

type TerminalWriteBufferOptions = {
  maxPendingBytes?: number
  onOverflow?: () => void
}

export class TerminalWriteBuffer {
  private held = false
  private pending: TerminalWriteChunk[] = []
  private pendingBytes = 0
  private readonly maxPendingBytes: number
  private readonly onOverflow?: () => void

  constructor(
    private readonly writeNow: (chunk: TerminalWriteChunk) => void,
    options: TerminalWriteBufferOptions = {},
  ) {
    this.maxPendingBytes = Math.max(1, options.maxPendingBytes ?? 1_048_576)
    this.onOverflow = options.onOverflow
  }

  write(chunk: TerminalWriteChunk): void {
    if (!this.held) {
      this.writeNow(chunk)
      return
    }
    const buffered = typeof chunk === "string" ? chunk : chunk.slice()
    this.pending.push(buffered)
    this.pendingBytes += typeof buffered === "string" ? buffered.length * 2 : buffered.byteLength
    if (this.pendingBytes > this.maxPendingBytes) {
      this.held = false
      this.onOverflow?.()
      this.flush()
    }
  }

  setHeld(held: boolean): void {
    if (this.held === held) return
    this.held = held
    if (!held) this.flush()
  }

  clear(): void {
    this.pending = []
    this.pendingBytes = 0
  }

  private flush(): void {
    const pending = this.pending
    this.pending = []
    this.pendingBytes = 0
    for (const chunk of pending) this.writeNow(chunk)
  }
}
