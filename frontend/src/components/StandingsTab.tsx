import React, { useState, useEffect } from 'react'

interface Team {
  id: number
  name: string
  short_name: string
}

interface StandingItem {
  team: Team
  gameweek: number
  points: number
  played: number
  wins: number
  draws: number
  losses: number
  goals_for: number
  goals_against: number
  goal_difference: number
  position: number
}

interface Season {
  id: number
  label: string
}

interface StandingsTabProps {
  seasons: Season[]
  selectedSeasonId: number
  setSelectedSeasonId: (id: number) => void
}

export const StandingsTab: React.FC<StandingsTabProps> = ({
  seasons,
  selectedSeasonId,
  setSelectedSeasonId,
}) => {
  const [gameweek, setGameweek] = useState<number>(38)
  const [maxGameweek, setMaxGameweek] = useState<number>(38)
  const [standings, setStandings] = useState<StandingItem[]>([])
  const [loading, setLoading] = useState<boolean>(false)

  useEffect(() => {
    if (!selectedSeasonId) return

    setLoading(true)
    // First query with no gameweek to find out the latest gameweek in database
    fetch(`http://localhost:8000/api/standings?season_id=${selectedSeasonId}`)
      .then((res) => res.json())
      .then((data) => {
        setStandings(data.standings || [])
        setGameweek(data.gameweek || 38)
        setMaxGameweek(data.gameweek || 38)
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setLoading(false)
      })
  }, [selectedSeasonId])

  useEffect(() => {
    if (!selectedSeasonId || gameweek === maxGameweek) return

    setLoading(true)
    fetch(`http://localhost:8000/api/standings?season_id=${selectedSeasonId}&gameweek=${gameweek}`)
      .then((res) => res.json())
      .then((data) => {
        setStandings(data.standings || [])
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setLoading(false)
      })
  }, [gameweek, selectedSeasonId])

  const getPositionClass = (pos: number) => {
    if (pos <= 4) return 'border-l-4 border-emerald-500 bg-emerald-950/10'
    if (pos === 5) return 'border-l-4 border-blue-500 bg-blue-950/10'
    if (pos >= 18) return 'border-l-4 border-rose-500 bg-rose-950/10'
    return 'border-l-4 border-transparent'
  }

  return (
    <div className="space-y-6">
      {/* Controls Card */}
      <div className="glass-card p-6 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Season Selector */}
        <div className="flex flex-col gap-1 w-full md:w-auto">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Select Season</label>
          <select
            value={selectedSeasonId}
            onChange={(e) => setSelectedSeasonId(Number(e.target.value))}
            className="bg-slate-900 border border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors w-full md:w-60"
          >
            {seasons.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {/* Gameweek Slider */}
        <div className="flex flex-col gap-1 flex-1 w-full">
          <div className="flex justify-between items-center mb-1">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Gameweek Round</label>
            <span className="bg-indigo-500/10 text-indigo-400 px-3 py-1 rounded-full text-xs font-bold border border-indigo-500/20">
              Round {gameweek} of {maxGameweek}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setGameweek(prev => Math.max(1, prev - 1))}
              disabled={gameweek <= 1}
              className="bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white p-2 rounded-xl text-sm font-bold w-10 h-10 flex items-center justify-center transition-colors border border-white/5"
            >
              -
            </button>
            <input
              type="range"
              min={1}
              max={maxGameweek || 38}
              value={gameweek}
              onChange={(e) => setGameweek(Number(e.target.value))}
              className="flex-1 accent-indigo-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
            <button
              onClick={() => setGameweek(prev => Math.min(maxGameweek, prev + 1))}
              disabled={gameweek >= maxGameweek}
              className="bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white p-2 rounded-xl text-sm font-bold w-10 h-10 flex items-center justify-center transition-colors border border-white/5"
            >
              +
            </button>
          </div>
        </div>
      </div>

      {/* Standings Table Card */}
      <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-slate-400 text-sm">Calculating standings...</p>
          </div>
        ) : standings.length === 0 ? (
          <div className="text-center py-20 text-slate-500">No match records found for this season.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 bg-slate-900/40 text-xs font-bold uppercase tracking-wider text-slate-400">
                  <th className="py-4 px-6 text-center w-16">Pos</th>
                  <th className="py-4 px-4">Club</th>
                  <th className="py-4 px-4 text-center">Pl</th>
                  <th className="py-4 px-4 text-center">W</th>
                  <th className="py-4 px-4 text-center">D</th>
                  <th className="py-4 px-4 text-center">L</th>
                  <th className="py-4 px-4 text-center">GF</th>
                  <th className="py-4 px-4 text-center">GA</th>
                  <th className="py-4 px-4 text-center">GD</th>
                  <th className="py-4 px-6 text-center font-extrabold text-indigo-400">Pts</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm font-medium text-slate-300">
                {standings.map((item) => (
                  <tr key={item.team.id} className={`hover:bg-white/20 transition-colors ${getPositionClass(item.position)}`}>
                    <td className="py-4 px-6 text-center font-bold text-slate-400">{item.position}</td>
                    <td className="py-4 px-4 font-bold text-white text-base">{item.team.name}</td>
                    <td className="py-4 px-4 text-center">{item.played}</td>
                    <td className="py-4 px-4 text-center">{item.wins}</td>
                    <td className="py-4 px-4 text-center">{item.draws}</td>
                    <td className="py-4 px-4 text-center">{item.losses}</td>
                    <td className="py-4 px-4 text-center">{item.goals_for}</td>
                    <td className="py-4 px-4 text-center">{item.goals_against}</td>
                    <td className="py-4 px-4 text-center">{item.goal_difference > 0 ? `+${item.goal_difference}` : item.goal_difference}</td>
                    <td className="py-4 px-6 text-center font-extrabold text-indigo-400 text-base">{item.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-6 justify-center md:justify-start px-4 text-xs font-semibold text-slate-500">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-emerald-500 rounded-full"></span>
          <span>UEFA Champions League Group Stage</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
          <span>UEFA Europa League Group Stage</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-rose-500 rounded-full"></span>
          <span>Relegation to Championship</span>
        </div>
      </div>
    </div>
  )
}
