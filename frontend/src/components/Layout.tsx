import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useThemeStore } from '../stores/themeStore';
import SearchDrawer from './SearchDrawer';
import {
  Home,
  Users,
  CalendarDays,
  Bell,
  MessageSquare,
  Settings,
  LogOut,
  Moon,
  Sun,
  Menu,
  X,
  Search,
  Sparkles,
  UserCog,
  CreditCard,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

const navItems = [
  { path: '/app', label: 'Dashboard', icon: Home, roles: ['gym_owner', 'gym_staff'] },
  { path: '/app/members', label: 'Members', icon: Users, roles: ['gym_owner', 'gym_staff'] },
  { path: '/app/attendance', label: 'Attendance', icon: CalendarDays, roles: ['gym_owner', 'gym_staff'] },
  { path: '/app/staff', label: 'Staff', icon: UserCog, roles: ['gym_owner'] },
  { path: '/app/notifications', label: 'Notifications', icon: Bell, roles: ['gym_owner'] },
  { path: '/app/messages', label: 'Messages', icon: MessageSquare, roles: ['gym_owner'] },
  { path: '/app/payments', label: 'Payments', icon: CreditCard, roles: ['gym_owner', 'gym_staff'] },
  { path: '/app/settings', label: 'Settings', icon: Settings, roles: ['gym_owner'] },
];

export default function Layout() {
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);
  const { isDark, toggle } = useThemeStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  useEffect(() => {
    const handleKeydown = (event: KeyboardEvent) => {
      const isCommandSearch = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k';

      if (isCommandSearch) {
        event.preventDefault();
        setIsSearchOpen(true);
      }
    };

    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  }, []);

  const visibleNavItems = useMemo(
    () => navItems.filter((item) => !user?.role || item.roles.includes(user.role)),
    [user?.role]
  );

  const pageTitle = useMemo(() => {
    const active = visibleNavItems.find((item) => item.path === location.pathname);
    if (active) return active.label;
    if (location.pathname.startsWith('/app/members')) return 'Members';
    if (location.pathname.startsWith('/app/attendance')) return 'Attendance';
    if (location.pathname.startsWith('/app/staff')) return 'Staff';
    if (location.pathname.startsWith('/app/notifications')) return 'Notifications';
    if (location.pathname.startsWith('/app/messages')) return 'Messages';
    if (location.pathname.startsWith('/app/payments')) return 'Payments';
    if (location.pathname.startsWith('/app/settings')) return 'Settings';
    return 'Dashboard';
  }, [location.pathname, visibleNavItems]);

  return (
    <div className={`min-h-screen lg:flex ${isDark ? 'bg-slate-950 text-slate-100' : 'bg-slate-100 text-slate-900'}`}>
      <aside
        className={`fixed left-0 top-16 z-30 h-[calc(100vh-4rem)] w-72 transform backdrop-blur transition-transform duration-300 ease-in-out lg:static lg:top-auto lg:h-auto lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } ${
          isDark
            ? 'border-r border-slate-800 bg-slate-950/95'
            : 'border-r border-slate-200 bg-white/95'
        }`}
      >
        <div className={`flex h-16 items-center justify-between border-b px-6 ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
            <Link to="/" className="text-xl font-semibold tracking-[0.2em] text-cyan-500">
              <span>ALFIT</span>
            </Link>
          <Sparkles size={16} className={isDark ? 'text-cyan-300/80' : 'text-cyan-500/80'} />
        </div>

        <div className="px-5 pb-3 pt-5">
          <div className={`rounded-2xl border p-4 text-xs ${isDark ? 'border-slate-800 bg-slate-900/70 text-slate-300' : 'border-slate-200 bg-slate-50 text-slate-600'}`}>
            <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-500/80">
              <span>Operations cockpit</span>
              <span className="art-subtext text-cyan-300/90">Operations cockpit</span>
            </p>
            <p className={`mt-2 text-sm ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
              Stay on top of members, automation, and retention in one place.
            </p>
          </div>
        </div>

        <nav className="space-y-1.5 p-4">
          {visibleNavItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition duration-200 ${
                location.pathname === path
                  ? 'bg-gradient-to-r from-cyan-400 to-emerald-300 text-slate-950 shadow-[0_8px_24px_rgba(34,211,238,0.25)]'
                  : isDark
                    ? 'text-slate-300 hover:bg-slate-900 hover:text-white'
                    : 'text-slate-700 hover:bg-slate-100 hover:text-slate-950'
              }`}
            >
              <Icon size={20} />
              <span>{label}</span>
            </Link>
          ))}

          <button
            onClick={logout}
            className={`mt-5 flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-sm transition ${
              isDark
                ? 'border-slate-700 text-slate-300 hover:border-red-500/40 hover:bg-red-500/10 hover:text-red-200'
                : 'border-slate-200 text-slate-700 hover:border-red-300 hover:bg-red-50 hover:text-red-700'
            }`}
          >
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </nav>
      </aside>

      {sidebarOpen && (
        <div
          className={`fixed inset-0 z-20 backdrop-blur-sm lg:hidden ${isDark ? 'bg-slate-950/70' : 'bg-slate-900/20'}`}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="relative flex min-w-0 flex-1 flex-col">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(34,211,238,0.12),transparent_25%),radial-gradient(circle_at_85%_85%,rgba(16,185,129,0.1),transparent_25%)]" />

        <header className={`sticky top-0 z-10 border-b backdrop-blur ${isDark ? 'border-slate-800/80 bg-slate-950/80' : 'border-slate-200/80 bg-white/85'}`}>
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <button
                className={`rounded-lg p-2 transition lg:hidden ${isDark ? 'text-slate-300 hover:bg-slate-800 hover:text-white' : 'text-slate-700 hover:bg-slate-200 hover:text-slate-950'}`}
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
              </button>
              <div>
                <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-500/80">
                  <span>Workspace</span>
                </p>
                <h1 className={`text-sm font-semibold sm:text-base ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  <span>{pageTitle}</span>
                </h1>
              </div>
            </div>

            <div className="flex items-center gap-2 sm:gap-3">
              <button
                type="button"
                onClick={() => setIsSearchOpen(true)}
                className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-xs transition ${
                  isDark
                    ? 'border-slate-700 bg-slate-900/70 text-slate-300 hover:border-slate-600 hover:text-white'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:text-slate-950'
                }`}
              >
                <Search size={14} />
                <span className="hidden md:inline">Search</span>
                <span className={`hidden rounded border px-1.5 py-0.5 text-[10px] md:inline ${isDark ? 'border-slate-700 text-slate-500' : 'border-slate-200 text-slate-400'}`}>
                  Ctrl/Cmd+K
                </span>
              </button>
              <button
                onClick={toggle}
                className={`rounded-lg border p-2 transition ${
                  isDark
                    ? 'border-slate-700 bg-slate-900/70 text-slate-300 hover:border-slate-600 hover:text-white'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:text-slate-950'
                }`}
                title="Toggle theme"
              >
                {isDark ? <Sun size={18} /> : <Moon size={18} />}
              </button>
            </div>
          </div>
        </header>

        <main className="relative z-[1] flex-1 p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>

      <SearchDrawer isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
    </div>
  );
}
