import React, { useState, useEffect, useRef } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Search, Plus, Trash2, User, Users } from 'lucide-react'
import { useSettings } from '../contexts/SettingsContext'

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
}

interface PlayerSeasonSummary {
  season_label: string
  minutes: number
  goals: number
  assists: number
  clean_sheets: number
  yellow_cards: number
  red_cards: number
  fpl_points: number
}

interface PlayerMatchStat {
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

interface PlayerAdvancedStats {
  season_label: string
  xg: number | null
  xa: number | null
  npxg: number | null
  xg_per_90: number | null
  xa_per_90: number | null
  progressive_carries: number | null
  progressive_passes: number | null
}

interface PlayerDetail {
  player: Player
  profile: PlayerProfile | null
  summaries: PlayerSeasonSummary[]
  recent_stats: PlayerMatchStat[]
  advanced_stats: PlayerAdvancedStats[] | null
}

const COLORS = ['#6366f1', '#f43f5e', '#10b981']

export const PlayerCompareTab: React.FC = () => {
  const { settings }                      = useSettings()
  const [searchQuery,   setSearchQuery]   = useState('')
  const [searchResults, setSearchResults] = useState<Player[]>([])
  const [compareList,   setCompareList]   = useState<PlayerDetail[]>([])
  const [searching,     setSearching]     = useState(false)
  const defaultsLoaded                    = useRef(false)

  useEffect(() => {
    if (searchQuery.trim().length < 2) { setSearchResults([]); return }
    setSearching(true)
    const t = setTimeout(() => {
      fetch(`http://localhost:8000/api/players?query=${searchQuery}`)
        .then(r => r.json())
        .then(data => { setSearchResults(data); setSearching(false) })
        .catch(() => setSearching(false))
    }, 300)
    return () => clearTimeout(t)
  }, [searchQuery])

  // Auto-populate with 2 players from the default team on first mount
  useEffect(() => {
    if (defaultsLoaded.current) return
    const teamId = settings.defaultTeamInternalId
    if (!teamId) return
    defaultsLoaded.current = true

    fetch(`http://localhost:8000/api/players?team_internal_id=${teamId}&limit=20`)
      .then(r => r.json())
      .then(async (players: Player[]) => {
        if (!Array.isArray(players) || players.length === 0) return
        // Pick first 2 players that have recorded stats
        const toAdd = players.slice(0, 2)
        for (const player of toAdd) {
          const res  = await fetch(`http://localhost:8000/api/players/compare?ids=${player.id}`)
          const data = await res.json()
          if (data?.[0]) {
            setCompareList(prev =>
              prev.length < 3 && !prev.some(p => p.player.id === player.id)
                ? [...prev, data[0]]
                : prev
            )
          }
        }
      })
      .catch(() => {})
  }, [settings.defaultTeamInternalId])

  const addPlayer = (player: Player) => {
    if (compareList.length >= 3) { alert('Max 3 players'); return }
    if (compareList.some(p => p.player.id === player.id)) return
    fetch(`http://localhost:8000/api/players/compare?ids=${player.id}`)
      .then(r => r.json())
      .then(data => {
        if (data?.[0]) {
          setCompareList(prev => [...prev, data[0]])
          setSearchQuery('')
          setSearchResults([])
        }
      })
      .catch(console.error)
  }

  const removePlayer = (id: number) =>
    setCompareList(prev => prev.filter(p => p.player.id !== id))

  // FPL points per season chart
  const fplChartData = (() => {
    const seasons = new Set<string>()
    compareList.forEach(pd => pd.summaries.forEach(s => seasons.add(s.season_label)))
    return Array.from(seasons).sort().map(season => {
      const row: any = { season }
      compareList.forEach(pd => {
        const sum = pd.summaries.find(s => s.season_label === season)
        row[`${pd.player.first_name} ${pd.player.second_name}`] = sum?.fpl_points ?? 0
      })
      return row
    })
  })()

  // xG per season chart (only if any player has adv stats)
  const hasAdvanced = compareList.some(pd => pd.advanced_stats && pd.advanced_stats.length > 0)
  const xgChartData = (() => {
    if (!hasAdvanced) return []
    const seasons = new Set<string>()
    compareList.forEach(pd => pd.advanced_stats?.forEach(s => seasons.add(s.season_label)))
    return Array.from(seasons).sort().map(season => {
      const row: any = { season }
      compareList.forEach(pd => {
        const adv = pd.advanced_stats?.find(s => s.season_label === season)
        row[`${pd.player.first_name} ${pd.player.second_name} xG`] = adv?.xg ?? 0
        row[`${pd.player.first_name} ${pd.player.second_name} xA`] = adv?.xa ?? 0
      })
      return row
    })
  })()

  const totalAdv = (pd: PlayerDetail, key: keyof PlayerAdvancedStats) =>
    pd.advanced_stats?.reduce((s, a) => s + ((a[key] as number | null) ?? 0), 0) ?? null

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Users className="w-5 h-5 text-indigo-400" />
          <h2 className="text-2xl font-black text-white">Player Comparison</h2>
        </div>
        <p className="text-sm text-slate-500">Compare up to 3 players across historical seasons, FPL stats, and advanced analytics.</p>
      </div>

      {/* Search */}
      <div className="glass-card p-6 rounded-2xl relative z-10">
        <h3 className="font-bold text-white mb-1 text-lg">Compare Players</h3>
        <p className="text-xs text-slate-500 mb-4">Add up to 3 players to compare across historical seasons.</p>
        <div className="relative">
          <Search className="absolute left-4 top-3.5 w-4 h-4 text-slate-400" />
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Type player name (e.g. Salah, Saka, Haaland)..."
            className="w-full bg-slate-900 border border-white/5 rounded-xl pl-12 pr-4 py-3 text-sm text-slate-200 outline-none focus:border-indigo-500 transition-colors"
          />
          {searching && (
            <div className="absolute right-4 top-3.5">
              <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>

        {searchResults.length > 0 && (
          <div className="absolute left-6 right-6 mt-2 bg-slate-900 border border-white/10 rounded-xl overflow-hidden shadow-2xl z-40 max-h-60 overflow-y-auto">
            {searchResults.map(player => (
              <button
                key={player.id}
                onClick={() => addPlayer(player)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 text-left border-b border-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
                    <User className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="font-bold text-white text-sm">{player.first_name} {player.second_name}</p>
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">{player.position}</span>
                  </div>
                </div>
                <Plus className="w-4 h-4 text-indigo-400" />
              </button>
            ))}
          </div>
        )}
      </div>

      {compareList.length > 0 ? (
        <div className="space-y-6">
          {/* Player cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {compareList.map((pd, idx) => (
              <div key={pd.player.id} className="glass-card p-5 rounded-2xl border border-white/5 relative flex flex-col overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1.5" style={{ backgroundColor: COLORS[idx] }} />
                <button
                  onClick={() => removePlayer(pd.player.id)}
                  className="absolute top-4 right-4 text-slate-500 hover:text-rose-500 transition-colors p-1.5 hover:bg-white/5 rounded-lg"
                >
                  <Trash2 className="w-4 h-4" />
                </button>

                <div className="flex items-center gap-3 mb-4 mt-1">
                  {pd.profile?.photo_url ? (
                    <img src={pd.profile.photo_url} alt="" className="w-14 h-14 rounded-full object-cover border-2 border-white/10" />
                  ) : (
                    <div className="w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center">
                      <User className="w-6 h-6 text-slate-500" />
                    </div>
                  )}
                  <div>
                    <span className="text-[10px] bg-slate-800 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
                      {pd.player.position}
                    </span>
                    <h4 className="text-base font-black text-white mt-1 leading-tight">
                      {pd.player.first_name} {pd.player.second_name}
                    </h4>
                    {pd.profile?.nationality && (
                      <p className="text-xs text-slate-500">{pd.profile.nationality}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-center border-t border-white/5 pt-4">
                  {[
                    { label: 'Goals',   val: pd.summaries.reduce((s, x) => s + x.goals,   0).toString() },
                    { label: 'Assists', val: pd.summaries.reduce((s, x) => s + x.assists, 0).toString() },
                    { label: 'xG',      val: totalAdv(pd, 'xg')?.toFixed(1) ?? '—' },
                    { label: 'xA',      val: totalAdv(pd, 'xa')?.toFixed(1) ?? '—' },
                  ].map(({ label, val }) => (
                    <div key={label} className="bg-slate-900/40 p-2.5 rounded-xl border border-white/3">
                      <span className="text-[10px] text-slate-500 font-bold uppercase">{label}</span>
                      <p className="text-lg font-black text-white mt-0.5">{val}</p>
                    </div>
                  ))}
                </div>

                {/* Progressive stats if available */}
                {pd.advanced_stats && pd.advanced_stats.length > 0 && (
                  <div className="mt-3 grid grid-cols-2 gap-2 text-center">
                    {[
                      { label: 'Prog. Carries', val: totalAdv(pd, 'progressive_carries') },
                      { label: 'Prog. Passes',  val: totalAdv(pd, 'progressive_passes') },
                    ].map(({ label, val }) => (
                      <div key={label} className="bg-slate-900/40 p-2 rounded-xl border border-white/3">
                        <span className="text-[10px] text-slate-500 font-bold uppercase">{label}</span>
                        <p className="text-base font-black text-white mt-0.5">{val ?? '—'}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {Array.from({ length: 3 - compareList.length }).map((_, i) => (
              <div key={i} className="glass-card p-6 rounded-2xl border border-dashed border-white/10 flex flex-col items-center justify-center text-center text-slate-500 min-h-[200px]">
                <User className="w-8 h-8 opacity-20 mb-2" />
                <p className="text-xs font-semibold">Add player to compare</p>
              </div>
            ))}
          </div>

          {/* FPL Points history chart */}
          {fplChartData.length > 0 && (
            <div className="glass-card p-6 rounded-2xl border border-white/5 h-[360px] flex flex-col">
              <h4 className="font-bold text-white mb-5">FPL Points by Season</h4>
              <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={fplChartData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="season" stroke="#64748b" fontSize={11} fontWeight={600} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} fontWeight={600} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px' }} />
                    <Legend />
                    {compareList.map((pd, idx) => (
                      <Bar key={pd.player.id} dataKey={`${pd.player.first_name} ${pd.player.second_name}`} fill={COLORS[idx]} radius={[4, 4, 0, 0]} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* xG / xA chart — only when at least one player has real data */}
          {hasAdvanced && xgChartData.length > 0 && compareList.some(pd => pd.advanced_stats?.some(s => s.xg != null)) && (
            <div className="glass-card p-6 rounded-2xl border border-white/5 h-[360px] flex flex-col">
              <h4 className="font-bold text-white mb-5">xG & xA by Season (TheStatsAPI)</h4>
              <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={xgChartData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="season" stroke="#64748b" fontSize={11} fontWeight={600} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} fontWeight={600} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px' }} />
                    <Legend />
                    {compareList.flatMap((pd, idx) => [
                      <Bar key={`${pd.player.id}-xg`} dataKey={`${pd.player.first_name} ${pd.player.second_name} xG`} fill={COLORS[idx]} radius={[4, 4, 0, 0]} />,
                      <Bar key={`${pd.player.id}-xa`} dataKey={`${pd.player.first_name} ${pd.player.second_name} xA`} fill={COLORS[idx]} fillOpacity={0.4} radius={[4, 4, 0, 0]} />,
                    ])}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Recent match details table */}
          <div className="glass-card p-6 rounded-2xl border border-white/5">
            <h4 className="font-bold text-white pb-2 border-b border-white/5 mb-4">Recent Match Details</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-semibold">
                <thead>
                  <tr className="border-b border-white/5 text-slate-400 uppercase tracking-wider">
                    <th className="py-3 px-4">Player</th>
                    <th className="py-3 px-4 text-center">GW</th>
                    <th className="py-3 px-4">Opponent</th>
                    <th className="py-3 px-4 text-center">Min</th>
                    <th className="py-3 px-4 text-center">G</th>
                    <th className="py-3 px-4 text-center">A</th>
                    <th className="py-3 px-4 text-center">FPL Pts</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-300">
                  {compareList.flatMap((pd, pidx) =>
                    pd.recent_stats.map((stat, sidx) => (
                      <tr key={`${pd.player.id}-${sidx}`} className="hover:bg-white/5 transition-colors">
                        <td className="py-3 px-4 font-bold text-white flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[pidx] }} />
                          {pd.player.first_name} {pd.player.second_name}
                        </td>
                        <td className="py-3 px-4 text-center text-slate-400">{stat.gameweek}</td>
                        <td className="py-3 px-4 text-indigo-400">{stat.opponent_name}</td>
                        <td className="py-3 px-4 text-center">{stat.minutes}</td>
                        <td className="py-3 px-4 text-center font-bold text-emerald-400">{stat.goals || '—'}</td>
                        <td className="py-3 px-4 text-center font-bold text-blue-400">{stat.assists || '—'}</td>
                        <td className="py-3 px-4 text-center font-black text-indigo-400">{stat.fpl_points}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="glass-card p-20 rounded-2xl text-center text-slate-500 border border-white/5">
          Search and select players above to compare their historical stats side-by-side.
        </div>
      )}
    </div>
  )
}
