import React, { useState, useEffect, useCallback } from 'react'
import { Activity, Clock, Circle, Radio } from 'lucide-react'
import { MatchDetailModal } from './MatchDetailModal'

interface FixtureTeam {
  name: string
  logo: string | null
  api_id: number | null
}

interface Fixture {
  fixture_id: number
  status_short: string
  status_long: string
  elapsed: number | null
  kickoff: string | null
  venue: string | null
  round: string | null
  home_team: FixtureTeam
  away_team: FixtureTeam
  home_score: number | null
  away_score: number | null
  home_ht_score: number | null
  away_ht_score: number | null
}

const STATUS: Record<string, { label: string; color: string; live: boolean }> = {
  NS:   { label: 'Upcoming',    color: 'text-slate-400',  live: false },
  '1H': { label: 'First Half',  color: 'text-emerald-400', live: true },
  HT:   { label: 'Half Time',   color: 'text-amber-400',  live: true },
  '2H': { label: 'Second Half', color: 'text-emerald-400', live: true },
  ET:   { label: 'Extra Time',  color: 'text-orange-400', live: true },
  P:    { label: 'Penalties',   color: 'text-orange-400', live: true },
  FT:   { label: 'Full Time',   color: 'text-slate-500',  live: false },
  AET:  { label: 'After ET',    color: 'text-slate-500',  live: false },
  PEN:  { label: 'After Pens',  color: 'text-slate-500',  live: false },
  SUSP: { label: 'Suspended',   color: 'text-rose-400',   live: false },
  INT:  { label: 'Interrupted', color: 'text-rose-400',   live: false },
  ABD:  { label: 'Abandoned',   color: 'text-rose-400',   live: false },
}

const FINISHED = new Set(['FT', 'AET', 'PEN'])

interface Props { onTeamClick?: (teamId: number) => void }

// onTeamClick reserved for when api_football_id → internal team ID mapping is populated
export const LiveTab: React.FC<Props> = ({ onTeamClick: _onTeamClick }) => {
  const [liveFixtures, setLiveFixtures]     = useState<Fixture[]>([])
  const [upcomingFixtures, setUpcomingFixtures] = useState<Fixture[]>([])
  const [loading, setLoading]               = useState(true)
  const [selectedId, setSelectedId]         = useState<number | null>(null)

  const fetchData = useCallback(async () => {
    const [liveRes, upcomingRes] = await Promise.allSettled([
      fetch('/api/live').then(r => r.json()),
      fetch('/api/fixtures').then(r => r.json()),
    ])
    if (liveRes.status === 'fulfilled' && liveRes.value?.fixtures) {
      setLiveFixtures(liveRes.value.fixtures)
    }
    if (upcomingRes.status === 'fulfilled' && upcomingRes.value?.fixtures) {
      setUpcomingFixtures(upcomingRes.value.fixtures.filter((f: Fixture) => f.status_short === 'NS'))
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 60_000)
    return () => clearInterval(interval)
  }, [fetchData])

  const renderCard = (f: Fixture) => {
    const st       = STATUS[f.status_short] ?? { label: f.status_short, color: 'text-slate-400', live: false }
    const hasScore = f.home_score !== null && f.away_score !== null
    const finished = FINISHED.has(f.status_short)

    return (
      <div
        key={f.fixture_id}
        onClick={() => setSelectedId(f.fixture_id)}
        className={`glass-card p-5 rounded-2xl border cursor-pointer transition-all hover:border-indigo-500/40 relative overflow-hidden ${
          st.live ? 'border-emerald-500/30' : 'border-white/5'
        }`}
      >
        {st.live && (
          <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-emerald-500 to-emerald-400 animate-pulse" />
        )}

        <div className="flex justify-between items-center mb-4">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
            {f.round ?? 'Premier League'}
          </span>
          <div className="flex items-center gap-1.5">
            {st.live && <Circle className="w-2 h-2 text-emerald-400 fill-emerald-400 animate-pulse" />}
            <span className={`text-xs font-bold ${st.color}`}>
              {st.live && f.elapsed != null ? `${f.elapsed}'` : st.label}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 flex flex-col items-start gap-2">
            {f.home_team.logo
              ? <img src={f.home_team.logo} alt="" className="w-10 h-10 object-contain" />
              : <div className="w-10 h-10 rounded-full bg-slate-800" />}
            <span className="text-sm font-bold text-white">{f.home_team.name}</span>
          </div>

          <div className="flex flex-col items-center gap-1 min-w-[80px]">
            {hasScore ? (
              <>
                <div className="flex items-center gap-2">
                  <span className={`text-3xl font-black ${finished ? 'text-slate-300' : 'text-white'}`}>
                    {f.home_score}
                  </span>
                  <span className="text-slate-600 text-xl font-bold">-</span>
                  <span className={`text-3xl font-black ${finished ? 'text-slate-300' : 'text-white'}`}>
                    {f.away_score}
                  </span>
                </div>
                {f.home_ht_score != null && (
                  <span className="text-[10px] text-slate-500 font-semibold">
                    HT {f.home_ht_score} - {f.away_ht_score}
                  </span>
                )}
              </>
            ) : (
              <div className="flex flex-col items-center">
                <Clock className="w-5 h-5 text-slate-500 mb-1" />
                <span className="text-sm font-bold text-slate-300">
                  {f.kickoff
                    ? new Date(f.kickoff).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    : 'TBC'}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5">
                  {f.kickoff ? new Date(f.kickoff).toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' }) : ''}
                </span>
              </div>
            )}
          </div>

          <div className="flex-1 flex flex-col items-end gap-2">
            {f.away_team.logo
              ? <img src={f.away_team.logo} alt="" className="w-10 h-10 object-contain" />
              : <div className="w-10 h-10 rounded-full bg-slate-800" />}
            <span className="text-sm font-bold text-white text-right">{f.away_team.name}</span>
          </div>
        </div>

        {f.venue && <p className="text-[10px] text-slate-600 text-center mt-3">{f.venue}</p>}
      </div>
    )
  }

  // Group upcoming by date label
  const byDate = upcomingFixtures.reduce<Record<string, Fixture[]>>((acc, f) => {
    const label = f.kickoff
      ? new Date(f.kickoff).toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })
      : 'TBC'
    acc[label] = [...(acc[label] ?? []), f]
    return acc
  }, {})

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-40 gap-4">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 text-sm">Loading fixtures...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Radio className="w-5 h-5 text-emerald-400" />
          <h2 className="text-2xl font-black text-white">Live & Upcoming</h2>
        </div>
        <p className="text-sm text-slate-500">Live Premier League scores and the next 7 days of fixtures.</p>
      </div>

      {/* Live now */}
      <section>
        <div className="flex items-center gap-3 mb-5">
          <Activity className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-black text-white">Live Now</h2>
          <Circle className="w-2 h-2 text-emerald-400 fill-emerald-400 animate-pulse" />
          <span className="text-xs text-slate-500">refreshes every 60 s</span>
        </div>

        {liveFixtures.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {liveFixtures.map(renderCard)}
          </div>
        ) : (
          <div className="glass-card p-14 rounded-2xl text-center border border-white/5">
            <Activity className="w-10 h-10 text-slate-700 mx-auto mb-3" />
            <p className="text-slate-400 font-semibold">No live matches right now</p>
            <p className="text-slate-600 text-sm mt-1">Check back on match day</p>
          </div>
        )}
      </section>

      {/* Upcoming */}
      <section>
        <div className="flex items-center gap-3 mb-5">
          <Clock className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-black text-white">Upcoming — Next 7 Days</h2>
        </div>

        {Object.keys(byDate).length > 0 ? (
          <div className="space-y-6">
            {Object.entries(byDate).map(([dateLabel, fixtures]) => (
              <div key={dateLabel}>
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider px-1 mb-3">
                  {dateLabel}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {fixtures.map(renderCard)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="glass-card p-14 rounded-2xl text-center border border-white/5">
            <Clock className="w-10 h-10 text-slate-700 mx-auto mb-3" />
            <p className="text-slate-400 font-semibold">No upcoming fixtures found</p>
            <p className="text-slate-600 text-sm mt-1">Make sure your API key is configured in backend/.env</p>
          </div>
        )}
      </section>

      {selectedId !== null && (
        <MatchDetailModal fixtureId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  )
}
