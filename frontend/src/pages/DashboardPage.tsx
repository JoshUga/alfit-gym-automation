import { useEffect, useMemo, useState } from 'react';
import {
  Users,
  Phone,
  Bell,
  MessageSquare,
  CalendarClock,
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Activity,
  Inbox,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';
import { analyticsService, attendanceService, gymService, memberService } from '../services/api';
import { useThemeStore } from '../stores/themeStore';

type GymSummary = {
  id: number;
  name: string;
  preferred_currency: string;
  address?: string | null;
};

type KPIData = {
  total_members?: number;
  active_phone_numbers?: number;
  messages_sent_7d?: number;
  messages_sent_30d?: number;
  notification_delivery_rate?: number;
};

type AttendanceRecord = {
  id: number;
  member_id: number;
  attendance_date: string;
  status: 'present' | 'absent';
};

type MessageLog = {
  id: number;
  sender: string;
  recipient: string;
  content?: string | null;
  message_type: 'incoming' | 'outgoing';
  status?: string | null;
  created_at?: string | null;
};

type PhoneNumber = {
  id: number;
  phone_number: string;
  label?: string | null;
  is_active: boolean;
};

type Member = {
  id: number;
  name: string;
};

type AlertItem = {
  title: string;
  detail: string;
  level: 'warning' | 'ok';
};

function pad(value: number) {
  return String(value).padStart(2, '0');
}

function localDateKey(date: Date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function localDateDaysAgo(days: number) {
  const date = new Date();
  date.setHours(0, 0, 0, 0);
  date.setDate(date.getDate() - days);
  return date;
}

function formatRelativeTime(value?: string | null) {
  if (!value) {
    return 'just now';
  }

  const diffMs = Date.now() - new Date(value).getTime();
  const diffMinutes = Math.max(1, Math.round(diffMs / 60000));

  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }

  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }

  const diffDays = Math.round(diffHours / 24);
  return `${diffDays}d ago`;
}

export default function DashboardPage() {
  const isDark = useThemeStore((state) => state.isDark);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [gym, setGym] = useState<GymSummary | null>(null);
  const [kpis, setKpis] = useState<KPIData | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([]);
  const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>([]);
  const [messageLogs, setMessageLogs] = useState<MessageLog[]>([]);

  useEffect(() => {
    void loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    setError('');

    try {
      let resolvedGym: GymSummary;
      const storedGymId = localStorage.getItem('active_gym_id');

      if (storedGymId && Number.isFinite(Number(storedGymId))) {
        try {
          const gymRes = await gymService.get(Number(storedGymId));
          resolvedGym = gymRes.data.data as GymSummary;
        } catch {
          const gymRes = await gymService.getMine();
          resolvedGym = gymRes.data.data as GymSummary;
        }
      } else {
        const gymRes = await gymService.getMine();
        resolvedGym = gymRes.data.data as GymSummary;
      }

      setGym(resolvedGym);
      localStorage.setItem('active_gym_id', String(resolvedGym.id));
      localStorage.setItem('active_gym_currency', String(resolvedGym.preferred_currency || 'UGX').toUpperCase());

      const fromDate = localDateKey(localDateDaysAgo(29));
      const today = localDateKey(new Date());

      const [kpiRes, memberRes, phoneRes, attendanceRes, messageRes] = await Promise.all([
        analyticsService.getKPIs(resolvedGym.id),
        memberService.list(resolvedGym.id),
        gymService.getPhoneNumbers(resolvedGym.id),
        attendanceService.listRecords(resolvedGym.id, { start_date: fromDate, end_date: today }),
        analyticsService.getMessageLogs(resolvedGym.id),
      ]);

      setKpis((kpiRes.data.data || {}) as KPIData);
      setMembers((memberRes.data.data || []) as Member[]);
      setPhoneNumbers((phoneRes.data.data || []) as PhoneNumber[]);
      setAttendanceRecords((attendanceRes.data.data || []) as AttendanceRecord[]);
      setMessageLogs((messageRes.data.data || []) as MessageLog[]);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to load live dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const currency = gym?.preferred_currency || localStorage.getItem('active_gym_currency') || 'UGX';
  const totalMembers = kpis?.total_members ?? members.length;
  const activePhoneNumbers = kpis?.active_phone_numbers ?? phoneNumbers.filter((phone) => phone.is_active).length;
  const messagesSent7d = kpis?.messages_sent_7d ?? 0;
  const messagesSent30d = kpis?.messages_sent_30d ?? 0;
  const deliveryRate = kpis?.notification_delivery_rate ?? 0;

  const todayKey = localDateKey(new Date());
  const weeklyDates = useMemo(() => {
    return Array.from({ length: 7 }, (_, index) => {
      const date = localDateDaysAgo(6 - index);
      return localDateKey(date);
    });
  }, []);

  const weeklyAttendance = useMemo(() => {
    return weeklyDates.map((dateKey) => {
      const dayRecords = attendanceRecords.filter((record) => record.attendance_date === dateKey);
      return {
        dateKey,
        label: new Date(`${dateKey}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short' }),
        present: dayRecords.filter((record) => record.status === 'present').length,
        absent: dayRecords.filter((record) => record.status === 'absent').length,
      };
    });
  }, [attendanceRecords, weeklyDates]);

  const weeklyMessages = useMemo(() => {
    const volumeMap = new Map<string, { incoming: number; outgoing: number }>();

    messageLogs.forEach((log) => {
      if (!log.created_at) {
        return;
      }
      const dateKey = localDateKey(new Date(log.created_at));
      const bucket = volumeMap.get(dateKey) || { incoming: 0, outgoing: 0 };
      bucket[log.message_type] += 1;
      volumeMap.set(dateKey, bucket);
    });

    return weeklyDates.map((dateKey) => {
      const bucket = volumeMap.get(dateKey) || { incoming: 0, outgoing: 0 };
      return {
        dateKey,
        label: new Date(`${dateKey}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short' }),
        incoming: bucket.incoming,
        outgoing: bucket.outgoing,
      };
    });
  }, [messageLogs, weeklyDates]);

  const todaysAttendance = attendanceRecords.filter((record) => record.attendance_date === todayKey);
  const todayPresent = todaysAttendance.filter((record) => record.status === 'present').length;
  const todayAbsent = todaysAttendance.filter((record) => record.status === 'absent').length;
  const weekPresent = weeklyAttendance.reduce((total, item) => total + item.present, 0);
  const weekAbsent = weeklyAttendance.reduce((total, item) => total + item.absent, 0);

  const alerts: AlertItem[] = useMemo(() => {
    const items: AlertItem[] = [];

    if (members.length === 0) {
      items.push({
        title: 'No members enrolled yet',
        detail: 'Add the first member to start tracking attendance, messaging, and payments.',
        level: 'warning',
      });
    }

    if (activePhoneNumbers === 0) {
      items.push({
        title: 'No active phone line connected',
        detail: 'Connect a WhatsApp number to send messages from this gym.',
        level: 'warning',
      });
    }

    if (messagesSent7d > 0 && deliveryRate > 0 && deliveryRate < 85) {
      items.push({
        title: 'Message delivery rate needs attention',
        detail: `Only ${deliveryRate}% of outbound messages were delivered in the recent window.`,
        level: 'warning',
      });
    }

    if (items.length === 0) {
      items.push({
        title: 'All systems are healthy',
        detail: `${totalMembers} members, ${activePhoneNumbers} active phone line${activePhoneNumbers === 1 ? '' : 's'}, and ${messagesSent7d} outbound messages in the last 7 days.`,
        level: 'ok',
      });
    }

    return items.slice(0, 3);
  }, [activePhoneNumbers, deliveryRate, members.length, messagesSent7d, totalMembers]);

  const overviewCards = [
    {
      title: 'Active Members',
      value: totalMembers.toLocaleString(),
      detail: 'Members currently linked to this gym.',
      icon: Users,
      color: 'from-cyan-400 to-blue-500',
    },
    {
      title: 'Connected Lines',
      value: activePhoneNumbers.toLocaleString(),
      detail: 'Active WhatsApp phone numbers ready to send.',
      icon: Phone,
      color: 'from-emerald-400 to-teal-500',
    },
    {
      title: 'Check-ins Today',
      value: `${todayPresent}`,
      detail: `${todayAbsent} absent record${todayAbsent === 1 ? '' : 's'} logged today.`,
      icon: CalendarClock,
      color: 'from-amber-400 to-orange-500',
    },
    {
      title: 'Messages Sent (7d)',
      value: messagesSent7d.toLocaleString(),
      detail: `${messagesSent30d.toLocaleString()} sent in the last 30 days.`,
      icon: MessageSquare,
      color: 'from-fuchsia-500 to-rose-500',
    },
  ];

  const peakAttendance = Math.max(...weeklyAttendance.map((item) => item.present + item.absent), 1);
  return (
    <div className="space-y-6">
      <div className="mb-2 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-500/80">Live gym overview</p>
          <h1 className={`mt-2 text-3xl font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            {gym?.name || 'Gym Dashboard'}
          </h1>
          <p className={`mt-2 max-w-2xl text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Real activity from the active gym, including members, phone numbers, attendance, and message delivery.
          </p>
          <p className={`mt-2 text-xs ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
            Currency: {currency} {gym?.address ? `• ${gym.address}` : ''}
          </p>
        </div>
        <button
          type="button"
          className={`inline-flex items-center gap-2 border px-4 py-2 text-sm font-medium transition ${
            isDark
              ? 'border-slate-700 bg-slate-900/70 text-slate-200 hover:border-slate-500'
              : 'border-slate-300 bg-white text-slate-800 hover:border-slate-400'
          }`}
        >
          <TrendingUp size={16} />
          Generate Weekly Report
        </button>
      </div>

      {error && <div className="border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{error}</div>}

      {loading ? (
        <div className={`border p-6 text-sm ${isDark ? 'border-slate-800 bg-slate-900/60 text-slate-300' : 'border-slate-200 bg-white text-slate-600'}`}>
          Loading live gym data...
        </div>
      ) : (
        <>
          <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {overviewCards.map(({ title, value, detail, icon: Icon, color }) => (
              <article
                key={title}
                className={`border p-5 ${isDark ? 'border-slate-800 bg-slate-900/70' : 'border-slate-200 bg-white'}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className={`text-xs uppercase tracking-[0.16em] ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{title}</p>
                    <p className={`mt-2 text-3xl font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>{value}</p>
                    <p className={`mt-2 text-xs ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{detail}</p>
                  </div>
                  <div className={`bg-gradient-to-br p-3 text-white shadow-lg ${color}`}>
                    <Icon size={20} />
                  </div>
                </div>
              </article>
            ))}
          </section>

          <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <article className={`border p-6 xl:col-span-2 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Weekly Check-in Trend</h2>
                  <p className={`mt-1 text-xs ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                    Present and absent attendance records captured over the last 7 days.
                  </p>
                </div>
                <div className={`inline-flex items-center gap-1 px-2 py-1 text-xs ${isDark ? 'bg-emerald-500/15 text-emerald-300' : 'bg-emerald-100 text-emerald-700'}`}>
                  <ArrowUpRight size={14} />
                  {weekPresent} present this week
                </div>
              </div>

              <div className="mt-6 grid grid-cols-7 gap-2">
                {weeklyAttendance.map((day) => {
                  const height = Math.max(10, ((day.present + day.absent) / peakAttendance) * 100);

                  return (
                    <div key={day.dateKey} className="flex flex-col items-center gap-2">
                      <div className={`relative h-40 w-full overflow-hidden ${isDark ? 'bg-slate-800' : 'bg-slate-100'}`}>
                        <div
                          className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-cyan-500 via-cyan-400 to-emerald-300"
                          style={{ height: `${height}%` }}
                        />
                        <div className="absolute bottom-2 left-0 right-0 text-center text-[11px] font-medium text-slate-950">
                          {day.present + day.absent}
                        </div>
                      </div>
                      <div className="text-center">
                        <span className={`text-xs ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{day.label}</span>
                        <p className={`mt-1 text-[11px] ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
                          {day.present} P / {day.absent} A
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </article>

            <article className={`border p-6 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
              <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Live Alerts</h2>
              <div className="mt-4 space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.title}
                    className={`border p-3 ${isDark ? 'border-slate-800 bg-slate-950/70' : 'border-slate-200 bg-slate-50'}`}
                  >
                    <div className="flex items-start gap-2">
                      {alert.level === 'warning' ? (
                        <AlertTriangle size={16} className="mt-0.5 text-amber-500" />
                      ) : (
                        <CheckCircle2 size={16} className="mt-0.5 text-emerald-500" />
                      )}
                      <div>
                        <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-slate-900'}`}>{alert.title}</p>
                        <p className={`mt-1 text-xs ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{alert.detail}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className={`mt-5 border p-4 ${isDark ? 'border-slate-800 bg-slate-950/60' : 'border-slate-200 bg-slate-50'}`}>
                <div className="flex items-center gap-2">
                  <ShieldCheck size={16} className="text-cyan-500" />
                  <p className={`text-sm font-medium ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>Attendance summary</p>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-3 text-center text-xs">
                  <div>
                    <p className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>{weekPresent}</p>
                    <p className={isDark ? 'text-slate-400' : 'text-slate-600'}>Present</p>
                  </div>
                  <div>
                    <p className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>{weekAbsent}</p>
                    <p className={isDark ? 'text-slate-400' : 'text-slate-600'}>Absent</p>
                  </div>
                  <div>
                    <p className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>{deliveryRate.toFixed(0)}%</p>
                    <p className={isDark ? 'text-slate-400' : 'text-slate-600'}>Delivery</p>
                  </div>
                </div>
              </div>
            </article>
          </section>

          <section className="grid grid-cols-1 gap-6 lg:grid-cols-5">
            <article className={`border p-6 lg:col-span-3 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Recent Message Activity</h2>
                  <p className={`mt-1 text-xs ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                    Most recent inbound and outbound WhatsApp logs from this gym.
                  </p>
                </div>
                <div className={`inline-flex items-center gap-1 px-2 py-1 text-xs ${isDark ? 'bg-cyan-500/15 text-cyan-300' : 'bg-cyan-100 text-cyan-700'}`}>
                  <Activity size={14} />
                  {messagesSent7d} outbound / 7d
                </div>
              </div>

              <div className="mt-5 space-y-3">
                {messageLogs.slice(0, 5).map((log) => {
                  const isIncoming = log.message_type === 'incoming';
                  const preview = log.content?.trim() || 'No message content available';

                  return (
                    <div
                      key={log.id}
                      className={`border p-4 ${isDark ? 'border-slate-800 bg-slate-950/70' : 'border-slate-50 bg-slate-50'}`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="flex items-start gap-3">
                          <div className={`mt-0.5 rounded-full p-2 ${isIncoming ? 'bg-amber-500/15 text-amber-500' : 'bg-emerald-500/15 text-emerald-500'}`}>
                            {isIncoming ? <Inbox size={15} /> : <MessageSquare size={15} />}
                          </div>
                          <div>
                            <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-slate-900'}`}>
                              {isIncoming ? 'Incoming' : 'Outgoing'} message
                            </p>
                            <p className={`mt-1 text-xs ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                              {log.sender} → {log.recipient}
                            </p>
                            <p className={`mt-2 text-sm ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{preview}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-xs uppercase tracking-[0.14em] ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
                            {log.status || 'unknown'}
                          </p>
                          <p className={`mt-1 text-xs ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
                            {formatRelativeTime(log.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}

                {messageLogs.length === 0 && (
                  <div className={`border border-dashed p-4 text-sm ${isDark ? 'border-slate-800 text-slate-400' : 'border-slate-300 text-slate-600'}`}>
                    No message activity has been logged for this gym yet.
                  </div>
                )}
              </div>
            </article>

            <article className={`border p-6 lg:col-span-2 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
              <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Connected Lines</h2>
              <div className="mt-4 space-y-3">
                {phoneNumbers.map((phone) => (
                  <div
                    key={phone.id}
                    className={`border p-3 ${isDark ? 'border-slate-800 bg-slate-950/70' : 'border-slate-50 bg-slate-50'}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-slate-900'}`}>
                          {phone.label || 'WhatsApp line'}
                        </p>
                        <p className={`mt-1 text-xs ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>{phone.phone_number}</p>
                      </div>
                      <span
                        className={`rounded-full px-2 py-1 text-[11px] uppercase tracking-[0.14em] ${
                          phone.is_active
                            ? isDark
                              ? 'bg-emerald-500/15 text-emerald-300'
                              : 'bg-emerald-100 text-emerald-700'
                            : isDark
                              ? 'bg-slate-800 text-slate-400'
                              : 'bg-slate-200 text-slate-600'
                        }`}
                      >
                        {phone.is_active ? 'active' : 'inactive'}
                      </span>
                    </div>
                  </div>
                ))}

                {phoneNumbers.length === 0 && (
                  <div className={`border border-dashed p-4 text-sm ${isDark ? 'border-slate-800 text-slate-400' : 'border-slate-300 text-slate-600'}`}>
                    No phone numbers are connected yet.
                  </div>
                )}
              </div>

              <div className={`mt-5 border p-4 ${isDark ? 'border-slate-800 bg-slate-950/60' : 'border-slate-200 bg-slate-50'}`}>
                <div className="flex items-center gap-2">
                  <Bell size={16} className="text-fuchsia-500" />
                  <p className={`text-sm font-medium ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>Today&apos;s activity</p>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <p className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>{todayPresent}</p>
                    <p className={isDark ? 'text-slate-400' : 'text-slate-600'}>Check-ins</p>
                  </div>
                  <div>
                    <p className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>{messagesSent7d}</p>
                    <p className={isDark ? 'text-slate-400' : 'text-slate-600'}>Outbox (7d)</p>
                  </div>
                </div>
              </div>
            </article>
          </section>

          <section className={`border p-6 ${isDark ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'}`}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Quick Admin Actions</h2>
                <p className={`mt-1 text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Shortcuts for common tasks tied to the active gym.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button className="bg-cyan-500 px-4 py-2 text-sm font-medium text-slate-950 transition hover:bg-cyan-400">Create Campaign</button>
                <button className="bg-emerald-500 px-4 py-2 text-sm font-medium text-slate-950 transition hover:bg-emerald-400">Export Members</button>
                <button className="bg-amber-400 px-4 py-2 text-sm font-medium text-slate-950 transition hover:bg-amber-300">Review Billing Issues</button>
              </div>
            </div>
            <p className={`mt-4 text-xs ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
              Weekly attendance totals: {weekPresent} present, {weekAbsent} absent. Delivery rate: {deliveryRate.toFixed(1)}%.
            </p>
            <p className={`mt-2 text-xs ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
              Weekly message volume: {weeklyMessages.reduce((total, day) => total + day.incoming + day.outgoing, 0)} logs total.
            </p>
          </section>
        </>
      )}
    </div>
  );
}