window.__ModuleLoader__.load({
  id: 'local-shell-mcp-dsh',
  factory: (require) => {
    const module = { exports: {} }
    const exports = module.exports
    const React = require('react')

    const inject = ['slots', 'sessions', 'conversation']

    function LiveWorkspaceView({ sessionId, sendPrompt }) {
      const frameRef = React.useRef(null)
      const [loadError, setLoadError] = React.useState('')

      React.useEffect(() => {
        const onMessage = async (event) => {
          const frame = frameRef.current
          if (!frame || event.source !== frame.contentWindow || event.origin !== window.location.origin) return
          const data = event.data
          if (!data || data.type !== 'local-shell-mcp:dsh:prompt' || String(data.sessionId || '') !== String(sessionId)) return
          const requestId = String(data.requestId || '')
          try {
            await sendPrompt(String(data.text || ''))
            frame.contentWindow?.postMessage({
              type: 'local-shell-mcp:dsh:prompt-result',
              requestId,
              ok: true,
            }, window.location.origin)
          } catch (error) {
            frame.contentWindow?.postMessage({
              type: 'local-shell-mcp:dsh:prompt-result',
              requestId,
              ok: false,
              message: error instanceof Error ? error.message : String(error),
            }, window.location.origin)
          }
        }
        window.addEventListener('message', onMessage)
        return () => window.removeEventListener('message', onMessage)
      }, [sessionId, sendPrompt])

      const source = `/lsm/live-workspace?session=${encodeURIComponent(String(sessionId))}`
      return React.createElement(
        'div',
        {
          style: {
            width: '100%',
            height: 'calc(100dvh - 118px)',
            minHeight: '520px',
            overflow: 'hidden',
            background: 'var(--dsw-alias-bg-base, transparent)',
          },
        },
        loadError
          ? React.createElement('div', {
              style: {
                padding: '24px',
                color: 'var(--dsw-alias-label-secondary, currentColor)',
                fontSize: '13px',
              },
            }, `Live Workspace failed to load: ${loadError}`)
          : React.createElement('iframe', {
              ref: frameRef,
              src: source,
              title: 'local-shell-mcp Live Workspace',
              referrerPolicy: 'no-referrer',
              style: {
                width: '100%',
                height: '100%',
                display: 'block',
                border: 0,
                background: 'transparent',
              },
              onError: () => setLoadError('iframe navigation failed'),
            }),
      )
    }

    function apply(ctx) {
      ctx.slots.inject('conversation.view', () => ctx.slots.register({
        name: 'conversation.view',
        id: 'lsm-live-workspace',
        order: 20,
        label: 'Live Workspace',
        inject: (sessionId) => ({
          sendPrompt: async (text) => {
            if (!text.trim()) return
            const scoped = ctx.sessions.scope(sessionId)
            if (!scoped) throw new Error(`DSH session "${String(sessionId)}" is unavailable`)
            await scoped.conversation.send(text)
          },
        }),
      }, LiveWorkspaceView))
    }

    exports.inject = inject
    exports.apply = apply
    exports.LiveWorkspaceView = LiveWorkspaceView
    return module.exports
  },
})
