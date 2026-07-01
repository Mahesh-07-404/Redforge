import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useSettings } from '../contexts/SettingsContext';
import { useSession } from '../contexts/SessionContext';
import { RedForgeAPI } from '../services/api';
import {
  LayoutDashboard,
  MessageSquare,
  GitFork,
  Settings as SettingsIcon,
  Shield,
  Layers,
  Database,
  Grid,
  FileText,
  Activity,
  LogOut,
  Moon,
  Sun,
  Server,
  ChevronsUpDown,
} from 'lucide-react';

export const DashboardLayout: React.FC = () => {
  const { settings, updateSettings } = useSettings();
  const { sessions, activeSession, activeSessionId, setActiveSessionId } = useSession();
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected'>('disconnected');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const navigate = useNavigate();

  // Poll health endpoint
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await RedForgeAPI.getHealth(settings.apiUrl);
        setApiStatus('connected');
      } catch {
        setApiStatus('disconnected');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [settings.apiUrl]);

  const toggleTheme = () => {
    updateSettings({ theme: settings.theme === 'light' ? 'dark' : 'light' });
  };

  const navItems = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/chat', label: 'AI Chat', icon: MessageSquare },
    { to: '/workflows', label: 'Workflows', icon: GitFork },
    { to: '/sessions', label: 'Sessions', icon: Layers },
    { to: '/evidence', label: 'Evidence & Run', icon: Shield },
    { to: '/reports', label: 'Reports', icon: FileText },
    { to: '/memory', label: 'Memory Base', icon: Database },
    { to: '/plugins', label: 'Plugins', icon: Grid },
    { to: '/settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card/30 backdrop-blur-md flex flex-col">
        {/* Logo Section */}
        <div className="h-16 flex items-center px-6 gap-3 border-b border-border">
          <div className="h-8 w-8 rounded bg-primary flex items-center justify-center text-primary-foreground font-black tracking-wider shadow-[0_0_15px_rgba(170,59,255,0.4)]">
            RF
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-foreground m-0 p-0 leading-none">RedForge</h1>
            <span className="text-[10px] text-muted-foreground uppercase tracking-widest">OS Core v2.0</span>
          </div>
        </div>

        {/* Sidebar Nav */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-[0_0_12px_rgba(170,59,255,0.25)]'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User / API Info footer */}
        <div className="p-4 border-t border-border bg-card/50 flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${apiStatus === 'connected' ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-rose-500 shadow-[0_0_8px_#f43f5e]'}`} />
              {apiStatus === 'connected' ? 'API Gateway Live' : 'API Gateway Offline'}
            </span>
            <button
              onClick={toggleTheme}
              className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
              title="Toggle theme"
            >
              {settings.theme === 'light' ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-border bg-card/20 backdrop-blur-md px-8 flex items-center justify-between z-10 shrink-0">
          <div className="flex items-center gap-6">
            {/* Session Switcher Dropdown */}
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-3 px-4 py-1.5 rounded-md border border-border bg-muted/50 hover:bg-muted text-sm font-medium transition-all"
              >
                <div className="text-left">
                  <div className="text-[10px] text-muted-foreground uppercase tracking-widest leading-none">Active Session</div>
                  <div className="text-xs text-foreground font-semibold truncate max-w-[150px]">
                    {activeSession ? activeSession.name : 'No Active Session'}
                  </div>
                </div>
                <ChevronsUpDown className="h-4 w-4 text-muted-foreground" />
              </button>

              {dropdownOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setDropdownOpen(false)} />
                  <div className="absolute left-0 mt-2 w-64 rounded-md border border-border bg-card shadow-lg py-1 z-20 max-h-80 overflow-y-auto">
                    <div className="px-3 py-1.5 text-xs text-muted-foreground border-b border-border">Select Session</div>
                    {sessions.length === 0 ? (
                      <div className="px-3 py-4 text-xs text-muted-foreground text-center">No sessions available</div>
                    ) : (
                      sessions.map((sess) => (
                        <button
                          key={sess.id}
                          onClick={() => {
                            setActiveSessionId(sess.id);
                            setDropdownOpen(false);
                          }}
                          className={`w-full text-left px-3 py-2 text-xs flex flex-col hover:bg-muted ${
                            activeSessionId === sess.id ? 'bg-primary/10 border-l-2 border-primary' : ''
                          }`}
                        >
                          <span className="font-semibold text-foreground truncate">{sess.name}</span>
                          <span className="text-[10px] text-muted-foreground truncate uppercase">
                            {sess.mode} • {sess.target || 'No target'}
                          </span>
                        </button>
                      ))
                    )}
                    <div className="border-t border-border mt-1 pt-1">
                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          navigate('/sessions');
                        }}
                        className="w-full text-center px-3 py-1.5 text-xs font-semibold text-primary hover:bg-muted"
                      >
                        Manage Sessions
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Session Meta Tags */}
            {activeSession && (
              <div className="flex gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-accent text-accent-foreground border border-primary/20 uppercase tracking-wider">
                  Mode: {activeSession.mode}
                </span>
                {activeSession.target && (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-muted text-muted-foreground border border-border truncate max-w-[200px]">
                    Target: {activeSession.target}
                  </span>
                )}
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-primary/20 text-primary border border-primary/30 uppercase tracking-wider">
                  Autonomy: {activeSession.autonomy}
                </span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-4">
            <span className="text-xs text-muted-foreground select-none">
              API Host: <code className="text-[10px] bg-muted px-1.5 py-0.5 rounded text-foreground">{settings.apiUrl}</code>
            </span>
          </div>
        </header>

        {/* Content Outlet */}
        <main className="flex-1 overflow-y-auto p-8 bg-background/50">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
