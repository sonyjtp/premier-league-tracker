import { useState, useEffect } from 'react'
import { Navbar } from './components/Navbar'
import { StandingsTab } from './components/StandingsTab'
import { RiseFallTab } from './components/RiseFallTab'
import { TeamFormTab } from './components/TeamFormTab'
import { PlayerCompareTab } from './components/PlayerCompareTab'

interface Season {
  id: number
  label: string
}

function App() {
  const [activeTab, setActiveTab] = useState<string>('standings')
  const [seasons, setSeasons] = useState<Season[]>([])
  const [selectedSeasonId, setSelectedSeasonId] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(true)

  // Fetch seasons on startup
  useEffect(() => {
    fetch('http://localhost:8000/api/seasons')
      .then((res) => res.json())
      .then((data) => {
        setSeasons(data)
        if (data.length > 0) {
          // Default to latest season (which is first due to descending sort)
          setSelectedSeasonId(data[0].id)
        }
        setLoading(false)
      })
      .catch((err) => {
        console.error("Failed to load seasons. Backend might be starting...", err)
        // Retry in 2 seconds
        setTimeout(() => {
          window.location.reload()
        }, 3000)
      })
  }, [])

  return (
    <div className="min-h-screen bg-[#060a13] text-slate-100 pb-20 selection:bg-indigo-500 selection:text-white">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="max-w-7xl mx-auto px-6">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-40 gap-4">
            <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <h2 className="text-lg font-bold text-white">Starting Backend Services...</h2>
            <p className="text-slate-500 text-sm">Please make sure the PostgreSQL container and FastAPI app are running.</p>
          </div>
        ) : (
          <div className="transition-all duration-300">
            {activeTab === 'standings' && (
              <StandingsTab
                seasons={seasons}
                selectedSeasonId={selectedSeasonId}
                setSelectedSeasonId={setSelectedSeasonId}
              />
            )}
            {activeTab === 'risefall' && (
              <RiseFallTab
                seasons={seasons}
                selectedSeasonId={selectedSeasonId}
                setSelectedSeasonId={setSelectedSeasonId}
              />
            )}
            {activeTab === 'teamform' && (
              <TeamFormTab
                seasons={seasons}
                selectedSeasonId={selectedSeasonId}
                setSelectedSeasonId={setSelectedSeasonId}
              />
            )}
            {activeTab === 'playercompare' && <PlayerCompareTab />}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
