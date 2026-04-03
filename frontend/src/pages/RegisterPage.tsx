import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight, ChevronLeft, Sparkles } from 'lucide-react';
import { authService, gymService } from '../services/api';
import { useAuthStore } from '../stores/authStore';

const REGISTRATION_STEPS = ['Owner account', 'Gym profile', 'WhatsApp number', 'Scan QR'];

function isConnectedStatus(status: string) {
  return ['open', 'connected', 'online'].includes(status);
}

export default function RegisterPage() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const setTokens = useAuthStore((state) => state.setTokens);
  const logout = useAuthStore((state) => state.logout);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [gymName, setGymName] = useState('');
  const [gymEmail, setGymEmail] = useState('');
  const [gymPhone, setGymPhone] = useState('');
  const [gymAddress, setGymAddress] = useState('');
  const [whatsAppPhone, setWhatsAppPhone] = useState('');
  const [qrCode, setQrCode] = useState('');
  const [pairingCode, setPairingCode] = useState('');
  const [createdGymId, setCreatedGymId] = useState<number | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState('');
  const [setupDone, setSetupDone] = useState(false);
  const [onboardingMessageSent, setOnboardingMessageSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!setupDone || !createdGymId) {
      return;
    }

    let cancelled = false;
    let pollingComplete = false;
    let redirectTimeout: number | null = null;
    let intervalId: number | null = null;

    const pollStatus = async () => {
      if (pollingComplete) {
        return;
      }

      try {
        const statusRes = await gymService.getWhatsAppStatus(createdGymId);
        const status = String(statusRes.data.data.status || '').toLowerCase();

        if (cancelled) {
          return;
        }

        setConnectionStatus(status || 'pending_connection');
        if (isConnectedStatus(status)) {
          if (!onboardingMessageSent && whatsAppPhone) {
            try {
              await gymService.sendOnboardingWelcome(createdGymId, {
                phone_number: whatsAppPhone,
                owner_name: fullName || undefined,
              });
            } catch {
              // Do not block redirect if welcome send fails.
            } finally {
              if (!cancelled) {
                setOnboardingMessageSent(true);
              }
            }
          }

          pollingComplete = true;
          if (intervalId !== null) {
            window.clearInterval(intervalId);
          }
          redirectTimeout = window.setTimeout(() => navigate('/app'), 800);
        }
      } catch {
        if (!cancelled) {
          setConnectionStatus((currentStatus) => currentStatus || 'pending_connection');
        }
      }
    };

    void pollStatus();
    intervalId = window.setInterval(() => {
      void pollStatus();
    }, 3000);

    return () => {
      cancelled = true;
      if (intervalId !== null) {
        window.clearInterval(intervalId);
      }
      if (redirectTimeout !== null) {
        window.clearTimeout(redirectTimeout);
      }
    };
  }, [createdGymId, navigate, setupDone, onboardingMessageSent, whatsAppPhone, fullName]);

  const validateStep = (step: number) => {
    if (step === 0) {
      if (!email.trim()) {
        return 'Email is required';
      }
      if (password.length < 8) {
        return 'Password must be at least 8 characters';
      }
      if (password !== confirmPassword) {
        return 'Passwords do not match';
      }
    }

    if (step === 1 && !gymName.trim()) {
      return 'Gym name is required';
    }

    if (step === 2 && !whatsAppPhone.trim()) {
      return 'WhatsApp number is required';
    }

    return '';
  };

  const goToNextStep = () => {
    const validationError = validateStep(currentStep);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError('');
    setCurrentStep((step) => Math.min(step + 1, 2));
  };

  const goToPreviousStep = () => {
    setError('');
    setCurrentStep((step) => Math.max(step - 1, 0));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const validationError = validateStep(currentStep);
    if (validationError) {
      setError(validationError);
      return;
    }

    setSetupDone(false);
    setOnboardingMessageSent(false);
    setCreatedGymId(null);
    setQrCode('');
    setPairingCode('');
    setConnectionStatus('pending_connection');
    setLoading(true);
    let sessionEstablished = false;
    try {
      const res = await authService.register({ email, password, full_name: fullName || undefined });
      const { access_token, refresh_token } = res.data.data;
      setTokens(access_token, refresh_token);
      const meRes = await authService.getMe();
      login(access_token, refresh_token, meRes.data.data);
      sessionEstablished = true;

      const gymRes = await gymService.register({
        name: gymName,
        address: gymAddress || undefined,
        phone: gymPhone || undefined,
        email: gymEmail || undefined,
      });
      const gymId = gymRes.data.data.id as number;
      setCreatedGymId(gymId);
      localStorage.setItem('active_gym_id', String(gymId));

      const connectRes = await gymService.connectWhatsApp(gymId, {
        phone_number: whatsAppPhone,
      });

      const connectData = connectRes.data.data;
      setQrCode(connectData.qr_code || '');
      setPairingCode(connectData.pairing_code || '');
      setConnectionStatus(String(connectData.status || 'pending_connection').toLowerCase());
      setSetupDone(true);
      setCurrentStep(3);
    } catch (err: unknown) {
      if (!sessionEstablished) {
        logout();
      }
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 md:flex">
      <section className="relative hidden w-[48%] overflow-hidden md:flex">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_18%,rgba(34,211,238,0.22),transparent_40%),radial-gradient(circle_at_80%_80%,rgba(16,185,129,0.25),transparent_45%),linear-gradient(160deg,#020617_5%,#0f172a_56%,#022c22_100%)]" />
        <div className="pointer-events-none absolute -left-20 top-10 h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="pointer-events-none absolute -right-24 bottom-4 h-96 w-96 rounded-full bg-emerald-400/20 blur-3xl" />

        <div className="relative z-10 flex h-full w-full flex-col justify-between p-12 xl:p-16">
          <div>
            <Link to="/" className="text-xl font-semibold tracking-[0.22em] text-cyan-300">
              ALFIT
            </Link>
          </div>
          <div className="max-w-xl">
            <p className="mb-4 text-xs uppercase tracking-[0.28em] text-cyan-300/90">Build your operation layer</p>
            <h1 className="text-5xl font-semibold leading-tight text-white">
              Launch your gym stack in minutes.
            </h1>
            <p className="mt-6 text-base leading-relaxed text-slate-300">
              Set up your owner profile, register your gym, and connect WhatsApp in one streamlined onboarding flow.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-700/70 bg-slate-900/55 p-5 text-sm text-slate-200">
            <p className="mb-2 text-slate-400">Onboarding includes</p>
            <ul className="space-y-2">
              <li>1. Owner account + secure access</li>
              <li>2. Gym identity and profile setup</li>
              <li>3. WhatsApp connection and QR pairing</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="relative flex min-h-screen w-full items-start justify-center px-6 py-10 sm:px-10 md:w-[52%] md:items-center md:px-10 lg:px-14 xl:px-20">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_70%_20%,rgba(34,211,238,0.08),transparent_30%),radial-gradient(circle_at_20%_80%,rgba(16,185,129,0.08),transparent_35%)]" />

        <div className="relative z-10 w-full max-w-xl">
          <Link to="/" className="mb-10 inline-block text-sm font-semibold tracking-[0.22em] text-cyan-300 md:hidden">
            ALFIT
          </Link>

          <div className="mb-8 flex items-center gap-2 text-xs uppercase tracking-[0.24em] text-cyan-300/90">
            <Sparkles size={14} />
            Guided Onboarding
          </div>
          <h2 className="text-4xl font-semibold leading-tight text-white">Create your workspace.</h2>
          <p className="mt-3 text-sm leading-relaxed text-slate-400">
            A three-step setup to get your gym live with automation from day one.
          </p>

          <div className="mt-7 mb-7 flex items-center gap-2">
            {REGISTRATION_STEPS.map((stepLabel, index) => (
              <div key={stepLabel} className="flex min-w-0 flex-1 items-center gap-2">
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                    index < currentStep
                      ? 'bg-emerald-400 text-slate-900'
                      : index === currentStep
                        ? 'bg-cyan-400 text-slate-900'
                        : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {index + 1}
                </div>
                <p className={`truncate text-xs ${index <= currentStep ? 'text-slate-200' : 'text-slate-500'}`}>
                  {stepLabel}
                </p>
              </div>
            ))}
          </div>

          {error && <div className="mb-4 rounded-xl border border-red-500/35 bg-red-500/10 px-4 py-3 text-sm text-red-200">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-5">
            {currentStep === 0 && (
              <>
                <div>
                  <label className="mb-2 block text-xs font-medium uppercase tracking-[0.2em] text-slate-400">Owner Name</label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    <input
                      type="text"
                      placeholder="Full name"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full rounded-xl border border-slate-700 bg-slate-900/70 py-3 pl-11 pr-4 text-slate-100 outline-none transition focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-500/30"
                    />
                  </div>
                </div>
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
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-xs font-medium uppercase tracking-[0.2em] text-slate-400">Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                      <input
                        type="password"
                        placeholder="At least 8 chars"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full rounded-xl border border-slate-700 bg-slate-900/70 py-3 pl-11 pr-4 text-slate-100 outline-none transition focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-500/30"
                        required
                        minLength={8}
                      />
                    </div>
                  </div>
                  <div>
                    <label className="mb-2 block text-xs font-medium uppercase tracking-[0.2em] text-slate-400">Confirm Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                      <input
                        type="password"
                        placeholder="Repeat password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="w-full rounded-xl border border-slate-700 bg-slate-900/70 py-3 pl-11 pr-4 text-slate-100 outline-none transition focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-500/30"
                        required
                        minLength={8}
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            {currentStep === 1 && (
              <>
                <div>
                  <label className="mb-2 block text-xs font-medium uppercase tracking-[0.2em] text-slate-400">Gym Name</label>
                  <input
                    type="text"
                    placeholder="Your gym brand"
                    value={gymName}
                    onChange={(e) => setGymName(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-3 text-slate-100 outline-none transition focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-500/30"
                    required
                  />
                </div>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <input
                    type="email"
                    placeholder="Gym email (optional)"
                    value={gymEmail}
                    onChange={(e) => setGymEmail(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-3 text-slate-100 outline-none transition focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-500/30"
                  />
                  <input
                    type="text"
                    placeholder="Gym phone (optional)"
                    value={gymPhone}
                    onChange={(e) => setGymPhone(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-3 text-slate-100 outline-none transition focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-500/30"
                  />
                </div>
                <input
                  type="text"
                  placeholder="Gym address (optional)"
                  value={gymAddress}
                  onChange={(e) => setGymAddress(e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-3 text-slate-100 outline-none transition focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-500/30"
                />
              </>
            )}

            {currentStep === 2 && (
              <>
                <label className="mb-2 block text-xs font-medium uppercase tracking-[0.2em] text-slate-400">
                  WhatsApp Number
                </label>
                <input
                  type="text"
                  placeholder="WhatsApp number for pairing (required)"
                  value={whatsAppPhone}
                  onChange={(e) => setWhatsAppPhone(e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-3 text-slate-100 outline-none transition focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-500/30"
                  required
                />
                <p className="text-sm text-slate-400">
                  We will auto-generate your WhatsApp instance in the background. Next step will show your QR code.
                </p>
              </>
            )}

            {currentStep === 3 && (
              <div className="rounded-2xl border border-cyan-400/30 bg-cyan-500/5 p-5">
                <h3 className="text-lg font-semibold text-white">Scan QR to Connect</h3>
                <p className="mt-2 text-sm text-slate-300">
                  Status: <span className="font-semibold capitalize">{connectionStatus || 'pending_connection'}</span>
                </p>
                {pairingCode && (
                  <p className="mt-2 text-sm text-slate-300">
                    Pairing code: <span className="font-semibold text-cyan-300">{pairingCode}</span>
                  </p>
                )}
                <div className="mt-4">
                  {qrCode ? (
                    <img src={qrCode} alt="WhatsApp QR code" className="max-w-xs rounded-xl border border-slate-700" />
                  ) : (
                    <p className="text-sm text-slate-400">Preparing QR code...</p>
                  )}
                </div>
                <p className="mt-4 text-sm text-slate-300">
                  Once connection becomes active, Alfit will detect it automatically, send your onboarding welcome message, and redirect you to the dashboard.
                </p>
              </div>
            )}

            <div className="flex items-center justify-between gap-3 pt-2">
              <button
                type="button"
                onClick={goToPreviousStep}
                className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                disabled={currentStep === 0 || loading || currentStep === 3}
              >
                <ChevronLeft size={16} />
                Back
              </button>

              {currentStep < 2 ? (
                <button
                  type="button"
                  onClick={goToNextStep}
                  className="ml-auto inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
                >
                  Continue
                  <ArrowRight size={16} />
                </button>
              ) : currentStep === 2 ? (
                <button
                  type="submit"
                  disabled={loading}
                  className="ml-auto inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {loading ? 'Creating account and generating QR...' : 'Generate QR'}
                  {!loading && <ArrowRight size={16} />}
                </button>
              ) : (
                <button
                  type="button"
                  disabled
                  className="ml-auto inline-flex items-center gap-2 rounded-xl border border-slate-700 px-5 py-3 text-sm font-semibold text-slate-400"
                >
                  Waiting for connection...
                </button>
              )}
            </div>
          </form>

          {setupDone && currentStep !== 3 && (
            <div className="mt-6 rounded-2xl border border-emerald-500/35 bg-emerald-500/10 p-5">
              <p className="text-sm font-medium text-emerald-200 mb-2">
                Registration complete. WhatsApp connection started.
              </p>
              <p className="mb-2 text-sm text-slate-200">
                Status: <span className="font-semibold capitalize">{connectionStatus || 'pending_connection'}</span>
              </p>
              {pairingCode && (
                <p className="text-sm text-slate-200 mb-2">
                  Pairing code: <span className="font-semibold">{pairingCode}</span>
                </p>
              )}
              {qrCode && <img src={qrCode} alt="WhatsApp QR code" className="max-w-xs rounded-xl border border-slate-700" />}
              <p className="mt-4 text-sm text-slate-300">
                Scan the QR code. Once WhatsApp reports the line is connected, you will be redirected automatically.
              </p>
            </div>
          )}

          <p className="mt-8 text-sm text-slate-400">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-cyan-300 transition hover:text-cyan-200">
              Sign in
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}
