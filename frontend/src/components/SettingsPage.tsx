import React, { useState, useEffect } from 'react'
import { Settings, Check, Globe, Users, BarChart2, TrendingUp } from 'lucide-react'
// Users is used for the Default Team section header
import { useSettings } from '../contexts/SettingsContext'

interface League {
  id: number
  name: string
  country: string
  flag: string
  logo: string
}

interface Team {
  id: number
  name: string
  short_name: string
  fpl_id: number | null
  api_football_id: number | null
}

export const SettingsPage: React.FC = () => {
  const { settings, saveSettings } = useSettings()
  const [leagues, setLeagues]       = useState<League[]>([])
  const [teams,   setTeams]         = useState<Team[]>([])
  const [saved,   setSaved]         = useState(false)

  useEffect(() => {
    fetch('/api/leagues').then(r => r.json()).then(setLeagues).catch(() => {})
    fetch('/api/teams').then(r => r.json()).then(setTeams).catch(() => {})
  }, [])

  function selectLeague(league: League) {
    saveSettings({
      defaultLeagueId:   league.id,
      defaultLeagueName: league.name,
      defaultLeagueFlag: league.flag,
    })
    flash()
  }

  function selectTeam(team: Team) {
    saveSettings({
      defaultTeamInternalId: team.id,
      defaultTeamName:       team.name,
      defaultTeamFplId:      team.fpl_id,
      defaultTeamApiId:      team.api_football_id,
    })
    flash()
  }

  function flash() {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Page header */}
      <div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-indigo-400" />
            <h2 className="text-2xl font-black text-white">Settings</h2>
          </div>
          {saved && (
            <div className="flex items-center gap-1.5 text-emerald-400 text-sm font-semibold animate-fade-in">
              <Check className="w-4 h-4" />
              Saved
            </div>
          )}
        </div>
        <p className="text-sm text-slate-500 mt-1">
          These defaults pre-select league, team, and players across the app when you first open each page.
        </p>
      </div>

      {/* Default league */}
      <section className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
        <div>
          <h3 className="font-black text-white flex items-center gap-2">
            <Globe className="w-4 h-4 text-indigo-400" />
            Default League
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            The league selected when you open the Leagues tab.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {leagues.map(league => {
            const active = settings.defaultLeagueId === league.id
            return (
              <button
                key={league.id}
                onClick={() => selectLeague(league)}
                className={`flex items-center gap-3 p-4 rounded-xl border text-left transition-all ${
                  active
                    ? 'border-indigo-500/50 bg-indigo-500/10'
                    : 'border-white/5 hover:border-white/10 hover:bg-white/[0.02]'
                }`}
              >
                {league.logo && (
                  <img src={league.logo} alt={league.name} className="w-8 h-8 object-contain shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <p className={`font-bold text-sm ${active ? 'text-indigo-300' : 'text-white'}`}>
                    {league.name}
                  </p>
                  <p className="text-[11px] text-slate-500">{league.flag} {league.country}</p>
                </div>
                {active && <Check className="w-4 h-4 text-indigo-400 shrink-0" />}
              </button>
            )
          })}
        </div>
      </section>

      {/* Default team */}
      <section className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
        <div>
          <h3 className="font-black text-white flex items-center gap-2">
            <Users className="w-4 h-4 text-indigo-400" />
            Default Team
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Pre-selected in Team Form, Rise & Fall, and Player Comparison. Only Premier League teams
            are listed here as they have full historical data.
          </p>
        </div>

        <div className="relative">
          <select
            value={settings.defaultTeamInternalId ?? ''}
            onChange={e => {
              const team = teams.find(t => t.id === Number(e.target.value))
              if (team) selectTeam(team)
            }}
            className="w-full bg-slate-900 border border-white/5 rounded-xl px-4 py-3 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500 transition-colors appearance-none"
          >
            <option value="" disabled>Select a team…</option>
            {teams.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
          <div className="pointer-events-none absolute right-4 top-3.5 text-slate-400">▾</div>
        </div>

        {settings.defaultTeamName && (
          <div className="flex items-center gap-2 text-sm text-slate-400 px-1">
            <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            Current default: <span className="font-bold text-white">{settings.defaultTeamName}</span>
          </div>
        )}
      </section>

      {/* Where defaults apply */}
      <section className="glass-card p-6 rounded-2xl border border-white/5 space-y-3">
        <h3 className="font-black text-white text-sm">Where these defaults apply</h3>
        <div className="space-y-2.5 text-sm text-slate-400">
          {[
            { icon: Globe,      label: 'Leagues',     desc: 'Opens on your default league' },
            { icon: BarChart2,  label: 'Team Form',   desc: 'Team A = your default team' },
            { icon: TrendingUp, label: 'Rise & Fall', desc: '"Compare Seasons" opens on your default team' },
          ].map(({ icon: Icon, label, desc }) => (
            <div key={label} className="flex items-start gap-3">
              <Icon className="w-4 h-4 text-indigo-400 mt-0.5 shrink-0" />
              <div>
                <span className="font-semibold text-slate-300">{label}</span>
                <span className="text-slate-500"> — {desc}</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
