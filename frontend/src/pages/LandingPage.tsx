import { Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function LandingPage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return (
    <main className="min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <div className="relative min-h-screen">
        <div className="pointer-events-none absolute -left-28 top-14 h-80 w-80 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="pointer-events-none absolute -right-28 bottom-8 h-96 w-96 rounded-full bg-emerald-400/20 blur-3xl" />

        <section className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-between px-6 py-8 sm:px-10 lg:px-16">
          <header className="flex items-center justify-between">
            <h1 className="text-xl font-semibold tracking-[0.2em] text-cyan-300">ALFIT</h1>
          </header>

          <div className="max-w-3xl pb-14 pt-6 sm:pt-0">
            <p className="mb-4 text-xs uppercase tracking-[0.28em] text-cyan-300/80">Gym operations, simplified</p>
            <h2 className="text-4xl font-semibold leading-tight text-white sm:text-6xl sm:leading-tight">
              Run your gym with clarity, consistency, and less admin noise.
            </h2>
            <p className="mt-6 max-w-2xl text-base leading-relaxed text-slate-300 sm:text-lg">
              Alfit helps modern gyms automate member communication, monitor growth, and keep daily operations focused on people not paperwork.
            </p>

            <div className="mt-10 flex flex-wrap items-center gap-4">
              <Link
                to={isAuthenticated ? '/app' : '/register'}
                className="rounded-full bg-cyan-400 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
              >
                {isAuthenticated ? 'Open Dashboard' : 'Create Account'}
              </Link>
              <Link
                to={isAuthenticated ? '/app' : '/login'}
                className="rounded-full border border-slate-500 px-6 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-300 hover:text-white"
              >
                {isAuthenticated ? 'Go to App' : 'Sign In'}
              </Link>
            </div>
          </div>

          <footer className="border-t border-slate-800 py-4 text-xs text-slate-400">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p>By using Alfit, you agree to our terms and privacy commitments.</p>
              <nav className="flex items-center gap-4 text-xs text-slate-300">
                <Link to="/privacy-policy" className="hover:text-white transition-colors">Privacy</Link>
                <Link to="/terms-of-service" className="hover:text-white transition-colors">Terms</Link>
                <Link to="/data-removal" className="hover:text-white transition-colors">Data Removal</Link>
              </nav>
            </div>
          </footer>
        </section>
      </div>
    </main>
  );
}
