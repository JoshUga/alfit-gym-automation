import { useEffect, useMemo, useState } from 'react';
import { CreditCard, AlertTriangle, Clock3, CheckCircle2 } from 'lucide-react';
import { gymService, memberService } from '../services/api';
import { useThemeStore } from '../stores/themeStore';

interface Member {
  id: number;
  name: string;
  monthly_payment_amount?: number;
}

interface MemberPayment {
  id: number;
  member_id: number;
  amount: number;
  currency: string;
  status: string;
  billing_month?: string;
  paid_at?: string;
}

interface EnrichedPayment extends MemberPayment {
  member_name: string;
}

function currentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

export default function BillingPage() {
  const isDark = useThemeStore((state) => state.isDark);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [members, setMembers] = useState<Member[]>([]);
  const [payments, setPayments] = useState<EnrichedPayment[]>([]);
  const [currency, setCurrency] = useState('UGX');
  const [monthFilter, setMonthFilter] = useState(currentMonth());

  useEffect(() => {
    void loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const gymRes = await gymService.getMine();
      const gym = gymRes.data.data;
      const gymId = gym.id as number;
      const resolvedCurrency = String(gym.preferred_currency || 'UGX').toUpperCase();
      setCurrency(resolvedCurrency);

      const membersRes = await memberService.list(gymId);
      const loadedMembers = (membersRes.data.data || []) as Member[];
      setMembers(loadedMembers);

      const paymentResults = await Promise.allSettled(
        loadedMembers.map(async (member) => {
          const paymentRes = await memberService.listPayments(member.id);
          const rows = (paymentRes.data.data || []) as MemberPayment[];
          return rows.map((payment) => ({ ...payment, member_name: member.name }));
        }),
      );

      const mergedPayments = paymentResults.flatMap((result) => result.status === 'fulfilled' ? result.value : []);
      setPayments(mergedPayments.sort((a, b) => (b.paid_at || '').localeCompare(a.paid_at || '')));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to load payments');
    } finally {
      setLoading(false);
    }
  };

  const monthPayments = useMemo(
    () => payments.filter((payment) => (payment.billing_month || '').slice(0, 7) === monthFilter),
    [payments, monthFilter],
  );

  const byMemberPaidCompleted = useMemo(() => {
    const map = new Map<number, number>();
    monthPayments
      .filter((payment) => payment.status === 'completed')
      .forEach((payment) => map.set(payment.member_id, (map.get(payment.member_id) || 0) + payment.amount));
    return map;
  }, [monthPayments]);

  const arrears = members.filter((member) => {
    const due = member.monthly_payment_amount || 0;
    const paid = byMemberPaidCompleted.get(member.id) || 0;
    return due > 0 && paid < due;
  });
  const unpaidThisMonth = members.filter((member) => {
    const due = member.monthly_payment_amount || 0;
    const paid = byMemberPaidCompleted.get(member.id) || 0;
    return due > 0 && paid === 0;
  });
  const settled = members.filter((member) => {
    const due = member.monthly_payment_amount || 0;
    const paid = byMemberPaidCompleted.get(member.id) || 0;
    return due > 0 && paid >= due;
  });

  const cardClass = isDark ? 'border-slate-800 bg-slate-900/60 text-slate-100' : 'border-slate-200 bg-white text-slate-900';

  return (
    <div className="space-y-6">
      <div>
        <h1 className={`flex items-center gap-2 text-3xl font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
          <CreditCard size={24} />
          Payments
        </h1>
        <p className={`mt-2 text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>Monitor arrears, upcoming dues, and all transactions in one place.</p>
      </div>

      {error && <div className={`rounded-xl border p-3 text-sm ${isDark ? 'border-red-500/40 bg-red-500/10 text-red-200' : 'border-red-300 bg-red-50 text-red-700'}`}>{error}</div>}

      <div className={`rounded-2xl border p-4 ${cardClass}`}>
        <label className={`mb-2 block text-xs uppercase tracking-[0.14em] ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Billing Month</label>
        <input type="month" className="input-field max-w-[220px]" value={monthFilter} onChange={(e) => setMonthFilter(e.target.value)} />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className={`rounded-2xl border p-4 ${cardClass}`}>
          <p className="flex items-center gap-2 text-sm font-semibold text-amber-500"><AlertTriangle size={16} /> Arrears</p>
          <p className="mt-2 text-2xl font-semibold">{arrears.length}</p>
        </div>
        <div className={`rounded-2xl border p-4 ${cardClass}`}>
          <p className="flex items-center gap-2 text-sm font-semibold text-cyan-500"><Clock3 size={16} /> Unpaid This Month</p>
          <p className="mt-2 text-2xl font-semibold">{unpaidThisMonth.length}</p>
        </div>
        <div className={`rounded-2xl border p-4 ${cardClass}`}>
          <p className="flex items-center gap-2 text-sm font-semibold text-emerald-500"><CheckCircle2 size={16} /> Settled</p>
          <p className="mt-2 text-2xl font-semibold">{settled.length}</p>
        </div>
      </div>

      <div className={`rounded-2xl border p-4 ${cardClass}`}>
        <h2 className={`mb-3 text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Monthly Member Status</h2>
        {loading ? (
          <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Loading payments...</p>
        ) : members.length === 0 ? (
          <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>No members yet.</p>
        ) : (
          <div className="space-y-2">
            {members.map((member) => {
              const due = member.monthly_payment_amount || 0;
              const paid = byMemberPaidCompleted.get(member.id) || 0;
              const remaining = Math.max(due - paid, 0);
              return (
                <div key={member.id} className={`grid grid-cols-1 gap-2 border p-3 sm:grid-cols-[1fr_auto_auto_auto] ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
                  <span className={isDark ? 'text-slate-200' : 'text-slate-700'}>{member.name}</span>
                  <span className="text-xs">{currency} due: {due}</span>
                  <span className="text-xs">{currency} paid: {paid}</span>
                  <span className={`text-xs font-semibold ${remaining > 0 ? 'text-amber-500' : 'text-emerald-500'}`}>
                    {remaining > 0 ? `arrears ${currency} ${remaining}` : 'settled'}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className={`rounded-2xl border p-4 ${cardClass}`}>
        <h2 className={`mb-3 text-lg font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>All Payments</h2>
        {loading ? (
          <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Loading payment history...</p>
        ) : payments.length === 0 ? (
          <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>No payments recorded yet.</p>
        ) : (
          <div className="space-y-2">
            {payments.map((payment) => (
              <div key={payment.id} className={`grid grid-cols-1 gap-2 border p-3 sm:grid-cols-[1fr_auto_auto_auto] ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
                <span className={isDark ? 'text-slate-200' : 'text-slate-700'}>{payment.member_name}</span>
                <span className="text-xs">{payment.currency} {payment.amount}</span>
                <span className="text-xs">{payment.billing_month || 'N/A'}</span>
                <span className={`text-xs uppercase ${payment.status === 'completed' ? 'text-emerald-500' : payment.status === 'pending' ? 'text-amber-500' : 'text-red-500'}`}>
                  {payment.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
