import React, { useState, useEffect, useRef } from 'react'
import { Search, X, User, Shield } from 'lucide-react'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface PlayerResult {
  type: 'player'
  id: number
  first_name: string
  second_name: string
  position: string
}

export interface TeamResult {
  type: 'team'
  id: number
  name: string
  short_name: string
  api_football_id: number | null
}

export type SearchResult = PlayerResult | TeamResult

interface Props {
  onSelectPlayer: (player: PlayerResult) => void
  onSelectTeam:   (team:   TeamResult)   => void
  onClose:        () => void
  excludePlayerIds?: number[]
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const POS_STYLE: Record<string, string> = {
  GK:  'text-amber-400  bg-amber-400/10  border-amber-400/20',
  DEF: 'text-blue-400   bg-blue-400/10   border-blue-400/20',
  MID: 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20',
  FWD: 'text-rose-400   bg-rose-400/10   border-rose-400/20',
}

// ── Component ─────────────────────────────────────────────────────────────────

export const PlayerSearchModal: React.FC<Props> = ({
  onSelectPlayer, onSelectTeam, onClose, excludePlayerIds = [],
}) => {
  const [query,   setQuery]   = useState('')
  const [players, setPlayers] = useState<PlayerResult[]>([])
  const [teams,   setTeams]   = useState<TeamResult[]>([])
  const [loading, setLoading] = useState(false)
  const inputRef              = useRef<HTMLInputElement>(null)

  useEffect(() => { inputRef.current?.focus() }, [])

  useEffect(() => {
    const q = query.trim()
    if (q.length < 2) { setPlayers([]); setTeams([]); return }

    setLoading(true)
    const enc = encodeURIComponent(q)

    Promise.all([
      fetch(`/api/players?query=${enc}`).then(r => r.json()),
      fetch(`/api/teams?query=${enc}`).then(r => r.json()),
    ])
      .then(([playerData, teamData]) => {
        setPlayers(
          (Array.isArray(playerData) ? playerData : [])
            .filter((p: any) => !excludePlayerIds.includes(p.id))
            .map((p: any): PlayerResult => ({ type: 'player', id: p.id, first_name: p.first_name, second_name: p.second_name, position: p.position }))
        )
        setTeams(
          (Array.isArray(teamData) ? teamData : [])
            .map((t: any): TeamResult => ({ type: 'team', id: t.id, name: t.name, short_name: t.short_name, api_football_id: t.api_football_id }))
        )
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [query])

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onClose])

  const hasResults   = players.length > 0 || teams.length > 0
  const queryTooShort = query.trim().length < 2

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[8vh] px-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

      <div
        className="relative w-full max-w-lg glass-card rounded-2xl border border-white/10 shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-white/5">
          <Search className="w-4 h-4 text-slate-500 shrink-0" />
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search players or teams…"
            className="flex-1 bg-transparent text-slate-200 text-sm outline-none placeholder:text-slate-600"
          />
          {loading
            ? <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin shrink-0" />
            : <button onClick={onClose} className="text-slate-500 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors shrink-0">
                <X className="w-4 h-4" />
              </button>
          }
        </div>

        {/* Results */}
        <div className="max-h-[60vh] overflow-y-auto">
          {queryTooShort ? (
            <p className="text-slate-600 text-sm text-center py-10 px-5">
              Type at least 2 characters to search players and teams
            </p>
          ) : !hasResults && !loading ? (
            <p className="text-slate-500 text-sm text-center py-10 px-5">
              No results for "<span className="text-slate-300">{query}</span>"
            </p>
          ) : (
            <>
              {/* Teams section */}
              {teams.length > 0 && (
                <div>
                  <p className="px-5 pt-4 pb-2 text-[10px] font-bold uppercase tracking-widest text-slate-600">
                    Teams
                  </p>
                  {teams.map(team => (
                    <button
                      key={team.id}
                      onClick={() => { onSelectTeam(team); onClose() }}
                      className="w-full flex items-center gap-3 px-5 py-3 hover:bg-white/5 transition-colors border-b border-white/[0.04] last:border-0 text-left"
                    >
                      <div className="w-9 h-9 rounded-full bg-slate-800 flex items-center justify-center shrink-0">
                        <Shield className="w-4 h-4 text-slate-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-white text-sm truncate">{team.name}</p>
                        <p className="text-[11px] text-slate-500">Premier League</p>
                      </div>
                      <span className="text-[10px] font-bold text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full border border-white/5 shrink-0">
                        Team
                      </span>
                    </button>
                  ))}
                </div>
              )}

              {/* Players section */}
              {players.length > 0 && (
                <div>
                  <p className="px-5 pt-4 pb-2 text-[10px] font-bold uppercase tracking-widest text-slate-600">
                    Players
                  </p>
                  {players.map(player => (
                    <button
                      key={player.id}
                      onClick={() => { onSelectPlayer(player); onClose() }}
                      className="w-full flex items-center gap-3 px-5 py-3 hover:bg-white/5 transition-colors border-b border-white/[0.04] last:border-0 text-left"
                    >
                      <div className="w-9 h-9 rounded-full bg-slate-800 flex items-center justify-center shrink-0">
                        <User className="w-4 h-4 text-slate-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-white text-sm truncate">
                          {player.first_name} {player.second_name}
                        </p>
                      </div>
                      <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full border shrink-0 ${POS_STYLE[player.position] ?? 'text-slate-400 bg-slate-800 border-white/5'}`}>
                        {player.position}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer hint */}
        <div className="px-5 py-2.5 border-t border-white/5 bg-slate-900/30 flex items-center gap-4 text-[11px] text-slate-600">
          <span><kbd className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-500 border border-white/5">↵</kbd> select</span>
          <span><kbd className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-500 border border-white/5">Esc</kbd> close</span>
        </div>
      </div>
    </div>
  )
}
