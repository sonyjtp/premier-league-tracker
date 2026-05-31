import React, { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Search, Plus, Trash2, User } from 'lucide-react'

interface Player {
  id: number
  first_name: string
  second_name: string
  position: string
  current_fpl_id: number | null
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

interface PlayerDetail {
  player: Player
  summaries: PlayerSeasonSummary[]
  recent_stats: PlayerMatchStat[]
}

export const PlayerCompareTab: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [searchResults, setSearchResults] = useState<Player[]>([])
  const [compareList, setCompareList] = useState<PlayerDetail[]>([])
  const [searching, setSearching] = useState<boolean>(false)

  // Trigger search on query change
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults([])
      return
    }

    setSearching(true)
    const delayDebounce = setTimeout(() => {
      fetch(`http://localhost:8000/api/players?query=${searchQuery}`)
        .then((res) => res.json())
        .then((data) => {
          setSearchResults(data)
          setSearching(false)
        })
        .catch((err) => {
          console.error(err)
          setSearching(false)
        })
    }, 300)

    return () => clearTimeout(delayDebounce)
  }, [searchQuery])

  const addPlayerToCompare = (player: Player) => {
    // Check limit of 3 players
    if (compareList.length >= 3) {
      alert("You can compare up to 3 players at a time.")
      return
    }
    // Avoid duplicate addition
    if (compareList.some((p) => p.player.id === player.id)) {
      return
    }

    fetch(`http://localhost:8000/api/players/compare?ids=${player.id}`)
      .then((res) => res.json())
      .then((data) => {
        if (data && data.length > 0) {
          setCompareList((prev) => [...prev, data[0]])
          setSearchQuery('')
          setSearchResults([])
        }
      })
      .catch((err) => console.error(err))
  }

  const removePlayerFromCompare = (playerId: number) => {
    setCompareList((prev) => prev.filter((p) => p.player.id !== playerId))
  }

  // Prep Recharts data for multi-season comparison
  const getHistoricalChartData = () => {
    // We get all unique season labels across compared players
    const allSeasons = new Set<string>()
    compareList.forEach((pd) => {
      pd.summaries.forEach((s) => allSeasons.add(s.season_label))
    })

    const sortedSeasons = Array.from(allSeasons).sort()
    
    return sortedSeasons.map((season) => {
      const dataPoint: any = { season }
      compareList.forEach((pd) => {
        const sum = pd.summaries.find((s) => s.season_label === season)
        dataPoint[`${pd.player.first_name} ${pd.player.second_name}`] = sum ? sum.fpl_points : 0
      })
      return dataPoint
    })
  }

  const historicalChartData = getHistoricalChartData()
  const playerColors = ["#6366f1", "#f43f5e", "#10b981"]

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="glass-card p-6 rounded-2xl relative">
        <h3 className="font-bold text-white mb-3 text-lg">Compare Players</h3>
        <p className="text-xs text-slate-500 mb-4">Search players to add up to 3 for comparison across historical seasons and current form.</p>
        
        <div className="relative">
          <Search className="absolute left-4 top-3.5 w-4.5 h-4.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Type player name (e.g. Salah, Saka, Haaland)..."
            className="w-full bg-slate-900 border border-white/5 rounded-xl pl-12 pr-4 py-3 text-sm text-slate-200 outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        {/* Search Results Dropdown */}
        {searchResults.length > 0 && (
          <div className="absolute left-6 right-6 mt-2 bg-slate-900 border border-white/10 rounded-xl overflow-hidden shadow-2xl z-40 max-h-60 overflow-y-auto">
            {searchResults.map((player) => (
              <button
                key={player.id}
                onClick={() => addPlayerToCompare(player)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 text-left border-b border-white/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
                    <User className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="font-bold text-white text-sm">
                      {player.first_name} {player.second_name}
                    </div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">
                      {player.position}
                    </span>
                  </div>
                </div>
                <Plus className="w-4 h-4 text-indigo-400" />
              </button>
            ))}
          </div>
        )}
        
        {searching && (
          <div className="absolute right-10 top-16">
            <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
      </div>

      {compareList.length > 0 ? (
        <div className="space-y-6">
          {/* Side-by-Side Player Profiles */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {compareList.map((pd, idx) => (
              <div key={pd.player.id} className="glass-card p-5 rounded-2xl border border-white/5 relative flex flex-col justify-between overflow-hidden">
                <div
                  className="absolute top-0 left-0 w-full h-1.5"
                  style={{ backgroundColor: playerColors[idx] }}
                ></div>
                <button
                  onClick={() => removePlayerFromCompare(pd.player.id)}
                  className="absolute top-4 right-4 text-slate-500 hover:text-rose-500 transition-colors p-1.5 hover:bg-white/5 rounded-lg"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                
                <div className="mb-4">
                  <span className="text-[10px] bg-slate-800 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
                    {pd.player.position}
                  </span>
                  <h4 className="text-xl font-black text-white mt-2 leading-tight">
                    {pd.player.first_name} {pd.player.second_name}
                  </h4>
                </div>

                <div className="grid grid-cols-2 gap-3 text-center border-t border-white/5 pt-4">
                  <div className="bg-slate-900/40 p-2.5 rounded-xl border border-white/3">
                    <span className="text-[10px] text-slate-500 font-bold uppercase">Total Goals</span>
                    <p className="text-lg font-black text-white mt-0.5">
                      {pd.summaries.reduce((sum, s) => sum + s.goals, 0)}
                    </p>
                  </div>
                  <div className="bg-slate-900/40 p-2.5 rounded-xl border border-white/3">
                    <span className="text-[10px] text-slate-500 font-bold uppercase">Total Assists</span>
                    <p className="text-lg font-black text-white mt-0.5">
                      {pd.summaries.reduce((sum, s) => sum + s.assists, 0)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Empty Slots */}
            {Array.from({ length: 3 - compareList.length }).map((_, i) => (
              <div key={i} className="glass-card p-6 rounded-2xl border border-white/5 border-dashed border-white/10 flex flex-col items-center justify-center text-center text-slate-500 min-h-[160px]">
                <User className="w-8 h-8 opacity-20 mb-2" />
                <p className="text-xs font-semibold">Add player to compare</p>
              </div>
            ))}
          </div>

          {/* Historical Seasons Chart */}
          {historicalChartData.length > 0 && (
            <div className="glass-card p-6 rounded-2xl border border-white/5 h-[400px] flex flex-col">
              <h4 className="font-bold text-white mb-6">Historical Performance Comparison (FPL Points)</h4>
              <div className="flex-1 w-full min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={historicalChartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="season" stroke="#64748b" fontSize={11} fontWeight="600" tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} fontWeight="600" tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        borderColor: 'rgba(255,255,255,0.08)',
                        borderRadius: '12px',
                        color: '#f8fafc',
                      }}
                    />
                    <Legend />
                    {compareList.map((pd, idx) => (
                      <Bar
                        key={pd.player.id}
                        dataKey={`${pd.player.first_name} ${pd.player.second_name}`}
                        fill={playerColors[idx]}
                        radius={[4, 4, 0, 0]}
                      />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Recent Gameweek Performance Details */}
          <div className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
            <h4 className="font-bold text-white pb-2 border-b border-white/5">Recent Match Details (Current Season)</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs font-semibold">
                <thead>
                  <tr className="border-b border-white/5 text-slate-400 uppercase tracking-wider font-bold">
                    <th className="py-3 px-4">Player</th>
                    <th className="py-3 px-4 text-center">GW</th>
                    <th className="py-3 px-4">Opponent</th>
                    <th className="py-3 px-4 text-center">Min</th>
                    <th className="py-3 px-4 text-center">Goals</th>
                    <th className="py-3 px-4 text-center">Assists</th>
                    <th className="py-3 px-4 text-center">FPL Pts</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-300">
                  {compareList.flatMap((pd, pidx) => 
                    pd.recent_stats.map((stat, sidx) => (
                      <tr key={`${pd.player.id}-${sidx}`} className="hover:bg-white/20 transition-colors">
                        <td className="py-3.5 px-4 font-bold text-white flex items-center gap-2">
                          <span
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: playerColors[pidx] }}
                          ></span>
                          {pd.player.first_name} {pd.player.second_name}
                        </td>
                        <td className="py-3.5 px-4 text-center font-bold text-slate-400">{stat.gameweek}</td>
                        <td className="py-3.5 px-4 font-bold text-indigo-400">{stat.opponent_name}</td>
                        <td className="py-3.5 px-4 text-center">{stat.minutes}</td>
                        <td className="py-3.5 px-4 text-center font-bold text-emerald-400">{stat.goals || "-"}</td>
                        <td className="py-3.5 px-4 text-center font-bold text-blue-400">{stat.assists || "-"}</td>
                        <td className="py-3.5 px-4 text-center font-black text-indigo-400">{stat.fpl_points}</td>
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
          Search and select players above to compare their 10-year summaries and recent stats side-by-side.
        </div>
      )}
    </div>
  )
}
