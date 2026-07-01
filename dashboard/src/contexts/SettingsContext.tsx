import React, { createContext, useContext, useState, useEffect } from 'react';

interface Settings {
  apiUrl: string;
  theme: 'light' | 'dark';
  apiKey: string;
  authToken: string;
}

interface SettingsContextType {
  settings: Settings;
  updateSettings: (newSettings: Partial<Settings>) => void;
  isAuthenticated: boolean;
  logout: () => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<Settings>(() => {
    const saved = localStorage.getItem('redforge_settings');
    const parsed = saved ? JSON.parse(saved) : {};
    return {
      apiUrl: parsed.apiUrl || 'http://127.0.0.1:8000',
      theme: parsed.theme || 'dark',
      apiKey: parsed.apiKey || '',
      authToken: parsed.authToken || '',
    };
  });

  useEffect(() => {
    localStorage.setItem('redforge_settings', JSON.stringify(settings));
    
    // Apply theme class
    const root = window.document.documentElement;
    if (settings.theme === 'dark') {
      root.classList.remove('light');
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
      root.classList.add('light');
    }
  }, [settings]);

  const updateSettings = (newSettings: Partial<Settings>) => {
    setSettings((prev) => ({ ...prev, ...newSettings }));
  };

  const logout = () => {
    setSettings((prev) => ({ ...prev, authToken: '', apiKey: '' }));
  };

  const isAuthenticated = !!(settings.apiKey || settings.authToken);

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, isAuthenticated, logout }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};
