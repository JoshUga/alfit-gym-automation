import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, Search } from 'lucide-react';
import Drawer from './Drawer';
import { useThemeStore } from '../stores/themeStore';

type SearchItem = {
  label: string;
  description: string;
  path: string;
  keywords: string[];
};

const searchItems: SearchItem[] = [
  {
    label: 'Dashboard',
    description: 'Gym overview, metrics, and activity summary',
    path: '/app',
    keywords: ['home', 'overview', 'stats', 'dashboard'],
  },
  {
    label: 'Members',
    description: 'Find, add, edit, and manage members',
    path: '/app/members',
    keywords: ['clients', 'people', 'schedule', 'members'],
  },
  {
    label: 'Notifications',
    description: 'Automation schedules and campaign templates',
    path: '/app/notifications',
    keywords: ['alerts', 'schedule', 'campaigns', 'notifications'],
  },
  {
    label: 'Messages',
    description: 'Conversation and delivery history',
    path: '/app/messages',
    keywords: ['chat', 'history', 'whatsapp', 'messages'],
  },
  {
    label: 'Billing',
    description: 'Plan details and payment history',
    path: '/app/billing',
    keywords: ['subscription', 'invoice', 'payments', 'billing'],
  },
  {
    label: 'Settings',
    description: 'Gym profile, phone lines, and workspace controls',
    path: '/app/settings',
    keywords: ['profile', 'configuration', 'preferences', 'settings'],
  },
];

interface SearchDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SearchDrawer({ isOpen, onClose }: SearchDrawerProps) {
  const isDark = useThemeStore((state) => state.isDark);
  const navigate = useNavigate();
  const location = useLocation();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [query, setQuery] = useState('');

  useEffect(() => {
    if (!isOpen) {
      setQuery('');
      return;
    }

    window.setTimeout(() => inputRef.current?.focus(), 50);
  }, [isOpen]);

  const filteredItems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      return searchItems;
    }

    return searchItems.filter((item) => {
      const haystack = [item.label, item.description, ...item.keywords].join(' ').toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [query]);

  const handleOpen = (path: string) => {
    navigate(path);
    onClose();
  };

  return (
    <Drawer isOpen={isOpen} onClose={onClose} title="Search workspace">
      <div className="space-y-4">
        <div
          className={`flex items-center gap-3 rounded-2xl border px-4 py-3 ${
            isDark ? 'border-slate-700 bg-slate-900/80' : 'border-slate-200 bg-white'
          }`}
        >
          <Search size={18} className={isDark ? 'text-slate-400' : 'text-slate-500'} />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search pages, actions, settings..."
            className={`w-full bg-transparent text-sm outline-none ${
              isDark ? 'text-white placeholder:text-slate-500' : 'text-slate-900 placeholder:text-slate-400'
            }`}
          />
        </div>

        <div className="flex items-center justify-between text-xs uppercase tracking-[0.18em]">
          <span className={isDark ? 'text-slate-500' : 'text-slate-500'}>Quick navigation</span>
          <span className={isDark ? 'text-slate-600' : 'text-slate-400'}>Ctrl/Cmd + K</span>
        </div>

        <div className="space-y-2">
          {filteredItems.map((item) => {
            const isActive = location.pathname === item.path;

            return (
              <button
                key={item.path}
                type="button"
                onClick={() => handleOpen(item.path)}
                className={`flex w-full items-center justify-between rounded-2xl border px-4 py-4 text-left transition ${
                  isActive
                    ? isDark
                      ? 'border-cyan-400/40 bg-cyan-400/10'
                      : 'border-cyan-300 bg-cyan-50'
                    : isDark
                      ? 'border-slate-800 bg-slate-900/70 hover:border-slate-700 hover:bg-slate-900'
                      : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                <div>
                  <p className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>{item.label}</p>
                  <p className={`mt-1 text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{item.description}</p>
                </div>
                <ArrowRight size={16} className={isDark ? 'text-slate-500' : 'text-slate-400'} />
              </button>
            );
          })}

          {filteredItems.length === 0 && (
            <div
              className={`rounded-2xl border px-4 py-6 text-sm ${
                isDark ? 'border-slate-800 bg-slate-900/60 text-slate-400' : 'border-slate-200 bg-white text-slate-500'
              }`}
            >
              No matching pages found.
            </div>
          )}
        </div>
      </div>
    </Drawer>
  );
}
