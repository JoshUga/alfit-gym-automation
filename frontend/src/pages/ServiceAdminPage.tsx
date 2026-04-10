import { useMemo, useState } from 'react';
import { serviceAdminApi } from '../services/api';

const DEFAULT_ADMIN_USERNAME = 'service-admin';
const DEFAULT_ADMIN_PASSWORD = 'service-admin-2026';

export default function ServiceAdminPage() {
  const [username, setUsername] = useState(DEFAULT_ADMIN_USERNAME);
  const [password, setPassword] = useState(DEFAULT_ADMIN_PASSWORD);
  const [authenticated, setAuthenticated] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [overview, setOverview] = useState<Record<string, number> | null>(null);
  const [gyms, setGyms] = useState<Array<{ id: number; name: string; email?: string; phone?: string; is_active: boolean; member_count: number }>>([]);
  const [backups, setBackups] = useState<Array<{ id: number; label?: string; status: string; created_at?: string }>>([]);

  const authHeaders = useMemo(
    () => ({ 'X-Admin-Username': username, 'X-Admin-Password': password }),
    [username, password]
  );

  const login = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await serviceAdminApi.login({ username, password });
      if (!res.data.data.authenticated) {
        setError('Invalid admin credentials');
        setAuthenticated(false);
        return;
      }
      setAuthenticated(true);
      const [overviewRes, gymsRes, backupsRes] = await Promise.all([
        serviceAdminApi.getOverview(authHeaders),
        serviceAdminApi.listGyms(authHeaders),
        serviceAdminApi.listBackups(authHeaders),
      ]);
      setOverview(overviewRes.data.data);
      setGyms(gymsRes.data.data || []);
      setBackups(backupsRes.data.data || []);
    } catch {
      setError('Failed to authenticate or load admin data');
      setAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const createBackup = async () => {
    setLoading(true);
    setError('');
    try {
      await serviceAdminApi.createBackup(authHeaders, { label: `backup-${new Date().toISOString()}` });
      const backupsRes = await serviceAdminApi.listBackups(authHeaders);
      setBackups(backupsRes.data.data || []);
    } catch {
      setError('Backup failed');
    } finally {
      setLoading(false);
    }
  };

  const restoreBackup = async (backupId: number) => {
    setLoading(true);
    setError('');
    try {
      await serviceAdminApi.restoreBackup(authHeaders, backupId, { clear_existing: false });
      const [overviewRes, gymsRes] = await Promise.all([
        serviceAdminApi.getOverview(authHeaders),
        serviceAdminApi.listGyms(authHeaders),
      ]);
      setOverview(overviewRes.data.data);
      setGyms(gymsRes.data.data || []);
    } catch {
      setError('Restore failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-slate-100 md:p-10">
      <div className="mx-auto max-w-7xl">
        <h1 className="mb-2 text-3xl font-bold text-cyan-300">Service Admin Dashboard</h1>
        <p className="mb-6 text-sm text-slate-400">
          Platform-level control center for gyms, members, and full-system backup/restore.
        </p>

        {error && <div className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{error}</div>}

        {!authenticated ? (
          <div className="max-w-lg rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
            <h2 className="mb-4 text-lg font-semibold">Admin Sign In</h2>
            <div className="space-y-3">
              <input
                className="w-full rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-3"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
              />
              <input
                type="password"
                className="w-full rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-3"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
              />
              <button
                disabled={loading}
                onClick={login}
                className="rounded-xl bg-cyan-400 px-5 py-2.5 text-sm font-semibold text-slate-950"
              >
                {loading ? 'Authenticating...' : 'Enter Dashboard'}
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
              {Object.entries(overview || {}).map(([key, value]) => (
                <div key={key} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                  <p className="text-xs uppercase tracking-[0.14em] text-slate-400">{key.replaceAll('_', ' ')}</p>
                  <p className="mt-2 text-2xl font-bold text-cyan-300">{value}</p>
                </div>
              ))}
            </section>

            <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold">Gyms and Members</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-400">
                      <th className="py-2">Gym</th>
                      <th className="py-2">Email</th>
                      <th className="py-2">Phone</th>
                      <th className="py-2">Members</th>
                      <th className="py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {gyms.map((gym) => (
                      <tr key={gym.id} className="border-t border-slate-800">
                        <td className="py-2">{gym.name}</td>
                        <td className="py-2">{gym.email || '-'}</td>
                        <td className="py-2">{gym.phone || '-'}</td>
                        <td className="py-2">{gym.member_count}</td>
                        <td className="py-2">{gym.is_active ? 'Active' : 'Inactive'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold">System Backup & Restore</h2>
                <button
                  disabled={loading}
                  onClick={createBackup}
                  className="rounded-xl bg-emerald-400 px-4 py-2 text-sm font-semibold text-slate-950"
                >
                  {loading ? 'Working...' : 'Create Backup'}
                </button>
              </div>
              <div className="space-y-2">
                {backups.map((backup) => (
                  <div key={backup.id} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-sm">
                    <div>
                      <p className="font-semibold text-slate-200">#{backup.id} {backup.label || 'Unnamed backup'}</p>
                      <p className="text-xs text-slate-400">{backup.created_at || ''} • {backup.status}</p>
                    </div>
                    <button
                      disabled={loading}
                      onClick={() => restoreBackup(backup.id)}
                      className="rounded-lg border border-cyan-400/40 px-3 py-1.5 text-xs text-cyan-300"
                    >
                      Restore
                    </button>
                  </div>
                ))}
                {!backups.length && <p className="text-sm text-slate-400">No backups yet.</p>}
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}

