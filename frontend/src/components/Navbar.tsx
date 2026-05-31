import React from 'react'
import { Globe, TrendingUp, BarChart2, Radio, Settings, Search } from 'lucide-react'

interface NavbarProps {
  activeTab: string
  setActiveTab: (tab: string) => void
  onSearchOpen: () => void
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, onSearchOpen }) => {
  const tabs = [
    { id: 'leagues',  label: 'Leagues',    icon: Globe      },
    { id: 'risefall', label: 'Rise & Fall', icon: TrendingUp },
    { id: 'teamform', label: 'Team Form',  icon: BarChart2  },
    { id: 'live',     label: 'Live',       icon: Radio      },
    { id: 'settings', label: 'Settings',   icon: Settings   },
  ]

  return (
    <nav className="sticky top-0 z-50 px-6 py-4 glass-panel border-b border-white/5 mb-8">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="bg-gradient-to-tr from-indigo-500 to-rose-500 p-2.5 rounded-xl shadow-lg shadow-indigo-500/10">
            <Globe className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Premier League Performance Platform
            </h1>
            <p className="text-xs text-slate-500">Top-5 European Leagues · 10-Season Analytics</p>
          </div>
        </div>

        {/* Right side: search + tabs */}
        <div className="flex items-center gap-2">
          {/* Player search button */}
          <button
            onClick={onSearchOpen}
            title="Search players (⌘K)"
            className="flex items-center gap-2 px-3 py-2 rounded-xl border border-white/5 bg-slate-900/60 text-slate-400 hover:text-white hover:border-indigo-500/40 transition-all text-sm font-medium"
          >
            <Search className="w-4 h-4" />
            <span className="hidden lg:inline text-xs text-slate-500">Search player…</span>
            <kbd className="hidden lg:inline text-[10px] text-slate-600 bg-slate-800 px-1.5 py-0.5 rounded border border-white/5">⌘K</kbd>
          </button>

          {/* Tab buttons */}
          <div className="flex bg-slate-900/60 p-1.5 rounded-xl border border-white/5 gap-1">
            {tabs.map(tab => {
              const Icon     = tab.icon
              const isActive = activeTab === tab.id
              const isLive   = tab.id === 'live'
              const isSets   = tab.id === 'settings'
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? isLive ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 text-white shadow-md shadow-emerald-600/20'
                        : isSets ? 'bg-slate-700 text-white'
                        : 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-md shadow-indigo-600/20'
                      : 'text-slate-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{tab.label}</span>
                  {isLive && !isActive && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />}
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}
