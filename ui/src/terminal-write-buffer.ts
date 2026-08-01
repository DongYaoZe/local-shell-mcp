export type TerminalWriteChunk = string | Uint8Array

export class TerminalWriteBuffer {
  private held = false
  private pending: TerminalWriteChunk[] = []

  constructor(private readonly writeNow: (chunk: TerminalWriteChunk) => void) {}

  write(chunk: TerminalWriteChunk): void {
    if (!this.held) {
      this.writeNow(chunk)
      return
    }
    this.pending.push(typeof chunk === "string" ? chunk : chunk.slice())
  }

  setHeld(held: boolean): void {
    if (this.held === held) return
    this.held = held
    if (!held) this.flush()
  }

  clear(): void {
    this.pending = []
  }

  private flush(): void {
    const pending = this.pending
    this.pending = []
    for (const chunk of pending) this.writeNow(chunk)
  }
}
