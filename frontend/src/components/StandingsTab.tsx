import React, { useState, useEffect } from 'react'
import { Trophy, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface Team { id: number; name: string; short_name: string }

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

interface Season { id: number; label: string }

interface Props {
  seasons: Season[]
  selectedSeasonId: number
  setSelectedSeasonId: (id: number) => void
  onTeamClick: (teamId: number) => void
}

type PositionChange = { dir: 'up' | 'down' | 'same'; amount: number }

const ZONE = {
  ucl:       { label: 'Champions League',  color: 'border-l-[3px] border-emerald-500 bg-emerald-950/10' },
  uel:       { label: 'Europa League',      color: 'border-l-[3px] border-blue-500   bg-blue-950/10'   },
  rel:       { label: 'Relegation',         color: 'border-l-[3px] border-rose-500   bg-rose-950/10'   },
  none:      { label: '',                   color: 'border-l-[3px] border-transparent'                  },
}

function zone(pos: number) {
  if (pos <= 4) return ZONE.ucl
  if (pos === 5) return ZONE.uel
  if (pos >= 18) return ZONE.rel
  return ZONE.none
}

function ChangeIcon({ change }: { change: PositionChange | null }) {
  if (!change || change.dir === 'same')
    return <Minus className="w-3 h-3 text-slate-600" />
  if (change.dir === 'up')
    return (
      <span className="flex items-center gap-0.5 text-emerald-400 text-[10px] font-black">
        <TrendingUp className="w-3 h-3" />{change.amount}
      </span>
    )
  return (
    <span className="flex items-center gap-0.5 text-rose-400 text-[10px] font-black">
      <TrendingDown className="w-3 h-3" />{change.amount}
    </span>
  )
}

export const StandingsTab: React.FC<Props> = ({ seasons, selectedSeasonId, setSelectedSeasonId, onTeamClick }) => {
  const [gameweek,     setGameweek]     = useState(38)
  const [maxGameweek,  setMaxGameweek]  = useState(38)
  const [standings,    setStandings]    = useState<StandingItem[]>([])
  const [prevPos,      setPrevPos]      = useState<Map<number, number>>(new Map())
  const [loading,      setLoading]      = useState(false)
  const [seasonLabel,  setSeasonLabel]  = useState('')

  // Initial fetch — get latest gameweek
  useEffect(() => {
    if (!selectedSeasonId) return
    setLoading(true)
    fetch(`http://localhost:8000/api/standings?season_id=${selectedSeasonId}`)
      .then(r => r.json())
      .then(data => {
        setStandings(data.standings ?? [])
        setSeasonLabel(data.season_label ?? '')
        const gw = data.gameweek ?? 38
        setGameweek(gw)
        setMaxGameweek(gw)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [selectedSeasonId])

  // Fetch chosen gameweek when slider changes
  useEffect(() => {
    if (!selectedSeasonId || gameweek === maxGameweek) return
    setLoading(true)
    fetch(`http://localhost:8000/api/standings?season_id=${selectedSeasonId}&gameweek=${gameweek}`)
      .then(r => r.json())
      .then(data => { setStandings(data.standings ?? []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [gameweek, selectedSeasonId])

  // Fetch previous gameweek for position-change arrows
  useEffect(() => {
    if (gameweek <= 1 || !selectedSeasonId) { setPrevPos(new Map()); return }
    fetch(`http://localhost:8000/api/standings?season_id=${selectedSeasonId}&gameweek=${gameweek - 1}`)
      .then(r => r.json())
      .then(data => {
        const m = new Map<number, number>()
        data.standings?.forEach((s: StandingItem) => m.set(s.team.id, s.position))
        setPrevPos(m)
      })
      .catch(() => setPrevPos(new Map()))
  }, [gameweek, selectedSeasonId])

  function getChange(teamId: number, currentPos: number): PositionChange | null {
    const prev = prevPos.get(teamId)
    if (prev == null) return null
    const diff = prev - currentPos
    if (diff > 0) return { dir: 'up',   amount: diff }
    if (diff < 0) return { dir: 'down', amount: -diff }
    return { dir: 'same', amount: 0 }
  }

  const leader = standings[0]?.points ?? 0

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Trophy className="w-5 h-5 text-indigo-400" />
          <h2 className="text-2xl font-black text-white">Premier League Standings</h2>
        </div>
        <p className="text-sm text-slate-500">
          {seasonLabel ? `${seasonLabel} season` : 'Select a season to view the table'}
          {maxGameweek > 0 && ` · Gameweek ${gameweek} of ${maxGameweek}`}
        </p>
      </div>

      {/* Controls */}
      <div className="glass-card p-5 rounded-2xl flex flex-col md:flex-row items-center gap-5 border border-white/5">
        <div className="flex flex-col gap-1 w-full md:w-56 shrink-0">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Season</label>
          <select
            value={selectedSeasonId}
            onChange={e => setSelectedSeasonId(Number(e.target.value))}
            className="bg-slate-900 border border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors w-full"
          >
            {seasons.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-2 flex-1 w-full">
          <div className="flex justify-between items-center">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Gameweek</label>
            <span className="bg-indigo-500/10 text-indigo-400 px-3 py-0.5 rounded-full text-xs font-bold border border-indigo-500/20">
              Round {gameweek} of {maxGameweek}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setGameweek(p => Math.max(1, p - 1))}
              disabled={gameweek <= 1}
              className="bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white rounded-xl text-sm font-bold w-9 h-9 flex items-center justify-center transition-colors border border-white/5 shrink-0"
            >−</button>
            <input
              type="range" min={1} max={maxGameweek || 38} value={gameweek}
              onChange={e => setGameweek(Number(e.target.value))}
              className="flex-1 accent-indigo-500 cursor-pointer"
            />
            <button
              onClick={() => setGameweek(p => Math.min(maxGameweek, p + 1))}
              disabled={gameweek >= maxGameweek}
              className="bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-white rounded-xl text-sm font-bold w-9 h-9 flex items-center justify-center transition-colors border border-white/5 shrink-0"
            >+</button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-400 text-sm">Calculating standings…</p>
          </div>
        ) : standings.length === 0 ? (
          <div className="text-center py-20 text-slate-500">No data found for this season.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 bg-slate-900/50 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <th className="py-3 px-4 text-center w-10">#</th>
                  <th className="py-3 px-2 w-6"></th>{/* change arrow */}
                  <th className="py-3 px-3">Club</th>
                  <th className="py-3 px-3 text-center">MP</th>
                  <th className="py-3 px-3 text-center">W</th>
                  <th className="py-3 px-3 text-center">D</th>
                  <th className="py-3 px-3 text-center">L</th>
                  <th className="py-3 px-3 text-center">GF</th>
                  <th className="py-3 px-3 text-center">GA</th>
                  <th className="py-3 px-3 text-center">GD</th>
                  <th className="py-3 px-3 text-center hidden sm:table-cell">−Pts</th>
                  <th className="py-3 px-4 text-center text-indigo-400">Pts</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04] text-sm text-slate-300">
                {standings.map(item => {
                  const z = zone(item.position)
                  const change = getChange(item.team.id, item.position)
                  const gap = leader - item.points
                  return (
                    <tr key={item.team.id} className={`hover:bg-white/[0.03] transition-colors ${z.color}`}>
                      <td className="py-3.5 px-4 text-center font-bold text-slate-400 tabular-nums">{item.position}</td>
                      <td className="py-3.5 px-2 text-center">
                        <ChangeIcon change={change} />
                      </td>
                      <td className="py-3.5 px-3 whitespace-nowrap">
                        <button onClick={() => onTeamClick(item.team.id)} className="font-semibold text-white hover:text-indigo-400 transition-colors text-left">
                          {item.team.name}
                        </button>
                      </td>
                      <td className="py-3.5 px-3 text-center tabular-nums">{item.played}</td>
                      <td className="py-3.5 px-3 text-center tabular-nums text-emerald-400 font-semibold">{item.wins}</td>
                      <td className="py-3.5 px-3 text-center tabular-nums">{item.draws}</td>
                      <td className="py-3.5 px-3 text-center tabular-nums text-rose-400/80">{item.losses}</td>
                      <td className="py-3.5 px-3 text-center tabular-nums">{item.goals_for}</td>
                      <td className="py-3.5 px-3 text-center tabular-nums">{item.goals_against}</td>
                      <td className={`py-3.5 px-3 text-center tabular-nums font-semibold ${item.goal_difference > 0 ? 'text-emerald-400' : item.goal_difference < 0 ? 'text-rose-400' : 'text-slate-400'}`}>
                        {item.goal_difference > 0 ? `+${item.goal_difference}` : item.goal_difference}
                      </td>
                      <td className="py-3.5 px-3 text-center tabular-nums text-slate-500 hidden sm:table-cell">
                        {gap > 0 ? `-${gap}` : '—'}
                      </td>
                      <td className="py-3.5 px-4 text-center font-black text-indigo-400 text-base tabular-nums">{item.points}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-x-8 gap-y-2 px-1 text-xs font-semibold text-slate-500">
        {[
          { color: 'bg-emerald-500', label: 'UEFA Champions League' },
          { color: 'bg-blue-500',    label: 'UEFA Europa League' },
          { color: 'bg-rose-500',    label: 'Relegation zone' },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
            {label}
          </div>
        ))}
      </div>
    </div>
  )
}
