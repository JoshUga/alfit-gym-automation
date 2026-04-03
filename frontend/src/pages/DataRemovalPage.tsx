import { useState } from 'react';

export default function DataRemovalPage() {
  const [email, setEmail] = useState('');
  const [details, setDetails] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-200 sm:px-10">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-3xl font-semibold text-white">Data Removal Request</h1>
        <p className="mt-4 text-sm leading-7 text-slate-300">
          Use this form to request deletion of personal data connected to your account.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <div>
            <label className="mb-2 block text-sm text-slate-300" htmlFor="email">
              Account email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm text-slate-300" htmlFor="details">
              Request details
            </label>
            <textarea
              id="details"
              required
              rows={5}
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            />
          </div>

          <button
            type="submit"
            className="rounded-full bg-cyan-400 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
          >
            Submit request
          </button>
        </form>

        {submitted && (
          <p className="mt-6 text-sm text-emerald-300">
            Request recorded. Our team will follow up via email. You can also contact privacy@alfit.app.
          </p>
        )}
      </div>
    </main>
  );
}
