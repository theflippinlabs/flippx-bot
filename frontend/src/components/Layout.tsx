import { Outlet, NavLink } from 'react-router-dom'
import { LayoutDashboard, Calendar, List, BarChart2, Twitter, Zap, Settings, BookOpen } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getBotStatus } from '../lib/api'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Home' },
  { to: '/scheduler', icon: Calendar, label: 'Schedule' },
  { to: '/library', icon: BookOpen, label: 'Library' },
  { to: '/queue', icon: List, label: 'Queue' },
  { to: '/analytics', icon: BarChart2, label: 'Stats' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Layout() {
  const { data: status } = useQuery({
    queryKey: ['bot-status'],
    queryFn: getBotStatus,
    refetchInterval: 30_000,
  })

  return (
    <div className="flex flex-col md:flex-row h-screen overflow-hidden">
      {/* Desktop Sidebar - hidden on mobile */}
      <aside className="hidden md:flex w-64 bg-slate-900 border-r border-slate-800 flex-col shrink-0">
        {/* Logo */}
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-sky-500 rounded-xl flex items-center justify-center">
              <Twitter className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-semibold text-slate-100">Twitter Bot</p>
              <p className="text-xs text-slate-500">Control Panel</p>
            </div>
          </div>
        </div>

        {/* Bot status */}
        <div className="px-4 py-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${status?.bot_enabled ? 'bg-emerald-400' : 'bg-red-400'}`} />
            <span className="text-xs text-slate-400">
              Bot {status?.bot_enabled ? 'Active' : 'Stopped'}
            </span>
            {status?.bot_enabled && (
              <Zap className="w-3 h-3 text-yellow-400 ml-auto" />
            )}
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-sky-500/10 text-sky-400'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800">
          <p className="text-xs text-slate-600">Twitter API v2 · Tweepy</p>
        </div>
      </aside>

      {/* Main content - add bottom padding on mobile for nav bar */}
      <main className="flex-1 overflow-y-auto bg-slate-950 pb-20 md:pb-0">
        <Outlet />
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-slate-900 border-t border-slate-800 z-50 safe-area-bottom">
        <div className="flex items-stretch justify-around">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-0.5 py-2 px-1 min-h-[56px] min-w-[48px] flex-1 transition-colors ${
                  isActive
                    ? 'text-sky-400'
                    : 'text-slate-500'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] font-medium leading-tight">{label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
