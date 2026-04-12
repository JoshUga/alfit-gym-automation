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

type SmtpForm = {
  host: string;
  port: string;
  username: string;
  password: string;
  from_email: string;
  from_name: string;
  secure: boolean;
  starttls: boolean;
  is_active: boolean;
};

const emptyGym: GymForm = { name: '', email: '', phone: '', address: '' };
const emptySmtp: SmtpForm = {
  host: '',
  port: '587',
  username: '',
  password: '',
  from_email: '',
  from_name: '',
  secure: false,
  starttls: true,
  is_active: true,
};

export default function SettingsPage() {
  const isDark = useThemeStore((state) => state.isDark);
  const [gymId, setGymId] = useState<number | null>(null);
  const [gym, setGym] = useState<GymForm>(emptyGym);
  const [phoneNumbers, setPhoneNumbers] = useState<Array<{ id: number; phone_number: string; label?: string }>>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [smtp, setSmtp] = useState<SmtpForm>(emptySmtp);
  const [savingSmtp, setSavingSmtp] = useState(false);
  const [testingSmtp, setTestingSmtp] = useState(false);
  const [domainName, setDomainName] = useState('');
  const [domainYears, setDomainYears] = useState('1');
  const [buyingDomain, setBuyingDomain] = useState(false);
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

      try {
        const smtpRes = await gymService.getSmtpSettings(g.id);
        const smtpData = smtpRes.data.data;
        if (smtpData) {
          setSmtp({
            host: smtpData.host || '',
            port: String(smtpData.port || 587),
            username: smtpData.username || '',
            password: '',
            from_email: smtpData.from_email || '',
            from_name: smtpData.from_name || '',
            secure: !!smtpData.secure,
            starttls: !!smtpData.starttls,
            is_active: !!smtpData.is_active,
          });
        }
      } catch {
        setSmtp(emptySmtp);
      }
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

  const handleSaveSmtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gymId) return;
    setSavingSmtp(true);
    setError('');
    setSuccess('');
    try {
      await gymService.updateSmtpSettings(gymId, {
        host: smtp.host,
        port: Number(smtp.port) || 587,
        username: smtp.username,
        password: smtp.password,
        from_email: smtp.from_email,
        from_name: smtp.from_name || undefined,
        secure: smtp.secure,
        starttls: smtp.starttls,
        is_active: smtp.is_active,
      });
      setSuccess('SMTP settings saved.');
      setSmtp((prev) => ({ ...prev, password: '' }));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Failed to save SMTP settings.');
    } finally {
      setSavingSmtp(false);
    }
  };

  const handleTestSmtp = async () => {
    if (!gymId) return;
    setTestingSmtp(true);
    setError('');
    setSuccess('');
    try {
      const res = await gymService.testSmtpSettings(gymId);
      if (res.data.data?.ok) {
        setSuccess('SMTP test successful.');
      } else {
        setError(`SMTP test failed: ${res.data.data?.reason || 'unknown'}`);
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'SMTP test failed.');
    } finally {
      setTestingSmtp(false);
    }
  };

  const handleBuyDomain = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gymId) return;
    setBuyingDomain(true);
    setError('');
    setSuccess('');
    try {
      const res = await gymService.createDomainCheckout(gymId, {
        domain_name: domainName,
        years: Number(domainYears) || 1,
      });
      const checkout = res.data.data?.checkout_url;
      if (checkout) {
        window.open(checkout, '_blank', 'noopener,noreferrer');
        setSuccess('Checkout opened in a new tab.');
      } else {
        setError('Could not create checkout URL.');
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Failed to create domain checkout.');
    } finally {
      setBuyingDomain(false);
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

        <div className={`rounded-2xl border p-6 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
          <h2 className={`mb-4 text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Gym SMTP Settings</h2>
          <form className="grid grid-cols-1 gap-4 md:grid-cols-2" onSubmit={handleSaveSmtp}>
            <input className={fieldClassName} placeholder="SMTP Host" value={smtp.host} onChange={(e) => setSmtp((p) => ({ ...p, host: e.target.value }))} required />
            <input className={fieldClassName} placeholder="SMTP Port" value={smtp.port} onChange={(e) => setSmtp((p) => ({ ...p, port: e.target.value }))} required />
            <input className={fieldClassName} placeholder="SMTP Username" value={smtp.username} onChange={(e) => setSmtp((p) => ({ ...p, username: e.target.value }))} required />
            <input type="password" className={fieldClassName} placeholder="SMTP Password (enter to set/update)" value={smtp.password} onChange={(e) => setSmtp((p) => ({ ...p, password: e.target.value }))} required />
            <input type="email" className={fieldClassName} placeholder="From Email" value={smtp.from_email} onChange={(e) => setSmtp((p) => ({ ...p, from_email: e.target.value }))} required />
            <input className={fieldClassName} placeholder="From Name" value={smtp.from_name} onChange={(e) => setSmtp((p) => ({ ...p, from_name: e.target.value }))} />
            <label className={`flex items-center gap-2 text-sm ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
              <input type="checkbox" checked={smtp.secure} onChange={(e) => setSmtp((p) => ({ ...p, secure: e.target.checked }))} />
              Use SSL (SMTPS)
            </label>
            <label className={`flex items-center gap-2 text-sm ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
              <input type="checkbox" checked={smtp.starttls} onChange={(e) => setSmtp((p) => ({ ...p, starttls: e.target.checked }))} />
              Use STARTTLS
            </label>
            <label className={`flex items-center gap-2 text-sm ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
              <input type="checkbox" checked={smtp.is_active} onChange={(e) => setSmtp((p) => ({ ...p, is_active: e.target.checked }))} />
              Active for this gym
            </label>
            <div className="md:col-span-2 flex gap-3">
              <button type="submit" className="rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-60" disabled={savingSmtp}>
                {savingSmtp ? 'Saving...' : 'Save SMTP'}
              </button>
              <button type="button" onClick={handleTestSmtp} className="rounded-xl border border-cyan-400/50 px-4 py-2.5 text-sm font-semibold text-cyan-300 transition hover:bg-cyan-500/10 disabled:opacity-60" disabled={testingSmtp || !gymId}>
                {testingSmtp ? 'Testing...' : 'Test SMTP'}
              </button>
            </div>
          </form>
        </div>

        <div className={`rounded-2xl border p-6 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
          <h2 className={`mb-4 text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Domain Purchase</h2>
          <form className="grid grid-cols-1 gap-4 md:grid-cols-3" onSubmit={handleBuyDomain}>
            <input className={fieldClassName} placeholder="example.com" value={domainName} onChange={(e) => setDomainName(e.target.value)} required />
            <input className={fieldClassName} placeholder="Years" type="number" min={1} value={domainYears} onChange={(e) => setDomainYears(e.target.value)} required />
            <button type="submit" className="rounded-xl bg-emerald-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:opacity-60" disabled={buyingDomain}>
              {buyingDomain ? 'Preparing...' : 'Buy via PayGate'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
