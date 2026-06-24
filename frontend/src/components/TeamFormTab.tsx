import React, { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { BarChart2 } from 'lucide-react'
import { useSettings } from '../contexts/SettingsContext'

interface Season { id: number; label: string }
interface Team   { id: number; name: string; short_name: string }

interface MatchFormItem {
  opponent_name: string
  is_home: boolean
  goals_for: number
  goals_against: number
  result: string
  match_date: string
  shots: number | null
  shots_on_target: number | null
  xg: number | null
}

interface TeamFormResponse {
  team: Team
  form_string: string
  matches: MatchFormItem[]
}

interface H2HMatch {
  match_date: string
  season_label: string
  home_team: string
  away_team: string
  home_goals: number
  away_goals: number
  result: string
}

interface Props {
  seasons: Season[]
  selectedSeasonId: number
  setSelectedSeasonId: (id: number) => void
  onTeamClick: (teamId: number) => void
}

export const TeamFormTab: React.FC<Props> = ({ seasons, selectedSeasonId, setSelectedSeasonId, onTeamClick }) => {
  const { settings } = useSettings()
  const [teams,      setTeams]      = useState<Team[]>([])
  const [team1Id,    setTeam1Id]    = useState(0)
  const [team2Id,    setTeam2Id]    = useState(0)
  const [form1,      setForm1]      = useState<TeamFormResponse | null>(null)
  const [form2,      setForm2]      = useState<TeamFormResponse | null>(null)
  const [lastX,      setLastX]      = useState(10)
  const [loading,    setLoading]    = useState(false)
  const [h2h,        setH2h]        = useState<H2HMatch[]>([])

  useEffect(() => {
    if (!selectedSeasonId) return
    fetch(`/api/teams?season_id=${selectedSeasonId}`)
      .then(r => r.json())
      .then(data => {
        setTeams(data)
        // Apply default team as Team A; pick another team as Team B
        const defId = settings.defaultTeamInternalId
        const defaultTeam = defId ? data.find((t: Team) => t.id === defId) : null
        const first  = defaultTeam ?? data[0]
        const second = data.find((t: Team) => t.id !== first?.id)
        if (first)  setTeam1Id(first.id)
        if (second) setTeam2Id(second.id)
      })
      .catch(console.error)
  }, [selectedSeasonId])

  useEffect(() => {
    if (!selectedSeasonId || !team1Id || !team2Id) return
    setLoading(true)
    Promise.all([
      fetch(`/api/teams/${team1Id}/form?season_id=${selectedSeasonId}&last_x=${lastX}`).then(r => r.json()),
      fetch(`/api/teams/${team2Id}/form?season_id=${selectedSeasonId}&last_x=${lastX}`).then(r => r.json()),
    ]).then(([d1, d2]) => { setForm1(d1); setForm2(d2); setLoading(false) })
      .catch(() => setLoading(false))
  }, [team1Id, team2Id, selectedSeasonId, lastX])

  // Head-to-head
  useEffect(() => {
    if (!team1Id || !team2Id || team1Id === team2Id) return
    fetch(`/api/head2head?team_a=${team1Id}&team_b=${team2Id}&limit=5`)
      .then(r => r.json())
      .then(data => setH2h(Array.isArray(data) ? data : []))
      .catch(() => setH2h([]))
  }, [team1Id, team2Id])

  // H2H record from team1's perspective
  const h2hRecord = h2h.reduce(
    (acc, m) => {
      const team1IsHome = teams.find(t => t.id === team1Id)?.name === m.home_team
      const team1Won = (team1IsHome && m.result === 'H') || (!team1IsHome && m.result === 'A')
      const draw = m.result === 'D'
      return {
        w: acc.w + (team1Won ? 1 : 0),
        d: acc.d + (draw ? 1 : 0),
        l: acc.l + (!team1Won && !draw ? 1 : 0),
      }
    },
    { w: 0, d: 0, l: 0 }
  )

  const formBubbles = (str: string) => (
    <div className="flex gap-1.5 justify-center mt-2">
      {str.split('').map((r, i) => (
        <span key={i} className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-black ${
          r === 'W' ? 'bg-emerald-600 text-white' :
          r === 'L' ? 'bg-rose-600 text-white' :
                      'bg-amber-500 text-slate-900'
        }`}>{r}</span>
      ))}
    </div>
  )

  const chartData = (() => {
    if (!form1 || !form2) return []
    const avg = (ms: MatchFormItem[], key: keyof MatchFormItem) => {
      const valid = ms.filter(m => m[key] != null)
      if (!valid.length) return 0
      return Number((valid.reduce((s, m) => s + (m[key] as number), 0) / valid.length).toFixed(2))
    }
    return [
      { name: 'Goals',           [form1.team.name]: avg(form1.matches, 'goals_for'),       [form2.team.name]: avg(form2.matches, 'goals_for') },
      { name: 'xG',              [form1.team.name]: avg(form1.matches, 'xg'),              [form2.team.name]: avg(form2.matches, 'xg') },
      { name: 'Shots',           [form1.team.name]: avg(form1.matches, 'shots'),           [form2.team.name]: avg(form2.matches, 'shots') },
      { name: 'Shots on Target', [form1.team.name]: avg(form1.matches, 'shots_on_target'), [form2.team.name]: avg(form2.matches, 'shots_on_target') },
    ].filter(row => (row[form1.team.name] as number) > 0 || (row[form2.team.name] as number) > 0)
  })()

  const matchRow = (m: MatchFormItem, accent: string) => (
    <div key={m.match_date + m.opponent_name} className="flex items-center gap-3 text-xs font-semibold p-2.5 rounded-xl bg-slate-900/40 border border-white/5">
      <span className="text-slate-500 shrink-0 w-20">{new Date(m.match_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}</span>
      <span className="flex-1 text-white truncate">
        <span className="text-slate-500">{m.is_home ? 'vs' : '@'}</span> <strong style={{ color: accent }}>{m.opponent_name}</strong>
      </span>
      <div className="flex flex-col items-end gap-0.5 shrink-0">
        <span className={`px-2 py-0.5 rounded font-bold text-[11px] ${
          m.result === 'W' ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/20' :
          m.result === 'L' ? 'bg-rose-950/40   text-rose-400   border border-rose-500/20'    :
                             'bg-amber-950/40  text-amber-400  border border-amber-500/20'
        }`}>{m.goals_for}–{m.goals_against} ({m.result})</span>
        {m.xg != null && <span className="text-[10px] text-slate-600">xG {m.xg.toFixed(2)}</span>}
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <BarChart2 className="w-5 h-5 text-indigo-400" />
          <h2 className="text-2xl font-black text-white">Team Form</h2>
        </div>
        <p className="text-sm text-slate-500">Compare recent form, stats, and head-to-head record between two clubs.</p>
      </div>

      {/* Controls */}
      <div className="glass-card p-5 rounded-2xl grid grid-cols-2 md:grid-cols-4 gap-4 border border-white/5">
        {[
          { label: 'Season',      value: selectedSeasonId, onChange: (v: number) => setSelectedSeasonId(v), options: seasons.map(s => ({ value: s.id, label: s.label })) },
          { label: 'Team A',      value: team1Id,          onChange: (v: number) => setTeam1Id(v),          options: teams.map(t => ({ value: t.id, label: t.name, disabled: t.id === team2Id })) },
          { label: 'Team B',      value: team2Id,          onChange: (v: number) => setTeam2Id(v),          options: teams.map(t => ({ value: t.id, label: t.name, disabled: t.id === team1Id })) },
          { label: 'Last X Games', value: lastX,           onChange: (v: number) => setLastX(v),            options: [{ value: 5, label: 'Last 5' }, { value: 10, label: 'Last 10' }, { value: 15, label: 'Last 15' }] },
        ].map(({ label, value, onChange, options }) => (
          <div key={label} className="flex flex-col gap-1">
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</label>
            <select
              value={value}
              onChange={e => onChange(Number(e.target.value))}
              className="bg-slate-900 border border-white/5 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors w-full"
            >
              {options.map((o: any) => <option key={o.value} value={o.value} disabled={o.disabled}>{o.label}</option>)}
            </select>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="glass-card p-20 flex flex-col items-center justify-center gap-4 rounded-2xl border border-white/5">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Loading form data…</p>
        </div>
      ) : form1 && form2 ? (
        <div className="space-y-6">
          {/* Form overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { form: form1, accent: 'bg-indigo-500' },
              { form: form2, accent: 'bg-rose-500'   },
            ].map(({ form, accent }) => (
              <div key={form.team.id} className="glass-card p-5 rounded-2xl border border-white/5 text-center relative overflow-hidden">
                <div className={`absolute top-0 left-0 w-full h-1 ${accent}`} />
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">{form.team.short_name}</p>
                <button onClick={() => onTeamClick(form.team.id)} className="text-lg font-black text-white mt-0.5 hover:text-indigo-400 transition-colors">
                  {form.team.name}
                </button>
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mt-2">Last {lastX} matches</p>
                {formBubbles(form.form_string)}
              </div>
            ))}
          </div>

          {/* Head-to-head record */}
          {h2h.length > 0 && (
            <div className="glass-card p-5 rounded-2xl border border-white/5">
              <h4 className="font-bold text-white mb-4 text-sm">Head-to-Head Record (last {h2h.length} meetings)</h4>
              <div className="flex items-center gap-4 mb-5">
                <div className="flex-1 text-center">
                  <p className="text-3xl font-black text-indigo-400">{h2hRecord.w}</p>
                  <p className="text-[11px] text-slate-500 font-bold uppercase tracking-wider mt-1">{form1.team.short_name} Wins</p>
                </div>
                <div className="flex-1 text-center border-x border-white/5">
                  <p className="text-3xl font-black text-slate-400">{h2hRecord.d}</p>
                  <p className="text-[11px] text-slate-500 font-bold uppercase tracking-wider mt-1">Draws</p>
                </div>
                <div className="flex-1 text-center">
                  <p className="text-3xl font-black text-rose-400">{h2hRecord.l}</p>
                  <p className="text-[11px] text-slate-500 font-bold uppercase tracking-wider mt-1">{form2.team.short_name} Wins</p>
                </div>
              </div>
              <div className="space-y-2">
                {h2h.map((m, i) => {
                  const team1Name = teams.find(t => t.id === team1Id)?.name ?? ''
                  const team1IsHome = m.home_team === team1Name
                  const res = m.result === 'D' ? 'D' : (team1IsHome && m.result === 'H') || (!team1IsHome && m.result === 'A') ? 'W' : 'L'
                  return (
                    <div key={i} className="flex items-center gap-2 text-xs font-semibold p-2.5 rounded-xl bg-slate-900/40 border border-white/5">
                      <span className="text-slate-500 shrink-0 hidden sm:inline">{m.season_label}</span>
                      <span className="text-slate-300 flex-1 truncate text-center min-w-0">{m.home_team} <span className="text-slate-600">vs</span> {m.away_team}</span>
                      <span className={`shrink-0 px-2 py-0.5 rounded font-bold ${
                        res === 'W' ? 'text-emerald-400 bg-emerald-950/30 border border-emerald-500/20' :
                        res === 'L' ? 'text-rose-400   bg-rose-950/30   border border-rose-500/20'    :
                                     'text-amber-400  bg-amber-950/30  border border-amber-500/20'
                      }`}>{m.home_goals}–{m.away_goals}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Stats chart */}
          {chartData.length > 0 && (
            <div className="glass-card p-5 rounded-2xl border border-white/5 h-72 flex flex-col">
              <h4 className="font-bold text-white mb-4 text-sm">Avg per Match — Last {lastX}</h4>
              <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" stroke="#64748b" fontSize={11} fontWeight={600} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} fontWeight={600} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px', fontSize: '12px' }} />
                    <Legend />
                    <Bar dataKey={form1.team.name} fill="#6366f1" radius={[4, 4, 0, 0]} />
                    <Bar dataKey={form2.team.name} fill="#f43f5e" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Recent results */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { form: form1, accent: '#818cf8' },
              { form: form2, accent: '#fb7185' },
            ].map(({ form, accent }) => (
              <div key={form.team.id} className="glass-card p-5 rounded-2xl border border-white/5 space-y-3">
                <h4 className="font-bold text-white text-sm border-b border-white/5 pb-2">
                  {form.team.name} — Recent Results
                </h4>
                <div className="space-y-2">
                  {form.matches.map(m => matchRow(m, accent))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="glass-card p-20 rounded-2xl text-center border border-white/5 text-slate-500">
          Select two teams above to compare their form.
        </div>
      )}
    </div>
  )
}
