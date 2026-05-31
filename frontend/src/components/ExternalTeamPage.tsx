import React, { useState, useEffect } from 'react'
import { ArrowLeft, MapPin, Shield, History } from 'lucide-react'
import type { ExternalTeamParams } from './LeaguesTab'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Fixture {
  fixture_id: number
  date: string | null
  status_short: string
  home_team: string
  away_team: string
  home_logo: string | null
  away_logo: string | null
  home_goals: number | null
  away_goals: number | null
  home_winner: boolean | null
}

interface SquadPlayer {
  id: number | null
  name: string
  age: number | null
  number: number | null
  position: string | null
  photo: string | null
}

interface Props extends ExternalTeamParams {
  onBack: () => void
  onViewFullHistory: (internalTeamId: number) => void
  onPlayerClick?: (playerId: number) => void
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function seasonLabel(year: number) {
  return `${year}–${String(year + 1).slice(2)}`
}

function ordinal(n: number) {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return n + (s[(v - 20) % 10] ?? s[v] ?? s[0])
}

const RESULT_STYLE = {
  W: 'bg-emerald-600 text-white',
  L: 'bg-rose-600   text-white',
  D: 'bg-amber-500  text-slate-900',
}

const POS_BADGE = (pos: number) =>
  pos === 1   ? 'bg-yellow-500/10  text-yellow-400  border-yellow-500/20'  :
  pos <= 4    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
  pos === 5   ? 'bg-blue-500/10    text-blue-400    border-blue-500/20'    :
  pos >= 18   ? 'bg-rose-500/10    text-rose-400    border-rose-500/20'    :
               'bg-slate-800      text-slate-300   border-white/5'

// ── Component ─────────────────────────────────────────────────────────────────

export const ExternalTeamPage: React.FC<Props> = ({
  teamApiId, teamName, teamLogo, leagueId, leagueName, season, standing,
  onBack, onViewFullHistory, onPlayerClick,
}) => {
  const [fixtures,           setFixtures]           = useState<Fixture[]>([])
  const [squad,              setSquad]              = useState<SquadPlayer[]>([])
  const [internalTeamId,     setInternalTeamId]     = useState<number | null>(null)
  const [fixturesLoad,       setFixturesLoad]       = useState(true)
  const [squadLoad,          setSquadLoad]          = useState(true)
  const [unavailablePlayers, setUnavailablePlayers] = useState<Set<number | null>>(new Set())

  useEffect(() => {
    // Fetch recent fixtures
    setFixturesLoad(true)
    fetch(`http://localhost:8000/api/external/teams/${teamApiId}/fixtures?league_id=${leagueId}&season=${season}&limit=10`)
      .then(r => r.json())
      .then(data => { setFixtures(Array.isArray(data) ? data : []); setFixturesLoad(false) })
      .catch(() => setFixturesLoad(false))

    // Fetch squad
    setSquadLoad(true)
    fetch(`http://localhost:8000/api/external/teams/${teamApiId}/squad`)
      .then(r => r.json())
      .then(data => { setSquad(Array.isArray(data) ? data : []); setSquadLoad(false) })
      .catch(() => setSquadLoad(false))

    // Check if this is a PL team we have internally
    fetch(`http://localhost:8000/api/teams/lookup?api_football_id=${teamApiId}`)
      .then(r => r.json())
      .then(data => { if (data.internal_team_id) setInternalTeamId(data.internal_team_id) })
      .catch(() => {})
  }, [teamApiId, leagueId, season])

  // Look up player by API-Football ID, fallback to name search
  function lookupPlayerAndNavigate(apiFootballId: number, playerName: string) {
    fetch(`http://localhost:8000/api/players/lookup/api-football/${apiFootballId}`)
      .then(r => {
        if (r.ok) return r.json()
        // Fallback: extract last name from abbreviated format (e.g., "M. Gibbs-White" -> search "Gibbs-White")
        const lastNameMatch = playerName.match(/\.\s*(.+)$/) || playerName.match(/\s+(\S+)$/)
        const searchQuery = lastNameMatch ? lastNameMatch[1] : playerName
        return fetch(`http://localhost:8000/api/players?query=${encodeURIComponent(searchQuery)}`)
          .then(r => r.json())
          .then((data: any[]) => {
            if (Array.isArray(data) && data.length > 0) return data[0]
            throw new Error('Player not found')
          })
      })
      .then((player: any) => {
        onPlayerClick?.(player.id)
      })
      .catch(() => {
        setUnavailablePlayers(prev => new Set([...prev, apiFootballId]))
      })
  }

  // Determine result from this team's perspective
  function getResult(f: Fixture): 'W' | 'L' | 'D' | null {
    if (f.home_goals == null || f.away_goals == null) return null
    const isHome = f.home_team === teamName
    if (f.home_goals === f.away_goals) return 'D'
    const teamWon = (isHome && f.home_winner) || (!isHome && !f.home_winner)
    return teamWon ? 'W' : 'L'
  }

  // Sort squad by number
  const sortedSquad = [...squad].sort((a, b) => (a.number ?? 99) - (b.number ?? 99))

  const pos = standing?.rank ?? null
  const formStr = standing?.form ?? ''

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors group"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
        Back to {leagueName}
      </button>

      {/* Header card */}
      <div className="glass-card p-6 rounded-2xl border border-white/5">
        <div className="flex items-start gap-5 flex-wrap">
          {/* Logo */}
          {teamLogo ? (
            <img src={teamLogo} alt={teamName} className="w-20 h-20 object-contain" />
          ) : (
            <div className="w-20 h-20 rounded-2xl bg-slate-800 flex items-center justify-center">
              <Shield className="w-10 h-10 text-slate-600" />
            </div>
          )}

          {/* Name + meta */}
          <div className="flex-1 min-w-0">
            <h1 className="text-3xl font-black text-white leading-tight">{teamName}</h1>
            <div className="flex items-center gap-2 mt-1">
              <MapPin className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-sm text-slate-400">{leagueName} · {seasonLabel(season)}</span>
            </div>

            {/* PL history button */}
            {internalTeamId && (
              <button
                onClick={() => onViewFullHistory(internalTeamId)}
                className="mt-3 flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs font-bold text-indigo-400 hover:bg-indigo-500/20 transition-colors"
              >
                <History className="w-3.5 h-3.5" />
                View 10-Season History
              </button>
            )}
          </div>

          {/* Position badge */}
          {pos && (
            <div className={`px-4 py-2 rounded-2xl border text-center min-w-[80px] ${POS_BADGE(pos)}`}>
              <p className="text-2xl font-black">{ordinal(pos)}</p>
              <p className="text-[10px] font-bold uppercase tracking-wider opacity-70 mt-0.5">Position</p>
            </div>
          )}
        </div>
      </div>

      {/* Stats row */}
      {standing && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Points',  value: standing.points,                                           sub: `${standing.played} played` },
            { label: 'Record',  value: `${standing.wins}–${standing.draws}–${standing.losses}`,   sub: 'W – D – L' },
            { label: 'Goals',   value: `${standing.goals_for} / ${standing.goals_against}`,        sub: 'For / Against' },
            { label: 'GD',      value: (standing.goals_diff ?? 0) > 0 ? `+${standing.goals_diff}` : standing.goals_diff, sub: 'Goal difference' },
          ].map(({ label, value, sub }) => (
            <div key={label} className="glass-card p-4 rounded-2xl border border-white/5 text-center">
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">{label}</p>
              <p className="text-2xl font-black text-white">{value}</p>
              <p className="text-[11px] text-slate-600 mt-0.5">{sub}</p>
            </div>
          ))}
        </div>
      )}

      {/* Form strip */}
      {formStr && (
        <div className="glass-card p-5 rounded-2xl border border-white/5">
          <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-3">Recent Form</h3>
          <div className="flex items-center gap-2">
            {formStr.split('').map((r, i) => (
              <span key={i} className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-black ${RESULT_STYLE[r as 'W' | 'L' | 'D'] ?? 'bg-slate-700 text-slate-200'}`}>
                {r}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recent fixtures */}
      <div className="glass-card p-5 rounded-2xl border border-white/5">
        <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-4">Recent Matches</h3>
        {fixturesLoad ? (
          <div className="flex justify-center py-8">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : fixtures.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-6">No fixtures found.</p>
        ) : (
          <div className="space-y-2">
            {[...fixtures].reverse().map((f, i) => {
              const res = getResult(f)
              const isHome = f.home_team === teamName
              const opponent = isHome ? f.away_team : f.home_team
              const oppLogo  = isHome ? f.away_logo  : f.home_logo
              const gf = isHome ? f.home_goals : f.away_goals
              const ga = isHome ? f.away_goals : f.home_goals
              const finished = ['FT', 'AET', 'PEN'].includes(f.status_short ?? '')

              return (
                <div key={f.fixture_id ?? i} className="flex items-center gap-3 text-xs font-semibold p-2.5 rounded-xl bg-slate-900/40 border border-white/5">
                  <span className="text-slate-500 w-20 shrink-0">
                    {f.date ? new Date(f.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) : '—'}
                  </span>
                  <span className="text-slate-500 shrink-0">{isHome ? 'vs' : '@'}</span>
                  <span className="flex items-center gap-1.5 flex-1 min-w-0">
                    {oppLogo && <img src={oppLogo} alt="" className="w-4 h-4 object-contain shrink-0" />}
                    <span className="truncate text-indigo-400 font-semibold">{opponent}</span>
                  </span>
                  {finished && res && gf != null && ga != null ? (
                    <span className={`px-2 py-0.5 rounded font-bold shrink-0 ${
                      res === 'W' ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/20' :
                      res === 'L' ? 'bg-rose-950/40   text-rose-400   border border-rose-500/20'    :
                                   'bg-amber-950/40  text-amber-400  border border-amber-500/20'
                    }`}>{gf}–{ga} ({res})</span>
                  ) : (
                    <span className="text-slate-500 shrink-0">{f.status_short ?? '—'}</span>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Squad */}
      <div>
        <h3 className="text-lg font-black text-white mb-4">Current Squad</h3>
        {squadLoad ? (
          <div className="glass-card p-10 rounded-2xl border border-white/5 flex justify-center">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : squad.length === 0 ? (
          <div className="glass-card p-10 rounded-2xl border border-white/5 text-center text-slate-500">
            <Shield className="w-10 h-10 mx-auto mb-3 text-slate-700" />
            <p className="font-semibold">Squad not yet available</p>
            <p className="text-sm mt-1 text-slate-600">
              Map this team's <code className="text-slate-500">api_football_id</code> to enable squad data.
            </p>
          </div>
        ) : (
          <div className="glass-card rounded-2xl border border-white/5 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10 bg-slate-900/50">
                    <th className="px-4 py-3 text-left text-[11px] font-bold uppercase tracking-wider text-slate-400">#</th>
                    <th className="px-4 py-3 text-left text-[11px] font-bold uppercase tracking-wider text-slate-400">Player</th>
                    <th className="px-4 py-3 text-left text-[11px] font-bold uppercase tracking-wider text-slate-400">Position</th>
                    <th className="px-4 py-3 text-center text-[11px] font-bold uppercase tracking-wider text-slate-400">Age</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedSquad.map((p) => {
                    const isUnavailable = unavailablePlayers.has(p.id)
                    return (
                      <tr key={p.id ?? p.name} className={`border-b border-white/5 transition-colors ${isUnavailable ? 'hover:bg-white/[0.01]' : 'hover:bg-white/[0.02]'}`}>
                        <td className="px-4 py-3 text-slate-400 font-semibold">{p.number ?? '—'}</td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => onPlayerClick && p.id && lookupPlayerAndNavigate(p.id, p.name)}
                            disabled={isUnavailable}
                            title={isUnavailable ? 'This player is not available in our Premier League database' : undefined}
                            className={`flex items-center gap-2 transition-colors group ${isUnavailable ? 'opacity-60 cursor-not-allowed' : 'hover:text-indigo-400'}`}
                          >
                            {p.photo ? (
                              <img src={p.photo} alt={p.name} className="w-7 h-7 rounded-full object-cover border border-white/10" />
                            ) : (
                              <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center">
                                <Shield className="w-3.5 h-3.5 text-slate-600" />
                              </div>
                            )}
                            <span className={`font-semibold ${isUnavailable ? 'text-slate-500' : 'text-white group-hover:text-indigo-400'} transition-colors`}>{p.name}</span>
                          </button>
                        </td>
                        <td className="px-4 py-3 text-slate-400">{p.position ?? '—'}</td>
                        <td className="px-4 py-3 text-center text-slate-400">{p.age ?? '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
