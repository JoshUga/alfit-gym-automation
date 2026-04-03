import { Users, Phone, Bell, MessageSquare } from 'lucide-react';
import Card from '../components/Card';
import { useThemeStore } from '../stores/themeStore';

export default function DashboardPage() {
  const isDark = useThemeStore((state) => state.isDark);

  return (
    <div>
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-500/80">Operations snapshot</p>
          <h1 className={`mt-2 text-3xl font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Dashboard</h1>
          <p className={`mt-2 text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Your gym metrics and communication activity at a glance.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
        <Card title="Total Members" value={0} icon={<Users size={24} />} />
        <Card
          title="Active Phone Numbers"
          value={0}
          icon={<Phone size={24} />}
          color="text-green-600"
        />
        <Card
          title="Notifications Sent"
          value={0}
          icon={<Bell size={24} />}
          color="text-yellow-600"
        />
        <Card
          title="Messages (7d)"
          value={0}
          icon={<MessageSquare size={24} />}
          color="text-blue-600"
        />
      </div>

      <div className={`mt-8 rounded-2xl border p-6 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
        <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Performance Notes</h2>
        <p className={`mt-2 text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
          Data widgets will automatically expand here as member, notification, and billing activity increases.
        </p>
      </div>
    </div>
  );
}
