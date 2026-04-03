import { useThemeStore } from '../stores/themeStore';

interface Column<T> {
  key: string;
  label: string;
  render?: (item: T) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (item: T) => void;
}

export default function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  onRowClick,
}: DataTableProps<T>) {
  const isDark = useThemeStore((state) => state.isDark);

  return (
    <div className={`overflow-hidden rounded-2xl border ${isDark ? 'border-slate-800 bg-slate-900/50' : 'border-slate-200 bg-white'}`}>
      <div className="overflow-x-auto">
        <table className={`w-full text-left ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
          <thead>
            <tr className={`${isDark ? 'border-b border-slate-800 bg-slate-950/60' : 'border-b border-slate-200 bg-slate-50'}`}>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 text-xs font-semibold uppercase tracking-[0.14em] ${isDark ? 'text-slate-400' : 'text-slate-500'}`}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((item, idx) => (
              <tr
                key={idx}
                onClick={() => onRowClick?.(item)}
                className={`border-b transition-colors ${onRowClick ? 'cursor-pointer' : ''} ${
                  isDark
                    ? `${idx % 2 === 0 ? 'bg-slate-900/40' : 'bg-slate-900/15'} border-slate-800/70 hover:bg-slate-800/70`
                    : `${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/80'} border-slate-200 hover:bg-slate-100`
                }`}
              >
                {columns.map((col) => (
                  <td key={col.key} className={`px-4 py-3 text-sm ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
                    {col.render ? col.render(item) : String(item[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td colSpan={columns.length} className={`py-10 text-center text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  No data available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
