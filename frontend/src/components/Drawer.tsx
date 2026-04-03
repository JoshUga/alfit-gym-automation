import { X } from 'lucide-react';
import { useThemeStore } from '../stores/themeStore';

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export default function Drawer({ isOpen, onClose, title, children }: DrawerProps) {
  const isDark = useThemeStore((state) => state.isDark);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50">
      <button
        type="button"
        className={`absolute inset-0 backdrop-blur-sm ${isDark ? 'bg-slate-950/70' : 'bg-slate-900/20'}`}
        onClick={onClose}
        aria-label="Close drawer"
      />

      <aside
        className={`absolute right-0 top-0 h-full w-full max-w-xl border-l p-6 shadow-2xl ${
          isDark ? 'border-slate-800 bg-slate-950/95' : 'border-slate-200 bg-slate-50/95'
        }`}
      >
        <div className={`mb-6 flex items-center justify-between border-b pb-4 ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
          <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className={`rounded-lg p-1.5 transition ${
              isDark ? 'text-slate-400 hover:bg-slate-800 hover:text-slate-200' : 'text-slate-500 hover:bg-slate-200 hover:text-slate-800'
            }`}
            aria-label="Close drawer"
          >
            <X size={18} />
          </button>
        </div>
        <div className="h-[calc(100%-4rem)] overflow-y-auto pr-1">{children}</div>
      </aside>
    </div>
  );
}