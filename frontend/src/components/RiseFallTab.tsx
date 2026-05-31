import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Calendar, Info } from 'lucide-react'

interface Season {
  id: number
  label: string
}

interface Team {
  id: number
  name: string
  short_name: string
}

interface RiseFallTabProps {
  seasons: Season[]
  selectedSeasonId: number
  setSelectedSeasonId: (id: number) => void
}

const TEAM_COLORS: { [key: string]: string } = {
  "Arsenal": "#EF0107",
  "Aston Villa": "#95BFE5",
  "Bournemouth": "#B50E12",
  "Brentford": "#E30613",
  "Brighton & Hove Albion": "#0057B8",
  "Burnley": "#6C1D45",
  "Chelsea": "#034694",
  "Crystal Palace": "#1B458F",
  "Everton": "#003399",
  "Fulham": "#000000",
  "Ipswich Town": "#0000FF",
  "Leicester City": "#003090",
  "Liverpool": "#C8102E",
  "Manchester City": "#6CABDD",
  "Manchester United": "#DA291C",
  "Newcastle United": "#241F20",
  "Nottingham Forest": "#DD0000",
  "Southampton": "#D71920",
  "Tottenham Hotspur": "#132257",
  "West Ham United": "#7A263A",
  "Wolverhampton Wanderers": "#FDB913",
  "Leeds United": "#FFCD00",
  "Norwich City": "#FFF200",
  "Watford": "#FBEE23",
  "Sheffield United": "#EE2737",
}

const SEASON_COLORS = [
  "#6366f1", // indigo
  "#f43f5e", // rose
  "#10b981", // emerald
  "#3b82f6", // blue
  "#f59e0b", // amber
  "#8b5cf6", // violet
  "#ec4899", // pink
  "#06b6d4", // cyan
  "#14b8a6", // teal
  "#84cc16"  // lime
]

const GET_COLOR = (name: string, index: number) => {
  if (TEAM_COLORS[name]) return TEAM_COLORS[name]
  return SEASON_COLORS[index % SEASON_COLORS.length]
}

// Custom Tooltip showing date and GW when hovering
const CustomSeasonsTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-950 border border-white/10 p-4 rounded-xl shadow-2xl text-xs font-semibold space-y-3 max-w-[280px]">
        <div className="flex items-center gap-1.5 text-slate-400 font-bold border-b border-white/5 pb-1">
          <Calendar className="w-3.5 h-3.5 text-indigo-400" />
          <span>Round (GW) {label}</span>
        </div>
        
        {payload.map((p: any) => {
          const seasonLabel = p.name
          const data = p.payload
          const position = p.value
          
          const date = data[`${seasonLabel}_date`]
          const opponent = data[`${seasonLabel}_opponent`]
          const score = data[`${seasonLabel}_score`]
          const result = data[`${seasonLabel}_result`]
          
          let resColor = "text-slate-400"
          if (result === 'W') resColor = "text-emerald-400"
          if (result === 'L') resColor = "text-rose-400"
          if (result === 'D') resColor = "text-amber-400"

          return (
            <div key={seasonLabel} className="space-y-0.5 border-b border-white/5 pb-2 last:border-0 last:pb-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.stroke }}></span>
                  <span className="text-white font-bold">{seasonLabel}</span>
                </div>
                <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-indigo-300 font-bold">
                  Pos: {position}
                </span>
              </div>
              
              {opponent && (
                <div className="pl-3.5 text-[10px] text-slate-400 space-y-0.5 mt-1 font-medium">
                  <p className="truncate">Opponent: <strong className="text-slate-200">{opponent}</strong></p>
                  <p>
                    Result: <strong className={resColor}>{score} ({result})</strong>
                  </p>
                  {date && (
                    <p>Date: <span className="text-slate-500">{new Date(date).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'})}</span></p>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }
  return null
}

export const RiseFallTab: React.FC<RiseFallTabProps> = ({
  seasons,
  selectedSeasonId,
  setSelectedSeasonId,
}) => {
  const [mode, setMode] = useState<'teams' | 'seasons'>('teams')
  
  // State for MODE: Compare Teams (Single Season)
  const [chartDataTeams, setChartDataTeams] = useState<any[]>([])
  const [teamsList, setTeamsList] = useState<string[]>([])
  const [selectedTeams, setSelectedTeams] = useState<string[]>([])
  
  // State for MODE: Compare Seasons (Single Team)
  const [teamsMetadata, setTeamsMetadata] = useState<Team[]>([])
  const [selectedTeamId, setSelectedTeamId] = useState<number>(0)
  const [selectedSeasons, setSelectedSeasons] = useState<number[]>([])
  const [chartDataSeasons, setChartDataSeasons] = useState<any[]>([])
  
  const [loading, setLoading] = useState<boolean>(false)

  // 1. Fetch metadata for Compare Teams (Single Season)
  useEffect(() => {
    if (!selectedSeasonId || mode !== 'teams') return

    setLoading(true)
    fetch(`http://localhost:8000/api/standings/history?season_id=${selectedSeasonId}`)
      .then((res) => res.json())
      .then((data) => {
        setChartDataTeams(data)
        if (data.length > 0) {
          const keys = Object.keys(data[0]).filter((k) => k !== 'gameweek')
          setTeamsList(keys.sort())
          
          // Default: top 5 teams
          const finalRound = data[data.length - 1]
          const finalStandings = Object.entries(finalRound)
            .filter(([k]) => k !== 'gameweek')
            .map(([name, pos]) => ({ name, pos: Number(pos) }))
            .sort((a, b) => a.pos - b.pos)
            
          const top5 = finalStandings.slice(0, 5).map((item) => item.name)
          setSelectedTeams(top5)
        }
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setLoading(false)
      })
  }, [selectedSeasonId, mode])

  // 2. Fetch metadata for Compare Seasons (Single Team)
  useEffect(() => {
    // Fetch all teams to populate selector
    fetch('http://localhost:8000/api/teams')
      .then((res) => res.json())
      .then((data) => {
        setTeamsMetadata(data)
        if (data.length > 0 && !selectedTeamId) {
          setSelectedTeamId(data[0].id)
        }
      })
      .catch((err) => console.error(err))
      
    // Set default seasons to compare (latest 3 seasons)
    if (seasons.length > 0 && selectedSeasons.length === 0) {
      const top3Ids = seasons.slice(0, 3).map(s => s.id)
      setSelectedSeasons(top3Ids)
    }
  }, [seasons])

  // 3. Fetch chart data for Compare Seasons (Single Team)
  useEffect(() => {
    if (mode !== 'seasons' || !selectedTeamId || selectedSeasons.length === 0) return

    setLoading(true)
    const seasonsQuery = selectedSeasons.join(',')
    fetch(`http://localhost:8000/api/teams/${selectedTeamId}/seasons-compare?seasons=${seasonsQuery}`)
      .then((res) => res.json())
      .then((data) => {
        setChartDataSeasons(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setLoading(false)
      })
  }, [selectedTeamId, selectedSeasons, mode])

  // Handlers for Compare Teams Mode
  const handleTeamToggle = (team: string) => {
    setSelectedTeams((prev) =>
      prev.includes(team) ? prev.filter((t) => t !== team) : [...prev, team]
    )
  }
  const selectAllTeams = () => setSelectedTeams(teamsList)
  const selectNoTeams = () => setSelectedTeams([])

  // Handlers for Compare Seasons Mode
  const handleSeasonToggle = (seasonId: number) => {
    setSelectedSeasons((prev) =>
      prev.includes(seasonId) ? prev.filter((id) => id !== seasonId) : [...prev, seasonId]
    )
  }
  const selectAllSeasons = () => setSelectedSeasons(seasons.map(s => s.id))
  const selectNoSeasons = () => setSelectedSeasons([])

  return (
    <div className="space-y-6">
      {/* Mode Selector Panel */}
      <div className="glass-card p-4 rounded-2xl flex justify-center border border-white/5">
        <div className="flex bg-slate-950 p-1.5 rounded-xl border border-white/5">
          <button
            onClick={() => setMode('teams')}
            className={`px-5 py-2 rounded-lg text-xs font-bold transition-all ${
              mode === 'teams'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/10'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Compare Teams in a Season
          </button>
          <button
            onClick={() => setMode('seasons')}
            className={`px-5 py-2 rounded-lg text-xs font-bold transition-all ${
              mode === 'seasons'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/10'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Compare Seasons of a Team
          </button>
        </div>
      </div>

      {/* Control panel based on active mode */}
      {mode === 'teams' ? (
        /* Compare Teams Mode Panel */
        <div className="glass-card p-6 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-6 border border-white/5">
          <div className="flex flex-col gap-1 w-full md:w-auto">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Select Season</label>
            <select
              value={selectedSeasonId}
              onChange={(e) => setSelectedSeasonId(Number(e.target.value))}
              className="bg-slate-900 border border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors w-full md:w-60 animate-none"
            >
              {seasons.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <div className="text-sm text-slate-400 text-center md:text-right flex items-center gap-2">
            <Info className="w-4 h-4 text-indigo-400 shrink-0" />
            <span>Overlay different clubs below to trace and compare their standings.</span>
          </div>
        </div>
      ) : (
        /* Compare Seasons Mode Panel */
        <div className="glass-card p-6 rounded-2xl flex flex-col md:flex-row items-center justify-between gap-6 border border-white/5">
          <div className="flex flex-col gap-1 w-full md:w-auto">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">Select Team</label>
            <select
              value={selectedTeamId}
              onChange={(e) => setSelectedTeamId(Number(e.target.value))}
              className="bg-slate-900 border border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors w-full md:w-60"
            >
              {teamsMetadata.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
          <div className="text-sm text-slate-400 text-center md:text-right flex items-center gap-2">
            <Info className="w-4 h-4 text-indigo-400 shrink-0" />
            <span>Overlay multiple seasons for a single club. Hover graph points to see specific matches & dates.</span>
          </div>
        </div>
      )}

      {/* Main content split panel */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left checklist panel */}
        <div className="glass-card p-5 rounded-2xl border border-white/5 h-[500px] flex flex-col lg:col-span-1">
          {mode === 'teams' ? (
            /* Teams Checklist */
            <>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/5">
                <h3 className="font-bold text-white text-sm">Clubs</h3>
                <div className="flex gap-2 text-xs font-bold text-indigo-400">
                  <button onClick={selectAllTeams} className="hover:underline">All</button>
                  <span>|</span>
                  <button onClick={selectNoTeams} className="hover:underline">None</button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                {teamsList.map((team, idx) => {
                  const isChecked = selectedTeams.includes(team)
                  const color = GET_COLOR(team, idx)
                  return (
                    <label
                      key={team}
                      className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors text-xs font-semibold ${
                        isChecked ? 'bg-white/5 text-white' : 'text-slate-400 hover:bg-white/5'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleTeamToggle(team)}
                          className="rounded accent-indigo-500 cursor-pointer"
                        />
                        <span>{team}</span>
                      </div>
                      <span
                        className="w-2.5 h-2.5 rounded-full animate-pulse"
                        style={{ backgroundColor: color }}
                      ></span>
                    </label>
                  )
                })}
              </div>
            </>
          ) : (
            /* Seasons Checklist */
            <>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/5">
                <h3 className="font-bold text-white text-sm">Seasons</h3>
                <div className="flex gap-2 text-xs font-bold text-indigo-400">
                  <button onClick={selectAllSeasons} className="hover:underline">All</button>
                  <span>|</span>
                  <button onClick={selectNoSeasons} className="hover:underline">None</button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                {seasons.map((s, idx) => {
                  const isChecked = selectedSeasons.includes(s.id)
                  const color = SEASON_COLORS[idx % SEASON_COLORS.length]
                  return (
                    <label
                      key={s.id}
                      className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors text-xs font-semibold ${
                        isChecked ? 'bg-white/5 text-white' : 'text-slate-400 hover:bg-white/5'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleSeasonToggle(s.id)}
                          className="rounded accent-indigo-500 cursor-pointer"
                        />
                        <span>{s.label}</span>
                      </div>
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: color }}
                      ></span>
                    </label>
                  )
                })}
              </div>
            </>
          )}
        </div>

        {/* Right chart panel */}
        <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col justify-between h-[500px] lg:col-span-3">
          
          {mode === 'teams' ? (
            /* SINGLE SEASON - TEAMS COMPARE CHART */
            <>
              <h3 className="font-bold text-white mb-4">Rise & Fall (Table Position by Gameweek)</h3>
              {loading ? (
                <div className="flex-1 flex flex-col items-center justify-center gap-4">
                  <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-slate-400 text-sm">Building chart data...</p>
                </div>
              ) : chartDataTeams.length === 0 ? (
                <div className="flex-1 flex items-center justify-center text-slate-500">
                  No historical standings found.
                </div>
              ) : (
                <div className="flex-1 w-full min-h-0">
                  <ResponsiveContainer width="100%" height="95%">
                    <LineChart data={chartDataTeams} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                      <XAxis dataKey="gameweek" stroke="#64748b" fontSize={11} fontWeight="600" tickLine={false} />
                      <YAxis reversed domain={[1, 20]} tickCount={20} stroke="#64748b" fontSize={11} fontWeight="600" tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0f172a',
                          borderColor: 'rgba(255,255,255,0.08)',
                          borderRadius: '12px',
                          color: '#f8fafc',
                          fontSize: '12px',
                          fontWeight: '600',
                        }}
                      />
                      {selectedTeams.map((team) => (
                        <Line
                          key={team}
                          type="monotone"
                          dataKey={team}
                          stroke={GET_COLOR(team, teamsList.indexOf(team))}
                          strokeWidth={2.5}
                          dot={false}
                          activeDot={{ r: 6 }}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          ) : (
            /* SINGLE TEAM - SEASONS COMPARE CHART */
            <>
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-white">
                  Season-by-Season Trajectory: <span className="text-indigo-400">{teamsMetadata.find(t => t.id === selectedTeamId)?.name}</span>
                </h3>
              </div>
              {loading ? (
                <div className="flex-1 flex flex-col items-center justify-center gap-4">
                  <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                  <p className="text-slate-400 text-sm">Loading historical data...</p>
                </div>
              ) : chartDataSeasons.length === 0 ? (
                <div className="flex-1 flex items-center justify-center text-slate-500">
                  Select at least one season on the left checklist.
                </div>
              ) : (
                <div className="flex-1 w-full min-h-0">
                  <ResponsiveContainer width="100%" height="95%">
                    <LineChart data={chartDataSeasons} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                      <XAxis dataKey="gameweek" stroke="#64748b" fontSize={11} fontWeight="600" tickLine={false} />
                      <YAxis reversed domain={[1, 20]} tickCount={20} stroke="#64748b" fontSize={11} fontWeight="600" tickLine={false} />
                      <Tooltip content={<CustomSeasonsTooltip />} />
                      {selectedSeasons.map((seasonId) => {
                        const season = seasons.find(s => s.id === seasonId)
                        const label = season ? season.label : ""
                        const idx = seasons.findIndex(s => s.id === seasonId)
                        
                        return (
                          <Line
                            key={seasonId}
                            type="monotone"
                            dataKey={label}
                            stroke={SEASON_COLORS[idx % SEASON_COLORS.length]}
                            strokeWidth={2.5}
                            dot={false}
                            activeDot={{ r: 6 }}
                          />
                        )
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )}
        </div>

      </div>
    </div>
  )
}
