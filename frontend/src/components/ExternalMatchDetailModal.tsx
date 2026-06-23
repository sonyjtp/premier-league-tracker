import React, { useState, useEffect } from 'react'
import { X } from 'lucide-react'

interface Fixture {
  fixture_id: number
  date: string | null
  status_short: string
  home_team: string
  away_team: string
  home_team_api_id: number
  away_team_api_id: number
  home_goals: number | null
  away_goals: number | null
  home_logo?: string | null
  away_logo?: string | null
}

interface Stat {
  type: string
  value: number | string | null
  team: 'home' | 'away'
}

interface Props {
  fixture: Fixture
  homeTeamApiId: number
  awayTeamApiId: number
  onClose: () => void
  onSelectFixture?: (fixture: Fixture, homeId: number, awayId: number) => void
}

export const ExternalMatchDetailModal: React.FC<Props> = ({
  fixture,
  homeTeamApiId,
  awayTeamApiId,
  onClose,
  onSelectFixture,
}) => {
  const [stats, setStats] = useState<{ [key: string]: { home: any; away: any } }>({})
  const [h2h, setH2h] = useState<Fixture[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`/api/external/fixtures/${fixture.fixture_id}/statistics`)
        .then(r => r.json())
        .catch(() => []),
      fetch(
        `/api/external/fixtures/headtohead?team1_id=${homeTeamApiId}&team2_id=${awayTeamApiId}`
      )
        .then(r => r.json())
        .catch(() => []),
    ]).then(([statsData, h2hData]) => {
      const statsMap: { [key: string]: { home: any; away: any } } = {}
      ;(statsData || []).forEach((stat: Stat) => {
        if (!statsMap[stat.type]) statsMap[stat.type] = { home: null, away: null }
        statsMap[stat.type][stat.team] = stat.value
      })
      setStats(statsMap)
      setH2h(Array.isArray(h2hData) ? h2hData : [])
      setLoading(false)
    })
  }, [fixture.fixture_id, homeTeamApiId, awayTeamApiId])

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return ''
    return new Date(dateStr).toLocaleDateString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  }

  const h2hRecord = h2h.reduce(
    (acc, match) => {
      const homeWon =
        match.home_goals !== null &&
        match.away_goals !== null &&
        match.home_goals > match.away_goals
      const awayWon =
        match.home_goals !== null &&
        match.away_goals !== null &&
        match.away_goals > match.home_goals
      const draw = match.home_goals === match.away_goals && match.home_goals !== null
      return {
        homeW: acc.homeW + (homeWon ? 1 : 0),
        awayW: acc.awayW + (awayWon ? 1 : 0),
        draws: acc.draws + (draw ? 1 : 0),
      }
    },
    { homeW: 0, awayW: 0, draws: 0 }
  )

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-slate-950 rounded-3xl border border-white/10 max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-slate-950 border-b border-white/5 p-6 flex items-center justify-between">
          <h2 className="text-2xl font-black text-white">
            {fixture.home_team} vs {fixture.away_team}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Match Info */}
          <div className="glass-card p-6 rounded-2xl border border-white/5">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-sm text-slate-500 mb-2">{fixture.home_team}</p>
                <p className="text-4xl font-black text-white">{fixture.home_goals ?? '-'}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                  {formatDate(fixture.date)}
                </p>
                <p className="text-sm text-slate-400">{fixture.status_short}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-2">{fixture.away_team}</p>
                <p className="text-4xl font-black text-white">{fixture.away_goals ?? '-'}</p>
              </div>
            </div>
          </div>

          {/* Match Statistics */}
          {!loading && Object.keys(stats).length > 0 && (
            <div className="glass-card p-6 rounded-2xl border border-white/5">
              <h3 className="text-lg font-bold text-white mb-6">Match Statistics</h3>
              <StatisticsSection stats={stats} />
            </div>
          )}

          {/* H2H History */}
          {h2h.length > 0 && (
            <div className="glass-card p-6 rounded-2xl border border-white/5">
              <h3 className="text-lg font-bold text-white mb-4">Head-to-Head History</h3>

              {/* H2H Record */}
              <div className="grid grid-cols-3 gap-3 mb-6 p-4 bg-slate-900/40 rounded-xl">
                <div className="text-center">
                  <p className="text-2xl font-black text-emerald-400">{h2hRecord.homeW}</p>
                  <p className="text-xs text-slate-500 mt-1">{fixture.home_team} Wins</p>
                </div>
                <div className="text-center border-x border-white/5">
                  <p className="text-2xl font-black text-amber-400">{h2hRecord.draws}</p>
                  <p className="text-xs text-slate-500 mt-1">Draws</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-black text-rose-400">{h2hRecord.awayW}</p>
                  <p className="text-xs text-slate-500 mt-1">{fixture.away_team} Wins</p>
                </div>
              </div>

              {/* Recent H2H Matches */}
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {h2h
                  .sort((a, b) => {
                    const dateA = a.date ? new Date(a.date).getTime() : 0
                    const dateB = b.date ? new Date(b.date).getTime() : 0
                    return dateB - dateA // Descending order (newest first)
                  })
                  .slice(0, 10)
                  .map((match, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      if (onSelectFixture) {
                        onSelectFixture(match, match.home_team_api_id, match.away_team_api_id)
                      }
                    }}
                    className="w-full flex items-center justify-between text-xs p-3 rounded-lg bg-slate-900/30 border border-white/5 hover:bg-slate-900/50 hover:border-white/10 transition-all text-left"
                  >
                    <span className="text-slate-500 w-20">{formatDate(match.date)}</span>
                    <span className="text-slate-300 flex-1 text-center">
                      {match.home_team} <span className="text-slate-600">vs</span> {match.away_team}
                    </span>
                    <span className="font-semibold text-slate-200 w-16 text-right">
                      {match.home_goals}–{match.away_goals}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="text-center py-8 text-slate-400">Loading match details...</div>
          )}
        </div>
      </div>
    </div>
  )
}

const STAT_SECTIONS = [
  {
    title: 'Attacking',
    stats: ['Shots on Goal', 'Shots off Goal', 'Total Shots', 'Shots insidebox', 'Shots outsidebox', 'expected_goals'],
  },
  {
    title: 'Defensive',
    stats: ['Blocked Shots', 'Fouls', 'Goalkeeper Saves', 'goals_prevented'],
  },
  {
    title: 'Possession',
    stats: ['Ball Possession', 'Total passes', 'Passes accurate', 'Passes %'],
  },
  {
    title: 'Set Pieces',
    stats: ['Corner Kicks', 'Offsides'],
  },
  {
    title: 'Discipline',
    stats: ['Yellow Cards', 'Red Cards'],
  },
]

function StatisticsSection({ stats }: { stats: { [key: string]: { home: any; away: any } } }) {
  return (
    <div className="space-y-6">
      {STAT_SECTIONS.map(section => {
        const sectionStats = section.stats.filter(stat => stats[stat])
        if (sectionStats.length === 0) return null
        return (
          <div key={section.title}>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">{section.title}</h4>
            <div className="space-y-2">
              {sectionStats.map(statType => (
                <div key={statType} className="flex items-center gap-3 text-xs">
                  <div className="flex-1 text-right text-slate-300 font-medium">
                    {stats[statType].home ?? '-'}
                  </div>
                  <div className="w-32 text-center text-slate-500 font-semibold text-[10px] uppercase">
                    {statType}
                  </div>
                  <div className="flex-1 text-left text-slate-300 font-medium">
                    {stats[statType].away ?? '-'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
