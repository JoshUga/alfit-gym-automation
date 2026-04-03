import { useEffect, useState } from 'react';
import { Users, Phone, Bell, MessageSquare, Sparkles, CheckCircle2, Loader2 } from 'lucide-react';
import Card from '../components/Card';
import { useThemeStore } from '../stores/themeStore';
import { gymService } from '../services/api';
import { useAuthStore } from '../stores/authStore';

function isConnectedStatus(status: string) {
  return ['open', 'opened', 'connected', 'online'].includes(status.trim().toLowerCase());
}

export default function DashboardPage() {
  const isDark = useThemeStore((state) => state.isDark);
  const user = useAuthStore((state) => state.user);
  const [connectionStatus, setConnectionStatus] = useState('checking');
  const [welcomeState, setWelcomeState] = useState('idle');

  useEffect(() => {
    let cancelled = false;

    const runOnboardingWelcome = async () => {
      try {
        let gymId = Number(localStorage.getItem('active_gym_id') || '0');
        if (!gymId) {
          const mineRes = await gymService.getMine();
          gymId = Number(mineRes.data?.data?.id || 0);
          if (gymId) {
            localStorage.setItem('active_gym_id', String(gymId));
          }
        }

        if (!gymId) {
          if (!cancelled) {
            setConnectionStatus('unknown');
          }
          return;
        }

        const statusRes = await gymService.getWhatsAppStatus(gymId);
        const status = String(statusRes.data?.data?.status || 'unknown').toLowerCase();

        if (cancelled) {
          return;
        }

        setConnectionStatus(status);
        if (!isConnectedStatus(status)) {
          return;
        }

        const welcomeKey = `onboarding_welcome_sent_${gymId}`;
        if (localStorage.getItem(welcomeKey) === '1') {
          setWelcomeState('sent');
          return;
        }

        setWelcomeState('sending');
        const phone = localStorage.getItem(`onboarding_whatsapp_phone_${gymId}`) || undefined;

        const welcomeRes = await gymService.sendOnboardingWelcome(gymId, {
          phone_number: phone,
          owner_name: user?.full_name || undefined,
        });

        if (!cancelled) {
          const resultStatus = welcomeRes.data?.data?.status;
          if (resultStatus === 'sent') {
            localStorage.setItem(welcomeKey, '1');
            setWelcomeState('sent');
          } else {
            setWelcomeState('error');
          }
        }
      } catch {
        if (!cancelled) {
          setWelcomeState('error');
        }
      }
    };

    void runOnboardingWelcome();

    return () => {
      cancelled = true;
    };
  }, [user?.full_name]);

  return (
    <div>
      <div className={`mb-6 overflow-hidden rounded-2xl border p-5 ${isDark ? 'border-cyan-900/50 bg-gradient-to-r from-slate-900 via-cyan-950/40 to-slate-900' : 'border-cyan-200 bg-gradient-to-r from-cyan-50 via-white to-emerald-50'}`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className={`text-xs uppercase tracking-[0.2em] ${isDark ? 'text-cyan-300' : 'text-cyan-700'}`}>WhatsApp Connection</p>
            <p className={`mt-2 text-sm ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
              Status: <span className="font-semibold capitalize">{connectionStatus}</span>
            </p>
          </div>

          <div className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${
            welcomeState === 'sent'
              ? 'bg-emerald-500/20 text-emerald-300'
              : welcomeState === 'sending'
                ? 'bg-amber-500/20 text-amber-200'
                : 'bg-slate-700/40 text-slate-300'
          }`}>
            {welcomeState === 'sending' ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {welcomeState === 'sent' && 'Welcome message delivered'}
            {welcomeState === 'sending' && 'Sending your first welcome note...'}
            {welcomeState === 'idle' && 'Welcome note pending'}
            {welcomeState === 'error' && 'Welcome note failed (will retry on refresh)'}
          </div>
        </div>
      </div>

      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-500/80">Operations snapshot</p>
          <h1 className={`mt-2 text-3xl font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Dashboard</h1>
          <p className={`mt-2 text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Your gym metrics and communication activity at a glance.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
        <Card title="Total Members" value={0} icon={<Users size={24} />} />
        <Card
          title="Active Phone Numbers"
          value={0}
          icon={<Phone size={24} />}
          color="text-green-600"
        />
        <Card
          title="Notifications Sent"
          value={0}
          icon={<Bell size={24} />}
          color="text-yellow-600"
        />
        <Card
          title="Messages (7d)"
          value={0}
          icon={<MessageSquare size={24} />}
          color="text-blue-600"
        />
      </div>

      <div className={`mt-8 rounded-2xl border p-6 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
        <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Performance Notes</h2>
        <p className={`mt-2 text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
          Data widgets will automatically expand here as member, notification, and billing activity increases.
        </p>
        {isConnectedStatus(connectionStatus) && (
          <p className="mt-3 inline-flex items-center gap-2 rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-300">
            <CheckCircle2 size={14} /> WhatsApp line is active (Open)
          </p>
        )}
      </div>
    </div>
  );
}
