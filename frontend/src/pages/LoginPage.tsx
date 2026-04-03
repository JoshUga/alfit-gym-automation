import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, ArrowRight, Sparkles } from 'lucide-react';
import { authService } from '../services/api';
import { useAuthStore } from '../stores/authStore';

export default function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const setTokens = useAuthStore((state) => state.setTokens);
  const logout = useAuthStore((state) => state.logout);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await authService.login({ email, password });
      const { access_token, refresh_token } = res.data.data;
      setTokens(access_token, refresh_token);
      const meRes = await authService.getMe();
      login(access_token, refresh_token, meRes.data.data);
      navigate('/app');
    } catch (err: unknown) {
      logout();
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 md:flex">
      <section className="relative hidden w-[48%] overflow-hidden md:flex">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(34,211,238,0.25),transparent_40%),radial-gradient(circle_at_80%_75%,rgba(16,185,129,0.25),transparent_45%),linear-gradient(160deg,#020617_10%,#0f172a_55%,#022c22_100%)]" />
        <div className="pointer-events-none absolute -left-28 top-12 h-80 w-80 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="pointer-events-none absolute -right-20 bottom-10 h-96 w-96 rounded-full bg-emerald-400/20 blur-3xl" />

        <div className="relative z-10 flex h-full w-full flex-col justify-between p-12 xl:p-16">
          <div>
            <Link to="/" className="text-xl font-semibold tracking-[0.22em] text-cyan-300">
              ALFIT
            </Link>
          </div>
          <div className="max-w-xl">
            <p className="mb-4 text-xs uppercase tracking-[0.28em] text-cyan-300/90">Access your command center</p>
            <h1 className="text-5xl font-semibold leading-tight text-white">
              Manage your gym with precision, not chaos.
            </h1>
            <p className="mt-6 text-base leading-relaxed text-slate-300">
              Track members, automate messaging, and keep your operation moving with one polished workflow.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm text-slate-200">
            <div className="rounded-2xl border border-slate-700/70 bg-slate-900/50 px-4 py-3">
              <p className="text-slate-400">Member operations</p>
              <p className="mt-1 text-lg font-semibold">Centralized</p>
            </div>
            <div className="rounded-2xl border border-slate-700/70 bg-slate-900/50 px-4 py-3">
              <p className="text-slate-400">Response speed</p>
              <p className="mt-1 text-lg font-semibold">Near real-time</p>
            </div>
          </div>
        </div>
      </section>

      <section className="relative flex min-h-screen w-full items-center justify-center px-6 py-10 sm:px-10 md:w-[52%] md:px-10 lg:px-14 xl:px-20">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_70%_20%,rgba(34,211,238,0.08),transparent_30%),radial-gradient(circle_at_20%_80%,rgba(16,185,129,0.08),transparent_35%)]" />

        <div className="relative z-10 w-full max-w-lg">
          <Link to="/" className="mb-10 inline-block text-sm font-semibold tracking-[0.22em] text-cyan-300 md:hidden">
            ALFIT
          </Link>

          <div className="mb-8 flex items-center gap-2 text-xs uppercase tracking-[0.24em] text-cyan-300/90">
            <Sparkles size={14} />
            Secure Sign-In
          </div>
          <h2 className="text-4xl font-semibold leading-tight text-white">Welcome back.</h2>
          <p className="mt-3 text-sm leading-relaxed text-slate-400">
            Log in to continue managing your members, messages, and growth metrics.
          </p>

          {error && <div className="mt-6 rounded-xl border border-red-500/35 bg-red-500/10 px-4 py-3 text-sm text-red-200">{error}</div>}

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label className="mb-2 block text-xs font-medium uppercase tracking-[0.2em] text-slate-400">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                <input
                  type="email"
                  placeholder="owner@gym.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-900/70 py-3 pl-11 pr-4 text-slate-100 outline-none transition focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-500/30"
                  required
                />
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-medium uppercase tracking-[0.2em] text-slate-400">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                <input
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-900/70 py-3 pl-11 pr-4 text-slate-100 outline-none transition focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-500/30"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? 'Signing in...' : 'Sign In'}
              {!loading && <ArrowRight size={16} />}
            </button>
          </form>

          <p className="mt-8 text-sm text-slate-400">
            New to Alfit?{' '}
            <Link to="/register" className="font-semibold text-cyan-300 transition hover:text-cyan-200">
              Create your account
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}
