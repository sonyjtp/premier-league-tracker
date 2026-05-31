import React, { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface Season {
  id: number
  label: string
}

interface Team {
  id: number
  name: string
  short_name: string
}

interface MatchFormItem {
  opponent_name: string
  is_home: boolean
  goals_for: number
  goals_against: number
  result: string
  match_date: string
  shots: number | null
  shots_on_target: number | null
}

interface TeamFormResponse {
  team: Team
  form_string: string
  matches: MatchFormItem[]
}

interface TeamFormTabProps {
  seasons: Season[]
  selectedSeasonId: number
  setSelectedSeasonId: (id: number) => void
}

export const TeamFormTab: React.FC<TeamFormTabProps> = ({
  seasons,
  selectedSeasonId,
  setSelectedSeasonId,
}) => {
  const [teams, setTeams] = useState<Team[]>([])
  const [team1Id, setTeam1Id] = useState<number>(0)
  const [team2Id, setTeam2Id] = useState<number>(0)
  
  const [form1, setForm1] = useState<TeamFormResponse | null>(null)
  const [form2, setForm2] = useState<TeamFormResponse | null>(null)
  const [lastX, setLastX] = useState<number>(5)
  const [loading, setLoading] = useState<boolean>(false)

  // Fetch all teams for the selected season
  useEffect(() => {
    if (!selectedSeasonId) return

    fetch(`http://localhost:8000/api/teams?season_id=${selectedSeasonId}`)
      .then((res) => res.json())
      .then((data) => {
        setTeams(data)
        if (data.length >= 2) {
          setTeam1Id(data[0].id)
          setTeam2Id(data[1].id)
        }
      })
      .catch((err) => console.error(err))
  }, [selectedSeasonId])

  // Fetch form data for both teams when selection changes
  useEffect(() => {
    if (!selectedSeasonId || !team1Id || !team2Id) return

    setLoading(true)
    
    const p1 = fetch(`http://localhost:8000/api/teams/${team1Id}/form?season_id=${selectedSeasonId}&last_x=${lastX}`)
      .then((res) => res.json())
    
    const p2 = fetch(`http://localhost:8000/api/teams/${team2Id}/form?season_id=${selectedSeasonId}&last_x=${lastX}`)
      .then((res) => res.json())

    Promise.all([p1, p2])
      .then(([data1, data2]) => {
        setForm1(data1)
        setForm2(data2)
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setLoading(false)
      })
  }, [team1Id, team2Id, selectedSeasonId, lastX])

  const renderFormBubbles = (formStr: string) => {
    return (
      <div className="flex gap-1.5 justify-center mt-2">
        {formStr.split("").map((res, i) => {
          let color = "bg-slate-700 text-slate-200"
          if (res === "W") color = "bg-emerald-600 text-white"
          if (res === "L") color = "bg-rose-600 text-white"
          if (res === "D") color = "bg-amber-500 text-slate-900"
          
          return (
            <span
              key={i}
              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shadow-md shadow-black/10 ${color}`}
            >
              {res}
            </span>
          )
        })}
      </div>
    )
  }

  // Calculate stats for chart
  const getChartData = () => {
    if (!form1 || !form2) return []

    const calcAvg = (matches: MatchFormItem[], key: "goals_for" | "shots" | "shots_on_target") => {
      const valid = matches.filter((m) => m[key] !== null)
      if (valid.length === 0) return 0
      const sum = valid.reduce((acc, m) => acc + (m[key] as number), 0)
      return Number((sum / valid.length).toFixed(2))
    }

    return [
      {
        name: 'Avg Goals',
        [form1.team.name]: calcAvg(form1.matches, 'goals_for'),
        [form2.team.name]: calcAvg(form2.matches, 'goals_for'),
      },
      {
        name: 'Avg Shots',
        [form1.team.name]: calcAvg(form1.matches, 'shots'),
        [form2.team.name]: calcAvg(form2.matches, 'shots'),
      },
      {
        name: 'Avg Shots on Target',
        [form1.team.name]: calcAvg(form1.matches, 'shots_on_target'),
        [form2.team.name]: calcAvg(form2.matches, 'shots_on_target'),
      },
    ]
  }

  const statChartData = getChartData()

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="glass-card p-6 rounded-2xl grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
        {/* Season Selector */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Season</label>
          <select
            value={selectedSeasonId}
            onChange={(e) => setSelectedSeasonId(Number(e.target.value))}
            className="bg-slate-900 border border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors w-full"
          >
            {seasons.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {/* Team 1 Selector */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Team A</label>
          <select
            value={team1Id}
            onChange={(e) => setTeam1Id(Number(e.target.value))}
            className="bg-slate-900 border border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors w-full"
          >
            {teams.map((t) => (
              <option key={t.id} value={t.id} disabled={t.id === team2Id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        {/* Team 2 Selector */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Team B</label>
          <select
            value={team2Id}
            onChange={(e) => setTeam2Id(Number(e.target.value))}
            className="bg-slate-900 border border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors w-full"
          >
            {teams.map((t) => (
              <option key={t.id} value={t.id} disabled={t.id === team1Id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        {/* Match Count Slider */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Last X Games</label>
          <select
            value={lastX}
            onChange={(e) => setLastX(Number(e.target.value))}
            className="bg-slate-900 border border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors w-full"
          >
            <option value={5}>Last 5 matches</option>
            <option value={10}>Last 10 matches</option>
            <option value={15}>Last 15 matches</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="glass-card p-20 flex flex-col items-center justify-center gap-4 rounded-2xl">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-slate-400 text-sm">Gathering form and metrics...</p>
        </div>
      ) : form1 && form2 ? (
        <div className="space-y-6">
          {/* Form Overview Header Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Team 1 Form Card */}
            <div className="glass-card p-6 rounded-2xl border border-white/5 text-center relative overflow-hidden">
              <div className="absolute top-0 left-0 w-2.5 h-full bg-indigo-500"></div>
              <h3 className="text-lg font-bold text-white mb-1">{form1.team.name}</h3>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Form in last {lastX}</p>
              {renderFormBubbles(form1.form_string)}
            </div>

            {/* Team 2 Form Card */}
            <div className="glass-card p-6 rounded-2xl border border-white/5 text-center relative overflow-hidden">
              <div className="absolute top-0 left-0 w-2.5 h-full bg-rose-500"></div>
              <h3 className="text-lg font-bold text-white mb-1">{form2.team.name}</h3>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Form in last {lastX}</p>
              {renderFormBubbles(form2.form_string)}
            </div>
          </div>

          {/* Stats Bar Chart */}
          <div className="glass-card p-6 rounded-2xl border border-white/5 h-[400px] flex flex-col">
            <h4 className="font-bold text-white mb-6">Metrics Comparison (Last {lastX} Matches Avg)</h4>
            <div className="flex-1 w-full min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={statChartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} fontWeight="600" tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={12} fontWeight="600" tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: 'rgba(255,255,255,0.08)',
                      borderRadius: '12px',
                      color: '#f8fafc',
                    }}
                  />
                  <Legend />
                  <Bar dataKey={form1.team.name} fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey={form2.team.name} fill="#f43f5e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Scoreline Comparison Lists */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Team 1 Matches List */}
            <div className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
              <h4 className="font-bold text-white border-b border-white/5 pb-2">Recent Results ({form1.team.name})</h4>
              <div className="space-y-3">
                {form1.matches.map((m, i) => (
                  <div key={i} className="flex justify-between items-center text-xs font-semibold p-2.5 rounded-xl bg-slate-900/40 border border-white/5">
                    <span className="text-slate-400">{new Date(m.match_date).toLocaleDateString()}</span>
                    <span className="text-white">
                      {m.is_home ? "H" : "A"} vs <strong className="text-indigo-400">{m.opponent_name}</strong>
                    </span>
                    <span className={`px-2.5 py-1 rounded font-bold ${
                      m.result === 'W' ? 'bg-emerald-950/20 text-emerald-400 border border-emerald-500/20' :
                      m.result === 'L' ? 'bg-rose-950/20 text-rose-400 border border-rose-500/20' :
                      'bg-amber-950/20 text-amber-400 border border-amber-500/20'
                    }`}>
                      {m.goals_for} - {m.goals_against} ({m.result})
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Team 2 Matches List */}
            <div className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
              <h4 className="font-bold text-white border-b border-white/5 pb-2">Recent Results ({form2.team.name})</h4>
              <div className="space-y-3">
                {form2.matches.map((m, i) => (
                  <div key={i} className="flex justify-between items-center text-xs font-semibold p-2.5 rounded-xl bg-slate-900/40 border border-white/5">
                    <span className="text-slate-400">{new Date(m.match_date).toLocaleDateString()}</span>
                    <span className="text-white">
                      {m.is_home ? "H" : "A"} vs <strong className="text-rose-400">{m.opponent_name}</strong>
                    </span>
                    <span className={`px-2.5 py-1 rounded font-bold ${
                      m.result === 'W' ? 'bg-emerald-950/20 text-emerald-400 border border-emerald-500/20' :
                      m.result === 'L' ? 'bg-rose-950/20 text-rose-400 border border-rose-500/20' :
                      'bg-amber-950/20 text-amber-400 border border-amber-500/20'
                    }`}>
                      {m.goals_for} - {m.goals_against} ({m.result})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-20 text-slate-500">Failed to load form details.</div>
      )}
    </div>
  )
}
