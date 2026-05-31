import { useState, useEffect, useCallback } from 'react'
import { Navbar } from './components/Navbar'
import { RiseFallTab } from './components/RiseFallTab'
import { TeamFormTab } from './components/TeamFormTab'
import { LiveTab } from './components/LiveTab'
import { LeaguesTab } from './components/LeaguesTab'
import { SettingsPage } from './components/SettingsPage'
import { TeamPage } from './components/TeamPage'
import { ExternalTeamPage } from './components/ExternalTeamPage'
import { PlayerPage } from './components/PlayerPage'
import { PlayerSearchModal } from './components/PlayerSearchModal'
import { useSettings } from './contexts/SettingsContext'
import type { ExternalTeamParams } from './components/LeaguesTab'

interface Season { id: number; label: string }
interface Team   { id: number; name: string; fpl_id: number | null; api_football_id: number | null }

type View =
  | { type: 'tab' }
  | { type: 'team';          teamId: number }
  | { type: 'external-team'; params: ExternalTeamParams }
  | { type: 'player';        playerId: number }

function App() {
  const { settings, saveSettings }              = useSettings()
  const [activeTab,        setActiveTab]        = useState('leagues')
  const [view,             setView]             = useState<View>({ type: 'tab' })
  const [viewHistory,      setViewHistory]      = useState<View[]>([])
  const [seasons,          setSeasons]          = useState<Season[]>([])
  const [selectedSeasonId, setSelectedSeasonId] = useState(0)
  const [loading,          setLoading]          = useState(true)
  const [searchOpen,       setSearchOpen]       = useState(false)

  useEffect(() => {
    fetch('http://localhost:8000/api/seasons')
      .then(r => r.json())
      .then(data => {
        setSeasons(data)
        if (data.length > 0) setSelectedSeasonId(data[0].id)
        setLoading(false)
      })
      .catch(() => setTimeout(() => window.location.reload(), 3000))
  }, [])

  // Auto-resolve default team internal ID
  useEffect(() => {
    if (settings.defaultTeamInternalId) return
    fetch('http://localhost:8000/api/teams')
      .then(r => r.json())
      .then((teams: Team[]) => {
        const match = teams.find(t => t.name === settings.defaultTeamName)
        if (match) saveSettings({ defaultTeamInternalId: match.id, defaultTeamFplId: match.fpl_id, defaultTeamApiId: match.api_football_id })
      })
      .catch(() => {})
  }, [])

  // ⌘K / Ctrl+K shortcut to open player search
  const openSearch = useCallback(() => setSearchOpen(true), [])
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); openSearch() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [openSearch])

  const navigateToTeam         = (teamId: number)             => {
    setViewHistory([...viewHistory, view])
    setView({ type: 'team', teamId })
  }
  const navigateToExternalTeam = (params: ExternalTeamParams) => {
    setViewHistory([...viewHistory, view])
    setView({ type: 'external-team', params })
  }
  const navigateToPlayer       = (playerId: number)           => {
    setViewHistory([...viewHistory, view])
    setView({ type: 'player', playerId })
  }
  const navigateBack           = () => {
    if (viewHistory.length > 0) {
      const newHistory = [...viewHistory]
      const previousView = newHistory.pop()!
      setViewHistory(newHistory)
      setView(previousView)
    } else {
      setView({ type: 'tab' })
    }
  }

  const handleTabChange = (tab: string) => {
    if (view.type !== 'tab') {
      setViewHistory([...viewHistory, view])
    }
    setActiveTab(tab)
    setView({ type: 'tab' })
  }

  return (
    <div className="min-h-screen bg-[#060a13] text-slate-100 pb-20 selection:bg-indigo-500 selection:text-white">
      <Navbar activeTab={activeTab} setActiveTab={handleTabChange} onSearchOpen={openSearch} />

      <main className="max-w-7xl mx-auto px-6">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-40 gap-4">
            <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <h2 className="text-lg font-bold text-white">Starting Backend Services…</h2>
            <p className="text-slate-500 text-sm">Make sure the PostgreSQL container and FastAPI app are running.</p>
          </div>
        ) : view.type === 'team' ? (
          <TeamPage teamId={view.teamId} seasons={seasons} onBack={navigateBack} />
        ) : view.type === 'external-team' ? (
          <ExternalTeamPage {...view.params} onBack={navigateBack} onViewFullHistory={navigateToTeam} onPlayerClick={navigateToPlayer} />
        ) : view.type === 'player' ? (
          <PlayerPage playerId={view.playerId} onBack={navigateBack} />
        ) : (
          <div>
            {activeTab === 'leagues'  && <LeaguesTab onTeamClick={navigateToExternalTeam} />}
            {activeTab === 'risefall' && (
              <RiseFallTab seasons={seasons} selectedSeasonId={selectedSeasonId} setSelectedSeasonId={setSelectedSeasonId} />
            )}
            {activeTab === 'teamform' && (
              <TeamFormTab seasons={seasons} selectedSeasonId={selectedSeasonId} setSelectedSeasonId={setSelectedSeasonId} onTeamClick={navigateToTeam} />
            )}
            {activeTab === 'live'     && <LiveTab onTeamClick={navigateToTeam} />}
            {activeTab === 'settings' && <SettingsPage />}
          </div>
        )}
      </main>

      {/* Global player search modal */}
      {searchOpen && (
        <PlayerSearchModal
          onSelectPlayer={p => navigateToPlayer(p.id)}
          onSelectTeam={t => navigateToTeam(t.id)}
          onClose={() => setSearchOpen(false)}
        />
      )}
    </div>
  )
}

export default App
