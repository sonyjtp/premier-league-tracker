import React, { useState, useEffect } from 'react'
import { X, Zap, Users, BarChart2 } from 'lucide-react'

interface MatchEvent {
  minute: number | null
  extra_minute: number | null
  event_type: string
  detail: string | null
  team_name: string | null
  player_name: string | null
  assist_name: string | null
}

interface LineupPlayer {
  name: string
  shirt_number: number | null
  position: string | null
  grid: string | null
  is_starter: boolean
}

interface TeamLineup {
  team_name: string
  formation: string | null
  starters: LineupPlayer[]
  substitutes: LineupPlayer[]
}

interface Analytics {
  home_xg: number | null
  away_xg: number | null
  home_possession: number | null
  away_possession: number | null
  home_ppda: number | null
  away_ppda: number | null
}

interface Props {
  fixtureId: number
  onClose: () => void
}

type Tab = 'events' | 'lineups' | 'analytics'

function eventIcon(type: string, detail: string | null) {
  if (type === 'Goal')  return detail?.includes('Penalty') ? '⚽ (P)' : '⚽'
  if (type === 'Card')  return detail?.includes('Yellow') ? '🟨' : '🟥'
  if (type === 'subst') return '↔'
  if (type === 'Var')   return '📺'
  return '•'
}

export const MatchDetailModal: React.FC<Props> = ({ fixtureId, onClose }) => {
  const [events,    setEvents]    = useState<MatchEvent[]>([])
  const [lineups,   setLineups]   = useState<TeamLineup[]>([])
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [tab,       setTab]       = useState<Tab>('events')
  const [loading,   setLoading]   = useState(true)

  useEffect(() => {
    Promise.allSettled([
      fetch(`/api/fixtures/${fixtureId}/events`).then(r => r.json()),
      fetch(`/api/fixtures/${fixtureId}/lineups`).then(r => r.json()),
      fetch(`/api/fixtures/${fixtureId}/analytics`).then(r => r.json()),
    ]).then(([e, l, a]) => {
      setEvents(e.status === 'fulfilled' && Array.isArray(e.value) ? e.value : [])
      setLineups(l.status === 'fulfilled' && Array.isArray(l.value) ? l.value : [])
      if (a.status === 'fulfilled' && a.value && !a.value.detail) setAnalytics(a.value)
      setLoading(false)
    })
  }, [fixtureId])

  const TABS: { id: Tab; label: string; Icon: React.FC<any> }[] = [
    { id: 'events',    label: 'Events',    Icon: Zap },
    { id: 'lineups',   label: 'Lineups',   Icon: Users },
    { id: 'analytics', label: 'Analytics', Icon: BarChart2 },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-2xl max-h-[85vh] flex flex-col glass-card rounded-2xl border border-white/10 overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
          <h2 className="font-black text-white text-lg">Match Details</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1.5 hover:bg-white/5 rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab bar */}
        <div className="flex gap-1 px-3 py-2 border-b border-white/5 bg-slate-900/40">
          {TABS.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                tab === id ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex justify-center py-16">
              <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : tab === 'events' ? (
            events.length > 0 ? (
              <div className="space-y-2">
                {events.map((ev, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/40 border border-white/5">
                    <span className="text-base leading-none mt-0.5 w-6 text-center">
                      {eventIcon(ev.event_type, ev.detail)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline gap-2 flex-wrap">
                        {ev.minute != null && (
                          <span className="text-xs font-black text-slate-400 shrink-0">
                            {ev.minute}{ev.extra_minute != null ? `+${ev.extra_minute}` : ''}'
                          </span>
                        )}
                        <span className="text-sm font-bold text-white truncate">{ev.player_name ?? '—'}</span>
                        {ev.assist_name && (
                          <span className="text-xs text-slate-500">({ev.assist_name})</span>
                        )}
                      </div>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        {ev.team_name}{ev.detail ? ` · ${ev.detail}` : ''}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-12 text-sm">No events available for this fixture.</p>
            )
          ) : tab === 'lineups' ? (
            lineups.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {lineups.map((team, i) => (
                  <div key={i} className="space-y-3">
                    <div>
                      <h3 className="font-black text-white">{team.team_name}</h3>
                      {team.formation && (
                        <span className="text-xs text-slate-500 font-mono">{team.formation}</span>
                      )}
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">Starting XI</p>
                      <div className="space-y-1">
                        {team.starters.map((p, j) => (
                          <div key={j} className="flex items-center gap-3 text-xs p-2 rounded-lg bg-slate-900/50">
                            <span className="w-5 text-right font-mono font-bold text-slate-500">{p.shirt_number ?? '—'}</span>
                            <span className="flex-1 font-semibold text-white">{p.name}</span>
                            <span className="text-slate-600 font-mono text-[10px]">{p.position ?? ''}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    {team.substitutes.length > 0 && (
                      <div>
                        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">Substitutes</p>
                        <div className="space-y-1 opacity-60">
                          {team.substitutes.map((p, j) => (
                            <div key={j} className="flex items-center gap-3 text-xs p-2 rounded-lg">
                              <span className="w-5 text-right font-mono font-bold text-slate-500">{p.shirt_number ?? '—'}</span>
                              <span className="flex-1 text-slate-300">{p.name}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-12 text-sm">Lineups not yet available.</p>
            )
          ) : (
            analytics ? (
              <div className="space-y-8">
                {analytics.home_xg != null && analytics.away_xg != null && (
                  <StatBar
                    label="Expected Goals (xG)"
                    homeVal={analytics.home_xg}
                    awayVal={analytics.away_xg}
                    fmt={v => v.toFixed(2)}
                  />
                )}
                {analytics.home_possession != null && analytics.away_possession != null && (
                  <StatBar
                    label="Possession %"
                    homeVal={analytics.home_possession}
                    awayVal={analytics.away_possession}
                    fmt={v => `${v.toFixed(0)}%`}
                  />
                )}
                {analytics.home_ppda != null && analytics.away_ppda != null && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      PPDA (passes per def. action — lower = more pressing)
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      {[
                        { label: 'Home', val: analytics.home_ppda, color: 'text-indigo-400' },
                        { label: 'Away', val: analytics.away_ppda, color: 'text-rose-400' },
                      ].map(({ label, val, color }) => (
                        <div key={label} className="text-center p-4 bg-slate-900/40 rounded-xl border border-white/5">
                          <p className={`text-2xl font-black ${color}`}>{val?.toFixed(1)}</p>
                          <p className="text-xs text-slate-500 mt-1">{label} PPDA</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-12 text-sm">
                Analytics not yet available — they are synced after the match completes.
              </p>
            )
          )}
        </div>
      </div>
    </div>
  )
}

function StatBar({
  label, homeVal, awayVal, fmt,
}: {
  label: string
  homeVal: number
  awayVal: number
  fmt: (v: number) => string
}) {
  const total   = homeVal + awayVal
  const homePct = total > 0 ? (homeVal / total) * 100 : 50
  return (
    <div className="space-y-2">
      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">{label}</h4>
      <div className="flex items-center gap-4">
        <span className="text-2xl font-black text-white w-16 text-right">{fmt(homeVal)}</span>
        <div className="flex-1 flex h-3 rounded-full overflow-hidden gap-0.5">
          <div className="bg-indigo-500 h-full rounded-l-full transition-all" style={{ width: `${homePct}%` }} />
          <div className="bg-rose-500 h-full rounded-r-full transition-all" style={{ width: `${100 - homePct}%` }} />
        </div>
        <span className="text-2xl font-black text-white w-16">{fmt(awayVal)}</span>
      </div>
      <div className="flex justify-between text-[10px] text-slate-500 font-semibold px-0.5">
        <span>Home</span>
        <span>Away</span>
      </div>
    </div>
  )
}
