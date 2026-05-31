import React from 'react'
import { Trophy, TrendingUp, BarChart2, Users } from 'lucide-react'

interface NavbarProps {
  activeTab: string
  setActiveTab: (tab: string) => void
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'standings', label: 'Standings', icon: Trophy },
    { id: 'risefall', label: 'Rise & Fall', icon: TrendingUp },
    { id: 'teamform', label: 'Team Form', icon: BarChart2 },
    { id: 'playercompare', label: 'Player Comparer', icon: Users },
  ]

  return (
    <nav className="sticky top-0 z-50 px-6 py-4 glass-panel border-b border-white/5 mb-8">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-tr from-indigo-500 to-rose-500 p-2.5 rounded-xl shadow-lg shadow-indigo-500/10">
            <Trophy className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Premier League Performance Platform
            </h1>
            <p className="text-xs text-slate-500">10-Season Historical & Real-Time Analytics</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex bg-slate-900/60 p-1.5 rounded-xl border border-white/5 gap-1">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-md shadow-indigo-600/20'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
