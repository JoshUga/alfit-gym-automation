import { useEffect, useState } from 'react';
import { Settings, Phone, ShieldCheck } from 'lucide-react';
import { gymService } from '../services/api';
import { useThemeStore } from '../stores/themeStore';

type GymForm = {
  name: string;
  email: string;
  phone: string;
  address: string;
};

const emptyGym: GymForm = { name: '', email: '', phone: '', address: '' };

export default function SettingsPage() {
  const isDark = useThemeStore((state) => state.isDark);
  const [gymId, setGymId] = useState<number | null>(null);
  const [gym, setGym] = useState<GymForm>(emptyGym);
  const [phoneNumbers, setPhoneNumbers] = useState<Array<{ id: number; phone_number: string; label?: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    void loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    setError('');
    try {
      const gymRes = await gymService.getMine();
      const g = gymRes.data.data;
      setGymId(g.id);
      setGym({
        name: g.name || '',
        email: g.email || '',
        phone: g.phone || '',
        address: g.address || '',
      });
      localStorage.setItem('active_gym_id', String(g.id));

      const phonesRes = await gymService.getPhoneNumbers(g.id);
      setPhoneNumbers(phonesRes.data.data || []);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to load settings at the moment.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveGym = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gymId) return;
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await gymService.update(gymId, {
        name: gym.name,
        email: gym.email,
        phone: gym.phone,
        address: gym.address,
      });
      setSuccess('Gym settings saved successfully.');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Failed to save gym settings.');
    } finally {
      setSaving(false);
    }
  };

  const fieldClassName = `w-full rounded-xl border px-4 py-3 outline-none transition focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-500/30 ${
    isDark
      ? 'border-slate-700 bg-slate-950/70 text-slate-100'
      : 'border-slate-200 bg-white text-slate-900'
  }`;

  return (
    <div>
      <h1 className={`mb-6 flex items-center gap-2 text-3xl font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
        <Settings size={24} />
        Settings
      </h1>
      {error && <div className="mb-4 rounded-xl border border-red-500/35 bg-red-500/10 p-3 text-sm text-red-600">{error}</div>}
      {success && <div className="mb-4 rounded-xl border border-emerald-500/35 bg-emerald-500/10 p-3 text-sm text-emerald-600">{success}</div>}

      <div className="space-y-6">
        <div className={`rounded-2xl border p-6 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
          <h2 className={`mb-4 text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Gym Profile</h2>
          {loading ? (
            <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Loading gym profile...</p>
          ) : (
            <form className="grid grid-cols-1 gap-6 md:grid-cols-2" onSubmit={handleSaveGym}>
              <div>
                <label className={`mb-2 block text-xs uppercase tracking-[0.16em] ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Gym Name</label>
                <input
                  type="text"
                  className={fieldClassName}
                  value={gym.name}
                  onChange={(e) => setGym((prev) => ({ ...prev, name: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label className={`mb-2 block text-xs uppercase tracking-[0.16em] ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Email</label>
                <input
                  type="email"
                  className={fieldClassName}
                  value={gym.email}
                  onChange={(e) => setGym((prev) => ({ ...prev, email: e.target.value }))}
                />
              </div>
              <div>
                <label className={`mb-2 block text-xs uppercase tracking-[0.16em] ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Phone</label>
                <input
                  type="tel"
                  className={fieldClassName}
                  value={gym.phone}
                  onChange={(e) => setGym((prev) => ({ ...prev, phone: e.target.value }))}
                />
              </div>
              <div>
                <label className={`mb-2 block text-xs uppercase tracking-[0.16em] ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Address</label>
                <input
                  type="text"
                  className={fieldClassName}
                  value={gym.address}
                  onChange={(e) => setGym((prev) => ({ ...prev, address: e.target.value }))}
                />
              </div>
              <div className="md:col-span-2">
                <button type="submit" className="rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-60" disabled={saving}>
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          )}
        </div>

        <div className={`rounded-2xl border p-6 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
          <h2 className={`mb-4 flex items-center gap-2 text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            <Phone size={20} />
            Phone Numbers
          </h2>
          {!phoneNumbers.length ? (
            <p className={isDark ? 'text-slate-400' : 'text-slate-500'}>No phone numbers linked yet.</p>
          ) : (
            <div className="space-y-2">
              {phoneNumbers.map((p) => (
                <div
                  key={p.id}
                  className={`flex justify-between rounded-xl border px-3 py-2 text-sm ${
                    isDark ? 'border-slate-700 bg-slate-950/60 text-slate-200' : 'border-slate-200 bg-slate-50 text-slate-700'
                  }`}
                >
                  <span>{p.phone_number}</span>
                  <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>{p.label || 'Primary'}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-cyan-400/25 bg-cyan-500/5 p-6">
          <h2 className={`mb-3 flex items-center gap-2 text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            <ShieldCheck size={20} />
            Workspace Safeguards
          </h2>
          <div className={`rounded-xl border border-cyan-400/25 p-4 text-sm ${isDark ? 'bg-slate-900/70 text-slate-200' : 'bg-white/80 text-slate-700'}`}>
            <p className="font-medium text-cyan-500">Operational Security</p>
            <p className={`mt-2 ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
              Your automation and messaging engine is centrally managed for reliability. Gym-level settings here remain focused on profile, communication lines, and day-to-day operations.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
