import React, { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { ArrowLeft, User, X, Plus } from 'lucide-react'
import { PlayerSearchModal } from './PlayerSearchModal'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Player {
  id: number
  first_name: string
  second_name: string
  position: string
  current_fpl_id: number | null
}

interface PlayerProfile {
  photo_url: string | null
  nationality: string | null
  height: string | null
  weight: string | null
}

interface SeasonSummary {
  season_label: string
  minutes: number
  goals: number
  assists: number
  clean_sheets: number
  yellow_cards: number
  red_cards: number
  fpl_points: number
}

interface MatchStat {
  gameweek: number
  opponent_name: string
  minutes: number
  goals: number
  assists: number
  clean_sheets: number
  yellow_cards: number
  red_cards: number
  fpl_points: number
}

interface PlayerDetail {
  player: Player
  profile: PlayerProfile | null
  team_name: string | null
  summaries: SeasonSummary[]
  recent_stats: MatchStat[]
}

interface Props {
  playerId: number
  onBack: () => void
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const COLORS = ['#6366f1', '#f43f5e']

const POS_STYLE: Record<string, string> = {
  GK:  'bg-amber-400/10  text-amber-400  border-amber-400/20',
  DEF: 'bg-blue-400/10   text-blue-400   border-blue-400/20',
  MID: 'bg-indigo-400/10 text-indigo-400 border-indigo-400/20',
  FWD: 'bg-rose-400/10   text-rose-400   border-rose-400/20',
}

function total(summaries: SeasonSummary[], key: keyof SeasonSummary): number {
  return summaries.reduce((s, x) => s + ((x[key] as number) ?? 0), 0)
}

function PlayerAvatar({ profile, player, color }: { profile: PlayerProfile | null; player: Player; color: string }) {
  return profile?.photo_url ? (
    <img src={profile.photo_url} alt={player.first_name} className="w-20 h-20 rounded-full object-cover border-4 border-white/10 shrink-0" style={{ borderColor: color + '40' }} />
  ) : (
    <div className="w-20 h-20 rounded-full bg-slate-800 flex items-center justify-center shrink-0" style={{ borderColor: color + '40', borderWidth: 4, borderStyle: 'solid' }}>
      <User className="w-10 h-10 text-slate-600" />
    </div>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export const PlayerPage: React.FC<Props> = ({ playerId, onBack }) => {
  const [players,    setPlayers]    = useState<PlayerDetail[]>([])
  const [loading,    setLoading]    = useState(true)
  const [searchOpen, setSearchOpen] = useState(false)

  const fetchPlayer = async (ids: number[]) => {
    setLoading(true)
    const res  = await fetch(`http://localhost:8000/api/players/compare?ids=${ids.join(',')}`)
    const data = await res.json()
    setPlayers(Array.isArray(data) ? data : [])
    setLoading(false)
  }

  useEffect(() => { fetchPlayer([playerId]) }, [playerId])

  const addComparePlayer = (p: { id: number }) => {
    if (players.length >= 2) return
    const ids = [playerId, p.id]
    fetchPlayer(ids)
  }

  const removeCompare = () => fetchPlayer([playerId])

  const isComparing = players.length === 2

  // ── Build chart data ────────────────────────────────────────────────────────

  const fplChartData = (() => {
    const allSeasons = [...new Set(players.flatMap(pd => pd.summaries.map(s => s.season_label)))].sort()
    return allSeasons.map(season => {
      const row: Record<string, unknown> = { season }
      players.forEach(pd => {
        const s = pd.summaries.find(x => x.season_label === season)
        row[`${pd.player.first_name} ${pd.player.second_name}`] = s?.fpl_points ?? 0
      })
      return row
    })
  })()

  const goalsChartData = (() => {
    const allSeasons = [...new Set(players.flatMap(pd => pd.summaries.map(s => s.season_label)))].sort()
    return allSeasons.map(season => {
      const row: Record<string, unknown> = { season }
      players.forEach(pd => {
        const s = pd.summaries.find(x => x.season_label === season)
        const name = `${pd.player.first_name} ${pd.player.second_name}`
        row[`${name} Goals`] = s?.goals ?? 0
        row[`${name} Assists`] = s?.assists ?? 0
      })
      return row
    })
  })()

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-40 gap-4">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 text-sm">Loading player data…</p>
      </div>
    )
  }

  if (players.length === 0) {
    return <div className="text-center py-40 text-slate-500">Player not found.</div>
  }

  return (
    <div className="space-y-6">
      {/* Back */}
      <button onClick={onBack} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors group">
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
        Back
      </button>

      {/* Player header cards */}
      <div className={`grid gap-4 ${isComparing ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'}`}>
        {players.map((pd, idx) => (
          <div key={pd.player.id} className="glass-card p-5 rounded-2xl border border-white/5 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1" style={{ backgroundColor: COLORS[idx] }} />

            {idx === 1 && (
              <button onClick={removeCompare} className="absolute top-4 right-4 text-slate-500 hover:text-rose-400 transition-colors p-1.5 hover:bg-white/5 rounded-lg">
                <X className="w-4 h-4" />
              </button>
            )}

            <div className="flex items-start gap-4 mt-1">
              <PlayerAvatar profile={pd.profile} player={pd.player} color={COLORS[idx]} />
              <div className="flex-1 min-w-0">
                <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full border ${POS_STYLE[pd.player.position] ?? ''}`}>
                  {pd.player.position}
                </span>
                <div className="mt-1">
                  <p className="text-xs text-slate-400 font-semibold">{pd.player.first_name}</p>
                  <h2 className="text-3xl font-black text-white leading-tight">
                    {pd.player.second_name}
                  </h2>
                </div>
                <div className="mt-2 space-y-0.5">
                  {pd.team_name && (
                    <p className="text-sm font-semibold text-indigo-300">{pd.team_name}</p>
                  )}
                  {pd.profile?.nationality && (
                    <p className="text-xs text-slate-500">{pd.profile.nationality}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Career totals */}
            <div className="grid grid-cols-4 gap-2 mt-4 pt-4 border-t border-white/5">
              {[
                { label: 'Goals',  value: total(pd.summaries, 'goals') },
                { label: 'Assists',value: total(pd.summaries, 'assists') },
                { label: 'CS',     value: total(pd.summaries, 'clean_sheets') },
                { label: 'Points', value: total(pd.summaries, 'fpl_points') },
              ].map(({ label, value }) => (
                <div key={label} className="text-center bg-slate-900/40 rounded-xl p-2.5 border border-white/5">
                  <p className="text-[10px] text-slate-500 font-bold uppercase">{label}</p>
                  <p className="text-lg font-black text-white mt-0.5">{value}</p>
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Add comparison card */}
        {!isComparing && (
          <button
            onClick={() => setSearchOpen(true)}
            className="glass-card p-5 rounded-2xl border border-dashed border-white/10 flex flex-col items-center justify-center gap-3 text-slate-500 hover:border-indigo-500/40 hover:text-indigo-400 transition-all min-h-[180px] group"
          >
            <div className="w-12 h-12 rounded-full bg-slate-800 group-hover:bg-indigo-500/10 flex items-center justify-center transition-colors border border-white/5 group-hover:border-indigo-500/20">
              <Plus className="w-5 h-5" />
            </div>
            <div className="text-center">
              <p className="font-semibold text-sm">Compare with another player</p>
              <p className="text-xs text-slate-600 mt-0.5">Search and add a second player</p>
            </div>
          </button>
        )}
      </div>

      {/* Season stats table */}
      {(() => {
        const allSeasons = [...new Set(players.flatMap(pd => pd.summaries.map(s => s.season_label)))].sort().reverse()
        return (
          <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
            <div className="px-5 py-4 border-b border-white/5 bg-slate-900/40">
              <h3 className="font-bold text-white text-sm">Season by Season</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/5 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    <th className="py-3 px-4">Season</th>
                    {players.map((pd, idx) => (
                      <React.Fragment key={pd.player.id}>
                        <th colSpan={7} className="py-3 px-4 text-center space-y-0" style={{ color: COLORS[idx] }}>
                          <div className="text-xs font-semibold opacity-75">{pd.player.first_name}</div>
                          <div className="text-sm font-black">{pd.player.second_name}</div>
                        </th>
                      </React.Fragment>
                    ))}
                  </tr>
                  <tr className="border-b border-white/5 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    <th className="py-3 px-4" />
                    {players.map(() => (
                      <React.Fragment key={`header-${Math.random()}`}>
                        <th className="py-3 px-2 text-center">Min</th>
                        <th className="py-3 px-2 text-center">Goals</th>
                        <th className="py-3 px-2 text-center">Ast</th>
                        <th className="py-3 px-2 text-center hidden sm:table-cell">CS</th>
                        <th className="py-3 px-2 text-center hidden sm:table-cell">YC</th>
                        <th className="py-3 px-2 text-center">FPL</th>
                        <th className="py-3 px-2" />
                      </React.Fragment>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04] text-slate-300">
                  {allSeasons.map(season => (
                    <tr key={season} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-4 font-semibold text-slate-300 whitespace-nowrap">{season}</td>
                      {players.map((pd) => {
                        const s = pd.summaries.find(x => x.season_label === season)
                        return (
                          <React.Fragment key={`${pd.player.id}-${season}`}>
                            <td className="py-3 px-2 text-center tabular-nums text-slate-400">{s ? s.minutes.toLocaleString() : '—'}</td>
                            <td className="py-3 px-2 text-center font-bold text-emerald-400 tabular-nums">{s?.goals || '—'}</td>
                            <td className="py-3 px-2 text-center font-bold text-blue-400 tabular-nums">{s?.assists || '—'}</td>
                            <td className="py-3 px-2 text-center tabular-nums hidden sm:table-cell text-slate-400">{s?.clean_sheets || '—'}</td>
                            <td className="py-3 px-2 text-center tabular-nums hidden sm:table-cell text-amber-400/80">{s?.yellow_cards || '—'}</td>
                            <td className="py-3 px-2 text-center font-black text-indigo-400 tabular-nums">{s?.fpl_points || '—'}</td>
                            <td className="py-3 px-2 border-r border-white/5" />
                          </React.Fragment>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      })()}

      {/* FPL Points chart */}
      {fplChartData.length > 0 && (
        <div className="glass-card p-5 rounded-2xl border border-white/5 h-64 flex flex-col">
          <h3 className="font-bold text-white text-sm mb-4">FPL Points by Season</h3>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={fplChartData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="season" stroke="#64748b" fontSize={10} fontWeight={600} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={10} fontWeight={600} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px', fontSize: '12px' }} />
                {isComparing && <Legend />}
                {players.map((pd, idx) => (
                  <Bar key={pd.player.id} dataKey={`${pd.player.first_name} ${pd.player.second_name}`} fill={COLORS[idx]} radius={[4, 4, 0, 0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Goals & Assists chart */}
      {goalsChartData.length > 0 && (
        <div className="glass-card p-5 rounded-2xl border border-white/5 h-64 flex flex-col">
          <h3 className="font-bold text-white text-sm mb-4">Goals & Assists by Season</h3>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={goalsChartData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="season" stroke="#64748b" fontSize={10} fontWeight={600} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={10} fontWeight={600} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px', fontSize: '12px' }} />
                <Legend />
                {players.flatMap((pd, idx) => {
                  const name = `${pd.player.first_name} ${pd.player.second_name}`
                  return [
                    <Bar key={`${pd.player.id}-g`} dataKey={`${name} Goals`} fill={COLORS[idx]} radius={[4, 4, 0, 0]} />,
                    <Bar key={`${pd.player.id}-a`} dataKey={`${name} Assists`} fill={COLORS[idx]} fillOpacity={0.4} radius={[4, 4, 0, 0]} />,
                  ]
                })}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent match stats */}
      {isComparing && players.some(pd => pd.recent_stats.length > 0) && (
        <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
          <div className="px-5 py-4 border-b border-white/5 bg-slate-900/40">
            <h3 className="font-bold text-white text-sm">Recent Matches</h3>
          </div>
          <div className="space-y-6 p-5">
            {players.map((pd, idx) => (
              <div key={pd.player.id} className="border-b border-white/5 pb-6 last:border-0 last:pb-0">
                <div className="mb-3" style={{ color: COLORS[idx] }}>
                  <p className="text-[10px] font-semibold uppercase tracking-wider opacity-75">{pd.player.first_name}</p>
                  <p className="text-sm font-black uppercase tracking-wider">{pd.player.second_name}</p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-white/5 text-[10px] font-bold uppercase tracking-wider text-slate-600">
                        <th className="py-2 px-3 text-center">GW</th>
                        <th className="py-2 px-3">Opponent</th>
                        <th className="py-2 px-3 text-center">Min</th>
                        <th className="py-2 px-3 text-center">G</th>
                        <th className="py-2 px-3 text-center">A</th>
                        <th className="py-2 px-3 text-center text-indigo-400">Pts</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.04] text-slate-300">
                      {pd.recent_stats.map((r, ridx) => (
                        <tr key={ridx} className="hover:bg-white/[0.02] transition-colors">
                          <td className="py-2 px-3 text-center text-slate-500 tabular-nums">{r.gameweek}</td>
                          <td className="py-2 px-3 text-indigo-400 font-semibold">{r.opponent_name}</td>
                          <td className="py-2 px-3 text-center tabular-nums">{r.minutes}</td>
                          <td className="py-2 px-3 text-center font-bold text-emerald-400 tabular-nums">{r.goals || '—'}</td>
                          <td className="py-2 px-3 text-center font-bold text-blue-400 tabular-nums">{r.assists || '—'}</td>
                          <td className="py-2 px-3 text-center font-black text-indigo-400 tabular-nums">{r.fpl_points}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent match stats (single player) */}
      {!isComparing && players.some(pd => pd.recent_stats.length > 0) && (
        <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
          <div className="px-5 py-4 border-b border-white/5 bg-slate-900/40">
            <h3 className="font-bold text-white text-sm">Recent Matches</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <th className="py-3 px-4 text-center">GW</th>
                  <th className="py-3 px-3">Opponent</th>
                  <th className="py-3 px-3 text-center">Min</th>
                  <th className="py-3 px-3 text-center">G</th>
                  <th className="py-3 px-3 text-center">A</th>
                  <th className="py-3 px-3 text-center text-indigo-400">Pts</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04] text-slate-300">
                {players[0].recent_stats.map((r, ridx) => (
                  <tr key={ridx} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-center text-slate-500 tabular-nums">{r.gameweek}</td>
                    <td className="py-3 px-3 text-indigo-400 font-semibold">{r.opponent_name}</td>
                    <td className="py-3 px-3 text-center tabular-nums">{r.minutes}</td>
                    <td className="py-3 px-3 text-center font-bold text-emerald-400 tabular-nums">{r.goals || '—'}</td>
                    <td className="py-3 px-3 text-center font-bold text-blue-400 tabular-nums">{r.assists || '—'}</td>
                    <td className="py-3 px-3 text-center font-black text-indigo-400 tabular-nums">{r.fpl_points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Compare search modal */}
      {searchOpen && (
        <PlayerSearchModal
          excludePlayerIds={players.map(pd => pd.player.id)}
          onSelectPlayer={addComparePlayer}
          onSelectTeam={() => {}}
          onClose={() => setSearchOpen(false)}
        />
      )}
    </div>
  )
}
