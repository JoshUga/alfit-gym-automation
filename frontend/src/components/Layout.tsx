import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useThemeStore } from '../stores/themeStore';
import {
  Home,
  Users,
  Bell,
  MessageSquare,
  CreditCard,
  Settings,
  LogOut,
  Moon,
  Sun,
  Menu,
  X,
} from 'lucide-react';
import { useState } from 'react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: Home },
  { path: '/members', label: 'Members', icon: Users },
  { path: '/notifications', label: 'Notifications', icon: Bell },
  { path: '/messages', label: 'Messages', icon: MessageSquare },
  { path: '/billing', label: 'Billing', icon: CreditCard },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Layout() {
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);
  const { isDark, toggle } = useThemeStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen flex bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-white dark:bg-gray-800 border-r
          dark:border-gray-700 transform transition-transform duration-300 ease-in-out
          lg:translate-x-0 lg:static ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="h-16 flex items-center px-6 border-b dark:border-gray-700">
          <h1 className="text-xl font-bold text-primary-600">Alfit</h1>
        </div>
        <nav className="p-4 space-y-1">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 py-2 px-4 rounded-md transition-colors
                duration-200 ${
                  location.pathname === path
                    ? 'bg-primary-50 text-primary-600 dark:bg-gray-700'
                    : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
            >
              <Icon size={20} />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white dark:bg-gray-800 shadow-sm flex items-center justify-between px-6 sticky top-0 z-10">
          <button
            className="lg:hidden p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
          <div className="flex items-center gap-4">
            <button
              onClick={toggle}
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {isDark ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <button
              onClick={logout}
              className="flex items-center gap-2 text-gray-600 dark:text-gray-300
                hover:text-red-600 transition-colors"
            >
              <LogOut size={20} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </header>
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
