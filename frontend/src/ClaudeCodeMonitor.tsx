import { useEffect, useMemo, useState } from 'react'

type Agent = {
  id: string
  kind: 'main' | 'subagent'
  status: 'working' | 'idle' | 'stopped'
  last_activity_at: string | null
  tool_calls: number
}

type MonitorSnapshot = {
  available: boolean
  agents: Agent[]
}

function formatTime(value: string | null) {
  if (!value) return 'нет событий'
  return new Intl.DateTimeFormat('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value))
}

function labelForStatus(status: Agent['status']) {
  if (status === 'working') return 'работает'
  if (status === 'stopped') return 'остановлен'
  return 'ожидает'
}

function ClaudeCodeMonitor() {
  const [snapshot, setSnapshot] = useState<MonitorSnapshot | null>(null)
  const [unavailable, setUnavailable] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function refresh() {
      try {
        const response = await fetch('/api/v1/agent-monitor/claude-code')
        if (!response.ok) throw new Error('monitor request failed')
        const nextSnapshot: MonitorSnapshot = await response.json()
        if (!cancelled) {
          setSnapshot(nextSnapshot)
          setUnavailable(false)
        }
      } catch {
        if (!cancelled) setUnavailable(true)
      }
    }

    void refresh()
    const timer = window.setInterval(() => void refresh(), 2000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [])

  const workingCount = useMemo(
    () => snapshot?.agents.filter((agent) => agent.status === 'working').length ?? 0,
    [snapshot],
  )

  return (
    <section className="agent-monitor" aria-live="polite">
      <div className="agent-monitor__heading">
        <p>Claude Code: <strong>{workingCount}</strong> в работе</p>
        <span>обновление каждые 2 секунды</span>
      </div>
      {unavailable && <p className="agent-monitor__notice">Монитор локального Claude Code недоступен.</p>}
      {!unavailable && snapshot && !snapshot.available && (
        <p className="agent-monitor__notice">Активная сессия Claude Code для этого проекта не найдена.</p>
      )}
      {snapshot?.available && (
        <ul className="agent-monitor__list">
          {snapshot.agents.map((agent) => (
            <li key={`${agent.kind}-${agent.id}`}>
              <span>{agent.kind === 'main' ? 'Основной агент' : `Агент ${agent.id.slice(0, 8)}`}</span>
              <span className={`agent-status agent-status--${agent.status}`}>{labelForStatus(agent.status)}</span>
              <span>{agent.tool_calls} вызовов · {formatTime(agent.last_activity_at)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default ClaudeCodeMonitor
