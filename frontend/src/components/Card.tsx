import { useThemeStore } from '../stores/themeStore';

interface CardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
}

export default function Card({ title, value, icon, color = 'text-primary-600' }: CardProps) {
  const isDark = useThemeStore((state) => state.isDark);

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border p-5 ${
        isDark
          ? 'border-slate-800 bg-slate-900/70 shadow-[0_12px_30px_rgba(2,6,23,0.35)]'
          : 'border-slate-200 bg-white shadow-[0_12px_30px_rgba(15,23,42,0.08)]'
      }`}
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-cyan-400/10 blur-2xl" />
      <div className="flex items-center gap-4">
        <div className={`rounded-xl border p-3 ${isDark ? 'border-slate-700 bg-slate-950/70' : 'border-slate-200 bg-slate-50'} ${color}`}>
          {icon}
        </div>
        <div>
          <p className={`text-xs uppercase tracking-[0.16em] ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{title}</p>
          <p className={`mt-1 text-3xl font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>{value}</p>
        </div>
      </div>
    </div>
  );
}
