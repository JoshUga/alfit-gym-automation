import { CreditCard } from 'lucide-react';
import { useThemeStore } from '../stores/themeStore';

export default function BillingPage() {
  const isDark = useThemeStore((state) => state.isDark);

  return (
    <div>
      <h1 className={`mb-6 text-3xl font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Billing & Subscription</h1>
      <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {['Basic', 'Pro', 'Enterprise'].map((plan) => (
          <div
            key={plan}
            className={`rounded-2xl border p-6 text-center ${
              plan === 'Pro'
                ? 'border-cyan-400/40 bg-cyan-400/10'
                : isDark
                  ? 'border-slate-800 bg-slate-900/60'
                  : 'border-slate-200 bg-white'
            }`}
          >
            <h3 className={`mb-2 text-xl font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>{plan}</h3>
            <p className="mb-4 text-3xl font-bold text-cyan-500">
              {plan === 'Basic' ? '$29' : plan === 'Pro' ? '$79' : '$199'}
              <span className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>/mo</span>
            </p>
            <ul className={`mb-6 space-y-2 text-sm ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
              <li>{plan === 'Basic' ? '1' : plan === 'Pro' ? '5' : 'Unlimited'} phone numbers</li>
              <li>{plan === 'Basic' ? '100' : plan === 'Pro' ? '1000' : 'Unlimited'} AI messages</li>
              <li>{plan === 'Basic' ? 'Email' : 'Priority'} support</li>
            </ul>
            <button
              className={`w-full rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
                plan === 'Pro'
                  ? 'bg-cyan-400 text-slate-950 hover:bg-cyan-300'
                  : isDark
                    ? 'border border-slate-700 text-slate-200 hover:border-slate-600 hover:bg-slate-800'
                    : 'border border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-100'
              }`}
            >
              {plan === 'Pro' ? 'Current Plan' : 'Select Plan'}
            </button>
          </div>
        ))}
      </div>
      <div className={`rounded-2xl border p-6 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
        <h2 className={`mb-4 flex items-center gap-2 text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
          <CreditCard size={20} />
          Payment History
        </h2>
        <p className={`py-8 text-center ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>No payments yet</p>
      </div>
    </div>
  );
}
