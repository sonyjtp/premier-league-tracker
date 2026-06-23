import React, { useState, useEffect } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { ArrowLeft, MapPin, Calendar, Shield } from 'lucide-react'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Team      { id: number; name: string; short_name: string; api_football_id: number | null }
interface Profile   { logo_url: string | null; country: string | null; founded: number | null; venue_name: string | null }
interface Standing  { position: number; points: number; played: number; wins: number; draws: number; losses: number; goals_for: number; goals_against: number; goal_difference: number }
interface FormMatch { opponent_name: string; is_home: boolean; goals_for: number; goals_against: number; result: string; match_date: string; shots: number | null; shots_on_target: number | null; xg: number | null }
interface HistoryItem { season_id: number; season_label: string; final_position: number; points: number; played: number; wins: number; draws: number; losses: number; goals_for: number; goals_against: number; goal_difference: number }

interface Overview {
  team: Team
  profile: Profile | null
  current_season_id: number | null
  current_standing: Standing | null
  form_string: string
  recent_matches: FormMatch[]
  season_history: HistoryItem[]
}

interface SquadPlayer {
  id: number | null
  name: string
  age: number | null
  number: number | null
  position: string | null
  photo: string | null
}

interface Season { id: number; label: string }

interface Props {
  teamId: number
  seasons: Season[]
  onBack: () => void
  logoFallback?: string | null
  onTeamClick?: (teamId: number) => void
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const RESULT_STYLE = {
  W: 'bg-emerald-600 text-white',
  L: 'bg-rose-600   text-white',
  D: 'bg-amber-500  text-slate-900',
}

const positionColor = (pos: number) =>
  pos === 1        ? 'text-yellow-400' :
  pos <= 4         ? 'text-emerald-400' :
  pos === 5        ? 'text-blue-400'    :
  pos >= 18        ? 'text-rose-400'    :
                     'text-slate-200'

const posBadge = (pos: number) =>
  pos === 1        ? 'bg-yellow-500/10  text-yellow-400  border-yellow-500/20'  :
  pos <= 4         ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
  pos === 5        ? 'bg-blue-500/10    text-blue-400    border-blue-500/20'    :
  pos >= 18        ? 'bg-rose-500/10    text-rose-400    border-rose-500/20'    :
                     'bg-slate-800      text-slate-300   border-white/5'

const ordinal = (n: number) => {
  const s = ['th','st','nd','rd']
  const v = n % 100
  return n + (s[(v - 20) % 10] ?? s[v] ?? s[0])
}

// ── Component ─────────────────────────────────────────────────────────────────

export const TeamPage: React.FC<Props> = ({ teamId, seasons, onBack, logoFallback }) => {
  const [overview,   setOverview]   = useState<Overview | null>(null)
  const [squad,      setSquad]      = useState<SquadPlayer[]>([])
  const [seasonId,   setSeasonId]   = useState<number | null>(null)
  const [loading,    setLoading]    = useState(true)
  const [squadLoad,  setSquadLoad]  = useState(false)

  // Fetch overview (re-runs when seasonId changes)
  useEffect(() => {
    setLoading(true)
    const url = seasonId
      ? `/api/teams/${teamId}/overview?season_id=${seasonId}`
      : `/api/teams/${teamId}/overview`
    fetch(url)
      .then(r => r.json())
      .then(data => {
        setOverview(data)
        if (!seasonId) setSeasonId(data.current_season_id)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [teamId, seasonId])

  // Fetch squad once (when overview is loaded)
  useEffect(() => {
    if (!overview?.team) return
    setSquadLoad(true)
    fetch(`/api/teams/${teamId}/squad`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(data => {
        setSquad(Array.isArray(data) ? data : [])
        setSquadLoad(false)
      })
      .catch(err => {
        console.error('Squad fetch error:', err)
        setSquad([])
        setSquadLoad(false)
      })
  }, [teamId, overview?.team?.id])

  // Chart data: position per season (reversed y-axis — 1 is best)
  const historyChartData = overview?.season_history
    .slice()
    .reverse()
    .map(h => ({ season: h.season_label.replace('-', '–'), position: h.final_position }))

  // Group squad by position
  const grouped = squad.reduce<Record<string, SquadPlayer[]>>((acc, p) => {
    const pos = p.position ?? 'Unknown'
    acc[pos] = [...(acc[pos] ?? []), p]
    return acc
  }, {})
  const posOrder = ['Goalkeeper', 'Defender', 'Midfielder', 'Attacker']
  const groupedOrdered = posOrder
    .filter(p => grouped[p])
    .map(p => ({ position: p, players: grouped[p].sort((a, b) => (a.number ?? 99) - (b.number ?? 99)) }))

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-40 gap-4">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 text-sm">Loading team…</p>
      </div>
    )
  }

  if (!overview) {
    return (
      <div className="text-center py-40 text-slate-500">Team not found.</div>
    )
  }

  const { team, profile, current_standing: cs, form_string, recent_matches, season_history } = overview

  return (
    <div className="space-y-6">
      {/* Back button + header */}
      <div>
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors mb-5 group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
          Back
        </button>

        <div className="glass-card p-6 rounded-2xl border border-white/5">
          <div className="flex items-start gap-5 flex-wrap">
            {/* Logo */}
            {(profile?.logo_url ?? logoFallback) ? (
              <img src={(profile?.logo_url ?? logoFallback)!} alt={team.name} className="w-20 h-20 object-contain" />
            ) : (
              <div className="w-20 h-20 rounded-2xl bg-slate-800 flex items-center justify-center">
                <Shield className="w-10 h-10 text-slate-600" />
              </div>
            )}

            {/* Name & meta */}
            <div className="flex-1 min-w-0">
              <h1 className="text-3xl font-black text-white leading-tight">{team.name}</h1>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2">
                {profile?.venue_name && (
                  <span className="flex items-center gap-1.5 text-sm text-slate-400">
                    <MapPin className="w-3.5 h-3.5 text-slate-500" />{profile.venue_name}
                  </span>
                )}
                {profile?.founded && (
                  <span className="flex items-center gap-1.5 text-sm text-slate-400">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" />Est. {profile.founded}
                  </span>
                )}
                {profile?.country && (
                  <span className="text-sm text-slate-500">{profile.country}</span>
                )}
              </div>

              {/* Season picker */}
              <div className="flex items-center gap-3 mt-4">
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Season</label>
                <select
                  value={seasonId ?? ''}
                  onChange={e => setSeasonId(Number(e.target.value))}
                  className="bg-slate-900 border border-white/5 rounded-xl px-3 py-1.5 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors"
                >
                  {seasons.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                </select>
              </div>
            </div>

            {/* Current position badge */}
            {cs && (
              <div className={`px-4 py-2 rounded-2xl border text-center min-w-[80px] ${posBadge(cs.position)}`}>
                <p className="text-2xl font-black">{ordinal(cs.position)}</p>
                <p className="text-[10px] font-bold uppercase tracking-wider opacity-70 mt-0.5">Position</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Key stats row */}
      {cs && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Points',  value: cs.points,                      sub: `${cs.played} played` },
            { label: 'Record',  value: `${cs.wins}–${cs.draws}–${cs.losses}`, sub: 'W – D – L' },
            { label: 'Goals',   value: `${cs.goals_for} / ${cs.goals_against}`, sub: 'For / Against' },
            { label: 'GD',      value: cs.goal_difference > 0 ? `+${cs.goal_difference}` : cs.goal_difference, sub: 'Goal difference' },
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
      {form_string && (
        <div className="glass-card p-5 rounded-2xl border border-white/5">
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Form</h3>
          <div className="flex items-center gap-2 flex-wrap">
            {form_string.split('').map((r, i) => (
              <span key={i} className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-black ${RESULT_STYLE[r as 'W' | 'L' | 'D'] ?? 'bg-slate-700 text-slate-200'}`}>
                {r}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recent matches */}
      {recent_matches.length > 0 && (
        <div className="glass-card p-5 rounded-2xl border border-white/5">
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Last 10 Matches</h3>
          <div className="space-y-2">
            {recent_matches.map((m, i) => (
              <div key={i} className="flex items-center gap-3 text-xs font-semibold p-2.5 rounded-xl bg-slate-900/40 border border-white/5">
                <span className="text-slate-500 w-20 shrink-0">
                  {new Date(m.match_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
                </span>
                <span className="text-slate-500 shrink-0">{m.is_home ? 'vs' : '@'}</span>
                <button
                  className="flex-1 text-left font-semibold text-indigo-400 hover:text-indigo-300 transition-colors truncate"
                  onClick={() => {
                    // opponent click — not wired yet (no opponent teamId available here)
                  }}
                >
                  {m.opponent_name}
                </button>
                {m.xg != null && (
                  <span className="text-slate-600 hidden sm:inline">xG {m.xg.toFixed(2)}</span>
                )}
                <span className={`px-2 py-0.5 rounded font-bold shrink-0 ${
                  m.result === 'W' ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/20' :
                  m.result === 'L' ? 'bg-rose-950/40   text-rose-400   border border-rose-500/20'    :
                                     'bg-amber-950/40  text-amber-400  border border-amber-500/20'
                }`}>
                  {m.goals_for}–{m.goals_against} ({m.result})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Season history */}
      {season_history.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-black text-white">Season History</h3>

          {/* Position chart */}
          {historyChartData && historyChartData.length > 1 && (
            <div className="glass-card p-5 rounded-2xl border border-white/5 h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historyChartData} margin={{ top: 5, right: 10, left: -30, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="season" stroke="#64748b" fontSize={10} fontWeight={600} tickLine={false} />
                  <YAxis reversed domain={[1, 20]} tickCount={10} stroke="#64748b" fontSize={10} fontWeight={600} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px', fontSize: '12px' }}
                    formatter={(v: unknown) => [`${ordinal(Number(v))} place`, 'Position']}
                  />
                  <Line type="monotone" dataKey="position" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 4, fill: '#6366f1' }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* History table */}
          <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/5 bg-slate-900/50 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    <th className="py-3 px-4">Season</th>
                    <th className="py-3 px-3 text-center">Pos</th>
                    <th className="py-3 px-3 text-center text-indigo-400">Pts</th>
                    <th className="py-3 px-3 text-center">MP</th>
                    <th className="py-3 px-3 text-center">W</th>
                    <th className="py-3 px-3 text-center">D</th>
                    <th className="py-3 px-3 text-center">L</th>
                    <th className="py-3 px-3 text-center">GF</th>
                    <th className="py-3 px-3 text-center">GA</th>
                    <th className="py-3 px-3 text-center">GD</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04] text-sm text-slate-300">
                  {season_history.map(h => (
                    <tr
                      key={h.season_id}
                      onClick={() => setSeasonId(h.season_id)}
                      className={`hover:bg-white/[0.03] cursor-pointer transition-colors ${h.season_id === seasonId ? 'bg-indigo-500/5' : ''}`}
                    >
                      <td className="py-3 px-4 font-semibold text-white">{h.season_label}</td>
                      <td className={`py-3 px-3 text-center font-black tabular-nums ${positionColor(h.final_position)}`}>
                        {ordinal(h.final_position)}
                      </td>
                      <td className="py-3 px-3 text-center font-black text-indigo-400 tabular-nums">{h.points}</td>
                      <td className="py-3 px-3 text-center tabular-nums">{h.played}</td>
                      <td className="py-3 px-3 text-center tabular-nums text-emerald-400 font-semibold">{h.wins}</td>
                      <td className="py-3 px-3 text-center tabular-nums">{h.draws}</td>
                      <td className="py-3 px-3 text-center tabular-nums text-rose-400/80">{h.losses}</td>
                      <td className="py-3 px-3 text-center tabular-nums">{h.goals_for}</td>
                      <td className="py-3 px-3 text-center tabular-nums">{h.goals_against}</td>
                      <td className={`py-3 px-3 text-center tabular-nums font-semibold ${h.goal_difference > 0 ? 'text-emerald-400' : h.goal_difference < 0 ? 'text-rose-400' : 'text-slate-400'}`}>
                        {h.goal_difference > 0 ? `+${h.goal_difference}` : h.goal_difference}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <p className="text-[11px] text-slate-600 px-1">Click a row to load that season's stats above.</p>
        </div>
      )}

      {/* Squad */}
      <div>
        <h3 className="text-lg font-black text-white mb-4">Current Squad</h3>
        {squadLoad ? (
          <div className="glass-card p-10 rounded-2xl border border-white/5 flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : squad.length > 0 ? (
          <div className="space-y-6">
            {groupedOrdered.map(({ position, players }) => (
              <div key={position}>
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-3 px-1">{position}s</h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {players.map(p => (
                    <div key={p.id ?? p.name} className="glass-card p-3 rounded-xl border border-white/5 flex items-center gap-3">
                      {p.photo ? (
                        <img src={p.photo} alt={p.name} className="w-10 h-10 rounded-full object-cover border border-white/10 shrink-0" />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center shrink-0">
                          <Shield className="w-5 h-5 text-slate-600" />
                        </div>
                      )}
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-white truncate">{p.name}</p>
                        <p className="text-[10px] text-slate-500 font-semibold">
                          {p.number != null ? `#${p.number}` : ''}
                          {p.age != null ? ` · ${p.age}y` : ''}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="glass-card p-10 rounded-2xl border border-white/5 text-center text-slate-500">
            <Shield className="w-10 h-10 mx-auto mb-3 text-slate-700" />
            <p className="font-semibold">Squad not yet available</p>
            <p className="text-sm mt-1 text-slate-600">
              Map this team's <code className="text-slate-500">api_football_id</code> and run{' '}
              <code className="text-slate-500">POST /api/admin/sync/player-profiles</code> to populate squad data.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
