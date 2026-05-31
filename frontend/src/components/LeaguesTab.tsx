import React, { useState, useEffect } from 'react'
import { Globe } from 'lucide-react'
import { useSettings } from '../contexts/SettingsContext'

// ── Types ─────────────────────────────────────────────────────────────────────

interface League {
  id: number
  name: string
  country: string
  flag: string
  logo: string
}

interface StandingRow {
  rank: number
  team_api_id: number
  team_name: string
  team_logo: string | null
  points: number
  goals_diff: number
  form: string
  played: number
  wins: number
  draws: number
  losses: number
  goals_for: number
  goals_against: number
}

interface Props {
  onTeamClick: (params: ExternalTeamParams) => void
}

export interface ExternalTeamParams {
  teamApiId: number
  teamName: string
  teamLogo: string | null
  leagueId: number
  leagueName: string
  season: number
  standing: StandingRow | null
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const AVAILABLE_SEASONS = [2025, 2024, 2023, 2022, 2021]

function seasonLabel(year: number) {
  return `${year}–${String(year + 1).slice(2)}`
}

function zoneColor(rank: number, leagueId: number): string {
  // UCL spots: top 4 for PL/Liga/SerieA/L1, top 4 for Bundesliga
  if (rank <= 4)  return 'border-l-[3px] border-emerald-500 bg-emerald-950/10'
  if (rank === 5) return 'border-l-[3px] border-blue-500   bg-blue-950/10'
  // Relegation: bottom 3 for most, bottom 2 for Bundesliga (18 teams)
  const total = leagueId === 78 ? 18 : 20
  if (rank > total - 3) return 'border-l-[3px] border-rose-500 bg-rose-950/10'
  return 'border-l-[3px] border-transparent'
}

function FormPip({ r }: { r: string }) {
  const cls =
    r === 'W' ? 'bg-emerald-500' :
    r === 'L' ? 'bg-rose-500'    :
    r === 'D' ? 'bg-amber-500'   : 'bg-slate-700'
  return <span className={`w-2 h-2 rounded-full inline-block ${cls}`} title={r} />
}

// ── Component ─────────────────────────────────────────────────────────────────

export const LeaguesTab: React.FC<Props> = ({ onTeamClick }) => {
  const { settings } = useSettings()
  const [leagues,    setLeagues]    = useState<League[]>([])
  const [activeLeague, setActiveLeague] = useState<League | null>(null)
  const [season,     setSeason]     = useState(AVAILABLE_SEASONS[0])
  const [standings,  setStandings]  = useState<StandingRow[]>([])
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState<string | null>(null)

  // Load league list once
  useEffect(() => {
    fetch('http://localhost:8000/api/leagues')
      .then(r => r.json())
      .then(data => {
        setLeagues(data)
        // Open on the default league from settings
        const def = data.find((l: League) => l.id === settings.defaultLeagueId) ?? data[0] ?? null
        setActiveLeague(def)
      })
      .catch(console.error)
  }, [])

  // Load standings when league or season changes
  useEffect(() => {
    if (!activeLeague) return
    setLoading(true)
    setError(null)
    fetch(`http://localhost:8000/api/leagues/${activeLeague.id}/standings?season=${season}`)
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setStandings(data)
        } else {
          setStandings([])
          setError(`No standings data found for ${activeLeague.name} ${seasonLabel(season)}. The season may not have started yet.`)
        }
        setLoading(false)
      })
      .catch(() => {
        setError('Failed to load standings.')
        setLoading(false)
      })
  }, [activeLeague, season])

  const handleTeamClick = (row: StandingRow) => {
    if (!activeLeague) return
    onTeamClick({
      teamApiId:   row.team_api_id,
      teamName:    row.team_name,
      teamLogo:    row.team_logo,
      leagueId:    activeLeague.id,
      leagueName:  activeLeague.name,
      season,
      standing:    row,
    })
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      {/* League selector */}
      <div className="glass-card p-2 rounded-2xl border border-white/5">
        <div className="flex flex-wrap gap-1">
          {leagues.map(league => (
            <button
              key={league.id}
              onClick={() => setActiveLeague(league)}
              className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all flex-1 sm:flex-none justify-center sm:justify-start ${
                activeLeague?.id === league.id
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <span className="text-base">{league.flag}</span>
              <span className="hidden sm:inline">{league.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Season + league header row */}
      {activeLeague && (
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <img src={activeLeague.logo} alt={activeLeague.name} className="w-8 h-8 object-contain" />
            <div>
              <h3 className="font-black text-white text-lg leading-tight">{activeLeague.name}</h3>
              <p className="text-xs text-slate-500">{activeLeague.country}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Season</label>
            <select
              value={season}
              onChange={e => setSeason(Number(e.target.value))}
              className="bg-slate-900 border border-white/5 rounded-xl px-3 py-2 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors"
            >
              {AVAILABLE_SEASONS.map(y => (
                <option key={y} value={y}>{seasonLabel(y)}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Standings table */}
      <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-400 text-sm">Loading standings…</p>
          </div>
        ) : error ? (
          <div className="text-center py-16 text-slate-500">
            <Globe className="w-10 h-10 mx-auto mb-3 text-slate-700" />
            <p className="font-semibold">{error}</p>
          </div>
        ) : standings.length === 0 ? (
          <div className="text-center py-16 text-slate-500">No data available.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 bg-slate-900/50 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <th className="py-3 px-4 w-10 text-center">#</th>
                  <th className="py-3 px-3">Club</th>
                  <th className="py-3 px-3 text-center">MP</th>
                  <th className="py-3 px-3 text-center">W</th>
                  <th className="py-3 px-3 text-center">D</th>
                  <th className="py-3 px-3 text-center">L</th>
                  <th className="py-3 px-3 text-center">GF</th>
                  <th className="py-3 px-3 text-center">GA</th>
                  <th className="py-3 px-3 text-center">GD</th>
                  <th className="py-3 px-3 text-center hidden md:table-cell">Form</th>
                  <th className="py-3 px-4 text-center text-indigo-400">Pts</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04] text-sm text-slate-300">
                {standings.map(row => (
                  <tr
                    key={row.team_api_id}
                    className={`hover:bg-white/[0.03] transition-colors ${zoneColor(row.rank, activeLeague?.id ?? 39)}`}
                  >
                    <td className="py-3 px-4 text-center font-bold text-slate-400 tabular-nums">
                      {row.rank}
                    </td>
                    <td className="py-3 px-3">
                      <button
                        onClick={() => handleTeamClick(row)}
                        className="flex items-center gap-2.5 hover:text-indigo-400 transition-colors text-left group"
                      >
                        {row.team_logo
                          ? <img src={row.team_logo} alt="" className="w-6 h-6 object-contain shrink-0" />
                          : <span className="w-6 h-6 rounded-full bg-slate-800 shrink-0" />
                        }
                        <span className="font-semibold text-white group-hover:text-indigo-400 transition-colors whitespace-nowrap">
                          {row.team_name}
                        </span>
                      </button>
                    </td>
                    <td className="py-3 px-3 text-center tabular-nums">{row.played}</td>
                    <td className="py-3 px-3 text-center tabular-nums text-emerald-400 font-semibold">{row.wins}</td>
                    <td className="py-3 px-3 text-center tabular-nums">{row.draws}</td>
                    <td className="py-3 px-3 text-center tabular-nums text-rose-400/80">{row.losses}</td>
                    <td className="py-3 px-3 text-center tabular-nums">{row.goals_for}</td>
                    <td className="py-3 px-3 text-center tabular-nums">{row.goals_against}</td>
                    <td className={`py-3 px-3 text-center tabular-nums font-semibold ${
                      (row.goals_diff ?? 0) > 0 ? 'text-emerald-400' :
                      (row.goals_diff ?? 0) < 0 ? 'text-rose-400'    : 'text-slate-400'
                    }`}>
                      {(row.goals_diff ?? 0) > 0 ? `+${row.goals_diff}` : row.goals_diff}
                    </td>
                    <td className="py-3 px-3 text-center hidden md:table-cell">
                      <div className="flex items-center justify-center gap-0.5">
                        {row.form.split('').slice(-5).map((r, i) => <FormPip key={i} r={r} />)}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center font-black text-indigo-400 text-base tabular-nums">
                      {row.points}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Zone legend */}
      {standings.length > 0 && (
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
      )}
    </div>
  )
}
