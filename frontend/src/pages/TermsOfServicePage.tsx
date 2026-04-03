export default function TermsOfServicePage() {
  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-200 sm:px-10">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-3xl font-semibold text-white">Terms of Service</h1>
        <p className="mt-6 text-sm leading-7 text-slate-300">
          By using Alfit, you agree to use the platform in compliance with applicable laws and not misuse
          messaging, billing, or member management features. Account owners are responsible for data
          accuracy and authorized team access.
        </p>
        <p className="mt-4 text-sm leading-7 text-slate-300">
          Service availability, maintenance windows, and updates may change over time. Continued use of the
          platform after updates constitutes acceptance of revised terms.
        </p>
      </div>
    </main>
  );
}
