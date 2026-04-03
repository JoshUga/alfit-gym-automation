import { Bell, CalendarPlus } from 'lucide-react';
import { useThemeStore } from '../stores/themeStore';

export default function NotificationsPage() {
  const isDark = useThemeStore((state) => state.isDark);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-500/80">Automation</p>
          <h1 className={`mt-2 text-3xl font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Notifications</h1>
        </div>
        <button className="inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300">
          <CalendarPlus size={18} />
          Schedule Notification
        </button>
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className={`rounded-2xl border p-6 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
          <h2 className={`mb-4 flex items-center gap-2 text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            <Bell size={20} />
            Upcoming Notifications
          </h2>
          <p className={`py-10 text-center ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            No scheduled notifications
          </p>
        </div>
        <div className={`rounded-2xl border p-6 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
          <h2 className={`mb-4 text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Templates</h2>
          <p className={`py-10 text-center ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            No templates created yet
          </p>
        </div>
      </div>
    </div>
  );
}
