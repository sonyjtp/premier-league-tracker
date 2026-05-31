import React, { createContext, useContext, useState, useCallback } from 'react'

export interface UserSettings {
  defaultLeagueId: number
  defaultLeagueName: string
  defaultLeagueFlag: string
  defaultTeamInternalId: number | null
  defaultTeamName: string
  defaultTeamFplId: number | null
  defaultTeamApiId: number | null
}

export const DEFAULT_SETTINGS: UserSettings = {
  defaultLeagueId:      39,
  defaultLeagueName:    'Premier League',
  defaultLeagueFlag:    '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  defaultTeamInternalId: null,
  defaultTeamName:      'Tottenham Hotspur',
  defaultTeamFplId:     null,
  defaultTeamApiId:     null,
}

const STORAGE_KEY = 'pl_tracker_settings'

function loadFromStorage(): UserSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? { ...DEFAULT_SETTINGS, ...JSON.parse(raw) } : DEFAULT_SETTINGS
  } catch {
    return DEFAULT_SETTINGS
  }
}

interface SettingsContextType {
  settings: UserSettings
  saveSettings: (updates: Partial<UserSettings>) => void
}

const SettingsContext = createContext<SettingsContextType>({
  settings: DEFAULT_SETTINGS,
  saveSettings: () => {},
})

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<UserSettings>(loadFromStorage)

  const saveSettings = useCallback((updates: Partial<UserSettings>) => {
    setSettings(prev => {
      const next = { ...prev, ...updates }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      return next
    })
  }, [])

  return (
    <SettingsContext.Provider value={{ settings, saveSettings }}>
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  return useContext(SettingsContext)
}
