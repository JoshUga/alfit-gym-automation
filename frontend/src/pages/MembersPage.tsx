import { useEffect, useState, useCallback } from 'react';
import { UserPlus, Edit, Trash2, CreditCard } from 'lucide-react';
import DataTable from '../components/DataTable';
import Drawer from '../components/Drawer';
import { gymService, memberService, attendanceService, workoutService } from '../services/api';
import { useAuthStore } from '../stores/authStore';

interface Member {
  id: number;
  name: string;
  email: string;
  phone_number: string;
  status: string;
  schedule: string;
  training_days?: string[];
  target?: string;
  monthly_payment_amount?: number;
  created_at?: string;
  [key: string]: unknown;
}

interface MemberPayment {
  id: number;
  member_id: number;
  gym_id: number;
  amount: number;
  currency: string;
  payment_method?: string;
  status: string;
  billing_month?: string;
  balance_left?: number;
  paid_at?: string;
  note?: string;
}

interface MemberAttendanceSummary {
  member_id: number;
  gym_id: number;
  total_sessions: number;
  present_sessions: number;
  absent_sessions: number;
  attendance_rate: number;
}

interface AttendanceRecord {
  id: number;
  member_id: number;
  attendance_date: string;
  status: 'present' | 'absent';
  note?: string;
}

interface WorkoutPlan {
  id: number;
  member_name?: string;
  target?: string;
  training_days?: string[];
  plan_text: string;
  provider?: string;
  model?: string;
  created_at?: string;
  updated_at?: string;
}

interface WorkoutSessionView {
  day: string;
  warmup: string;
  main: string;
  conditioning: string;
}

interface WorkoutWeekView {
  number: string;
  focus: string;
  sessions: WorkoutSessionView[];
}

type AttendanceCellStatus = 'present' | 'absent' | 'planned' | 'missed' | 'off';

const currentBillingMonth = () => {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  return `${now.getFullYear()}-${month}`;
};

function blankForm() {
  return { name: '', email: '', phoneNumber: '', trainingDays: [] as string[], target: '', monthlyAmount: '' };
}

const WEEK_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const CALENDAR_DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function blankPaymentForm(defaultCurrency = 'UGX') {
  return { amount: '', currency: defaultCurrency, paymentMethod: '', status: 'completed', billingMonth: currentBillingMonth(), note: '' };
}

function resolveTrainingDays(member: Member): string[] {
  if (member.training_days && member.training_days.length > 0) {
    return member.training_days;
  }

  if (member.schedule?.toLowerCase().startsWith('training days:')) {
    const raw = member.schedule.split(':', 2)[1] ?? '';
    return raw.split(',').map((day) => day.trim()).filter(Boolean);
  }

  return [];
}

function isoDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function monthBounds(monthValue: string): { start: string; end: string } {
  const [yearText, monthText] = monthValue.split('-');
  const year = Number(yearText);
  const monthIndex = Number(monthText) - 1;
  const startDate = new Date(Date.UTC(year, monthIndex, 1));
  const endDate = new Date(Date.UTC(year, monthIndex + 1, 0));
  return { start: isoDate(startDate), end: isoDate(endDate) };
}

function listMonthDates(monthValue: string): string[] {
  const [yearText, monthText] = monthValue.split('-');
  const year = Number(yearText);
  const monthIndex = Number(monthText) - 1;
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  const dates: string[] = [];
  for (let day = 1; day <= daysInMonth; day += 1) {
    const dt = new Date(Date.UTC(year, monthIndex, day));
    dates.push(isoDate(dt));
  }
  return dates;
}

function monthLeadingOffset(monthValue: string): number {
  const [yearText, monthText] = monthValue.split('-');
  const year = Number(yearText);
  const monthIndex = Number(monthText) - 1;
  const firstDay = new Date(Date.UTC(year, monthIndex, 1)).getUTCDay();
  return (firstDay + 6) % 7;
}

function dayNameFromIso(iso: string): string {
  const dayIndex = new Date(`${iso}T00:00:00Z`).getUTCDay();
  return WEEK_DAYS[(dayIndex + 6) % 7];
}

function parseWorkoutPlanXml(xmlText: string): WorkoutWeekView[] {
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(xmlText, 'application/xml');
    if (doc.querySelector('parsererror')) {
      return [];
    }

    return Array.from(doc.querySelectorAll('weekly_plan > week')).map((week) => ({
      number: week.getAttribute('number') || '?',
      focus: week.querySelector('focus')?.textContent?.trim() || 'General progression',
      sessions: Array.from(week.querySelectorAll('session')).map((session) => ({
        day: session.querySelector('day')?.textContent?.trim() || 'Planned day',
        warmup: session.querySelector('warmup')?.textContent?.trim() || '',
        main: session.querySelector('main')?.textContent?.trim() || '',
        conditioning: session.querySelector('conditioning')?.textContent?.trim() || '',
      })),
    }));
  } catch {
    return [];
  }
}

function MemberForm({
  form,
  onChange,
  onSubmit,
  onCancel,
  submitLabel,
  submitting,
}: {
  form: ReturnType<typeof blankForm>;
  onChange: (f: ReturnType<typeof blankForm>) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  submitLabel: string;
  submitting: boolean;
}) {
  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      <input
        type="text"
        placeholder="Full Name *"
        className="input-field"
        value={form.name}
        onChange={(e) => onChange({ ...form, name: e.target.value })}
        required
      />
      <input
        type="email"
        placeholder="Email"
        className="input-field"
        value={form.email}
        onChange={(e) => onChange({ ...form, email: e.target.value })}
      />
      <input
        type="tel"
        placeholder="Phone Number * (e.g. +5511999999999)"
        className="input-field"
        value={form.phoneNumber}
        onChange={(e) => onChange({ ...form, phoneNumber: e.target.value })}
        required
      />
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <span>Training Days *</span>
          <span className="art-subtext text-cyan-300/90">Training Days</span>
        </label>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {WEEK_DAYS.map((day) => {
            const checked = form.trainingDays.includes(day);
            return (
              <label
                key={day}
                className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm transition ${
                  checked ? 'border-cyan-400 bg-cyan-500/10 text-cyan-100' : 'border-slate-700 text-slate-300'
                }`}
              >
                <input
                  type="checkbox"
                  className="accent-cyan-400"
                  checked={checked}
                  onChange={(e) => {
                    const nextDays = e.target.checked
                      ? [...form.trainingDays, day]
                      : form.trainingDays.filter((d) => d !== day);
                    onChange({ ...form, trainingDays: nextDays });
                  }}
                />
                {day}
              </label>
            );
          })}
        </div>
      </div>
      <input
        type="text"
        placeholder="Target * (e.g. Lose 5kg in 3 months)"
        className="input-field"
        value={form.target}
        onChange={(e) => onChange({ ...form, target: e.target.value })}
        required
      />
      <input
        type="number"
        min="1"
        step="1"
        placeholder="Monthly Amount *"
        className="input-field"
        value={form.monthlyAmount}
        onChange={(e) => onChange({ ...form, monthlyAmount: e.target.value })}
        required
      />
      <p className="text-xs text-gray-400 mt-1">
        Welcome message content is generated by AI and includes days, target, and monthly payment.
      </p>
      {form.trainingDays.length === 0 && (
        <p className="text-xs text-red-300">Select at least one training day.</p>
      )}
      <div className="flex gap-3 justify-end">
        <button type="button" onClick={onCancel} className="btn-secondary">
          Cancel
        </button>
        <button type="submit" className="btn-primary" disabled={submitting}>
          {submitting ? 'Saving...' : submitLabel}
        </button>
      </div>
    </form>
  );
}

export default function MembersPage() {
  const user = useAuthStore((state) => state.user);
  const isTrainer = user?.role === 'gym_staff';
  const [members, setMembers] = useState<Member[]>([]);
  const [gymId, setGymId] = useState<number | null>(() => {
    const savedGymId = localStorage.getItem('active_gym_id');
    return savedGymId ? Number(savedGymId) : null;
  });
  const [gymCurrency, setGymCurrency] = useState<string>(() => localStorage.getItem('active_gym_currency') || 'UGX');
  const [isAddDrawerOpen, setIsAddDrawerOpen] = useState(false);
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false);
  const [isDeleteDrawerOpen, setIsDeleteDrawerOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<Member | null>(null);
  const [addForm, setAddForm] = useState(blankForm());
  const [editForm, setEditForm] = useState(blankForm());
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [isPaymentDrawerOpen, setIsPaymentDrawerOpen] = useState(false);
  const [isMemberDetailDrawerOpen, setIsMemberDetailDrawerOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [attendanceSummary, setAttendanceSummary] = useState<MemberAttendanceSummary | null>(null);
  const [recentAttendance, setRecentAttendance] = useState<AttendanceRecord[]>([]);
  const [monthAttendance, setMonthAttendance] = useState<Record<string, 'present' | 'absent'>>({});
  const [calendarMonth, setCalendarMonth] = useState(() => currentBillingMonth());
  const [savingAttendanceDate, setSavingAttendanceDate] = useState<string | null>(null);
  const [workoutPlan, setWorkoutPlan] = useState<WorkoutPlan | null>(null);
  const [workoutXmlDraft, setWorkoutXmlDraft] = useState('');
  const [savingWorkoutPlan, setSavingWorkoutPlan] = useState(false);
  const [loadingMemberDetail, setLoadingMemberDetail] = useState(false);
  const [generatingWorkoutPlan, setGeneratingWorkoutPlan] = useState(false);
  const [memberPayments, setMemberPayments] = useState<MemberPayment[]>([]);
  const [paymentForm, setPaymentForm] = useState(blankPaymentForm(gymCurrency));
  const [loadingPayments, setLoadingPayments] = useState(false);

  useEffect(() => {
    void loadMembers();
  }, []);

  useEffect(() => {
    if (!gymId || !selectedMember || !isMemberDetailDrawerOpen) {
      return;
    }

    const loadMonthlyAttendance = async () => {
      try {
        const { start, end } = monthBounds(calendarMonth);
        const res = await attendanceService.listRecords(gymId, {
          member_id: selectedMember.id,
          start_date: start,
          end_date: end,
        });
        const records = (res.data.data || []) as AttendanceRecord[];
        const map: Record<string, 'present' | 'absent'> = {};
        records.forEach((record) => {
          map[record.attendance_date] = record.status;
        });
        setMonthAttendance(map);
      } catch {
        setMonthAttendance({});
      }
    };

    void loadMonthlyAttendance();
  }, [gymId, selectedMember, calendarMonth, isMemberDetailDrawerOpen]);

  const loadMembers = useCallback(async () => {
    setLoading(true);
    setError('');
    let loadedFromCache = false;

    try {
      const storedGymId = localStorage.getItem('active_gym_id');
      if (storedGymId) {
        const parsedGymId = Number(storedGymId);
        if (Number.isFinite(parsedGymId)) {
          try {
            setGymId(parsedGymId);
            if (localStorage.getItem('active_gym_currency')) {
              setGymCurrency(localStorage.getItem('active_gym_currency') || 'UGX');
            }
            const membersRes = await memberService.list(parsedGymId);
            setMembers(membersRes.data.data);
            loadedFromCache = true;
          } catch {
            // Cache can be stale (e.g. gym switched/deleted); force re-resolve from API.
            localStorage.removeItem('active_gym_id');
            setGymId(null);
          }
        }
      }

      if (!loadedFromCache) {
        const gymRes = await gymService.getMine();
        const resolvedGymId = gymRes.data.data.id as number;
        const resolvedCurrency = String(gymRes.data.data.preferred_currency || 'UGX').toUpperCase();
        setGymId(resolvedGymId);
        setGymCurrency(resolvedCurrency);
        localStorage.setItem('active_gym_id', String(resolvedGymId));
        localStorage.setItem('active_gym_currency', resolvedCurrency);

        const membersRes = await memberService.list(resolvedGymId);
        setMembers(membersRes.data.data);
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to load members for your gym');
      setMembers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gymId) {
      setError('No gym is linked to your account yet. Finish gym setup first.');
      return;
    }
    if (addForm.trainingDays.length === 0) {
      setError('Select at least one training day');
      return;
    }

    const monthlyAmount = Number(addForm.monthlyAmount);
    if (!Number.isFinite(monthlyAmount) || monthlyAmount <= 0) {
      setError('Enter a valid monthly amount greater than zero');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      const res = await memberService.create({
        gym_id: gymId,
        name: addForm.name,
        phone_number: addForm.phoneNumber,
        email: addForm.email || undefined,
        schedule: `Training days: ${addForm.trainingDays.join(', ')}`,
        training_days: addForm.trainingDays,
        target: addForm.target,
        monthly_payment_amount: Math.round(monthlyAmount),
      });

      setMembers((currentMembers) => [res.data.data, ...currentMembers]);
      setAddForm(blankForm());
      setIsAddDrawerOpen(false);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to add member');
    } finally {
      setSubmitting(false);
    }
  };

  const openEditModal = (member: Member) => {
    const resolvedTrainingDays = resolveTrainingDays(member);
    setEditingMember(member);
    setEditForm({
      name: member.name,
      email: member.email ?? '',
      phoneNumber: member.phone_number,
      trainingDays: resolvedTrainingDays,
      target: member.target ?? '',
      monthlyAmount: member.monthly_payment_amount ? String(member.monthly_payment_amount) : '',
    });
    setIsEditDrawerOpen(true);
  };

  const handleEditMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingMember) return;
    if (editForm.trainingDays.length === 0) {
      setError('Select at least one training day');
      return;
    }

    const monthlyAmount = Number(editForm.monthlyAmount);
    if (!Number.isFinite(monthlyAmount) || monthlyAmount <= 0) {
      setError('Enter a valid monthly amount greater than zero');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      const res = await memberService.update(editingMember.id, {
        name: editForm.name,
        phone_number: editForm.phoneNumber,
        email: editForm.email || undefined,
        schedule: `Training days: ${editForm.trainingDays.join(', ')}`,
        training_days: editForm.trainingDays,
        target: editForm.target,
        monthly_payment_amount: Math.round(monthlyAmount),
      });
      setMembers((prev) => prev.map((m) => (m.id === editingMember.id ? res.data.data : m)));
      setIsEditDrawerOpen(false);
      setEditingMember(null);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to update member');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteMember = async (memberId: number) => {
    setError('');
    try {
      await memberService.delete(memberId);
      setMembers((prev) => prev.filter((m) => m.id !== memberId));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to remove member');
    } finally {
      setDeleteConfirm(null);
      setIsDeleteDrawerOpen(false);
    }
  };

  const openPaymentDrawer = async (member: Member) => {
    setSelectedMember(member);
    setPaymentForm(blankPaymentForm(gymCurrency));
    setError('');
    setIsPaymentDrawerOpen(true);
    setLoadingPayments(true);
    try {
      const res = await memberService.listPayments(member.id);
      setMemberPayments(res.data.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to load payment history');
      setMemberPayments([]);
    } finally {
      setLoadingPayments(false);
    }
  };

  const handleAddPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMember) {
      return;
    }

    const numericAmount = Number(paymentForm.amount);
    if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
      setError('Enter a valid payment amount greater than zero');
      return;
    }

    if (!paymentForm.billingMonth) {
      setError('Select the month this payment covers');
      return;
    }

    setSubmitting(true);
    setError('');
    try {
      const res = await memberService.createPayment(selectedMember.id, {
        amount: Math.round(numericAmount),
        currency: paymentForm.currency || gymCurrency || 'UGX',
        payment_method: paymentForm.paymentMethod || undefined,
        status: paymentForm.status || 'completed',
        billing_month: paymentForm.billingMonth,
        note: paymentForm.note || undefined,
      });
      setMemberPayments((prev) => [res.data.data, ...prev]);
      setPaymentForm(blankPaymentForm(gymCurrency));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to record payment');
    } finally {
      setSubmitting(false);
    }
  };

  const openMemberDetails = async (member: Member) => {
    if (!gymId) {
      setError('No gym selected');
      return;
    }
    setSelectedMember(member);
    setIsMemberDetailDrawerOpen(true);
    setLoadingMemberDetail(true);
    setCalendarMonth(currentBillingMonth());
    setError('');

    try {
      const month = currentBillingMonth();
      const { start, end } = monthBounds(month);
      const [summaryRes, recordsRes, monthRecordsRes, workoutRes] = await Promise.all([
        attendanceService.memberSummary(gymId, member.id),
        attendanceService.listRecords(gymId, { member_id: member.id }),
        attendanceService.listRecords(gymId, { member_id: member.id, start_date: start, end_date: end }),
        workoutService.getLatest(gymId, member.id),
      ]);
      setAttendanceSummary(summaryRes.data.data);
      setRecentAttendance((recordsRes.data.data || []).slice(0, 10));
      const monthlyMap: Record<string, 'present' | 'absent'> = {};
      ((monthRecordsRes.data.data || []) as AttendanceRecord[]).forEach((record) => {
        monthlyMap[record.attendance_date] = record.status;
      });
      setMonthAttendance(monthlyMap);
      setWorkoutPlan(workoutRes.data.data || null);
      setWorkoutXmlDraft(workoutRes.data.data?.plan_text || '');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to load member details');
      setAttendanceSummary(null);
      setRecentAttendance([]);
      setMonthAttendance({});
      setWorkoutPlan(null);
      setWorkoutXmlDraft('');
    } finally {
      setLoadingMemberDetail(false);
    }
  };

  const handleGenerateWorkoutPlan = async () => {
    if (!gymId || !selectedMember) {
      setError('Missing gym or member context');
      return;
    }

    setGeneratingWorkoutPlan(true);
    setError('');
    try {
      const res = await workoutService.generate(selectedMember.id, {
        gym_id: gymId,
        member_name: selectedMember.name,
        target: selectedMember.target,
        training_days: resolveTrainingDays(selectedMember),
      });
      setWorkoutPlan(res.data.data);
      setWorkoutXmlDraft(res.data.data.plan_text || '');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to generate workout plan');
    } finally {
      setGeneratingWorkoutPlan(false);
    }
  };

  const handleMarkAttendance = async (attendanceDate: string, status: 'present' | 'absent') => {
    if (!gymId || !selectedMember) {
      setError('Missing gym or member context');
      return;
    }

    setSavingAttendanceDate(attendanceDate);
    setError('');
    try {
      await attendanceService.createRecord({
        gym_id: gymId,
        member_id: selectedMember.id,
        attendance_date: attendanceDate,
        status,
      });
      setMonthAttendance((prev) => ({ ...prev, [attendanceDate]: status }));

      const [summaryRes, recordsRes] = await Promise.all([
        attendanceService.memberSummary(gymId, selectedMember.id),
        attendanceService.listRecords(gymId, { member_id: selectedMember.id }),
      ]);
      setAttendanceSummary(summaryRes.data.data);
      setRecentAttendance((recordsRes.data.data || []).slice(0, 10));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to save attendance');
    } finally {
      setSavingAttendanceDate(null);
    }
  };

  const handleSaveWorkoutPlan = async () => {
    if (!workoutPlan || !selectedMember) {
      setError('Generate a workout plan first before editing');
      return;
    }
    if (!workoutXmlDraft.trim()) {
      setError('Workout XML cannot be empty');
      return;
    }

    setSavingWorkoutPlan(true);
    setError('');
    try {
      const res = await workoutService.update(workoutPlan.id, {
        member_name: selectedMember.name,
        target: selectedMember.target,
        training_days: resolveTrainingDays(selectedMember),
        plan_text: workoutXmlDraft,
      });
      setWorkoutPlan(res.data.data);
      setWorkoutXmlDraft(res.data.data.plan_text || workoutXmlDraft);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to update workout plan');
    } finally {
      setSavingWorkoutPlan(false);
    }
  };

  const selectedTrainingDays = selectedMember ? resolveTrainingDays(selectedMember) : [];
  const calendarDates = listMonthDates(calendarMonth);
  const leadingEmptyCells = Array.from({ length: monthLeadingOffset(calendarMonth) });
  const todayIso = isoDate(new Date());
  const parsedWorkoutWeeks = parseWorkoutPlanXml(workoutXmlDraft);

  const attendanceStatusForDate = (dateIso: string): AttendanceCellStatus => {
    const memberCreatedAt = selectedMember?.created_at ? isoDate(new Date(selectedMember.created_at)) : null;
    if (memberCreatedAt && dateIso < memberCreatedAt) {
      return 'off';
    }
    const recorded = monthAttendance[dateIso];
    if (recorded) {
      return recorded;
    }
    const dayName = dayNameFromIso(dateIso);
    const isPlannedDay = selectedTrainingDays.includes(dayName);
    if (!isPlannedDay) {
      return 'off';
    }
    if (dateIso < todayIso) {
      return 'missed';
    }
    return 'planned';
  };

  const attendanceStatusClasses: Record<AttendanceCellStatus, string> = {
    present: 'border-emerald-500/70 bg-emerald-500/15 text-emerald-200',
    absent: 'border-red-500/70 bg-red-500/15 text-red-200',
    planned: 'border-cyan-500/70 bg-cyan-500/15 text-cyan-200',
    missed: 'border-amber-500/70 bg-amber-500/15 text-amber-200',
    off: 'border-slate-700 bg-slate-900/40 text-slate-400',
  };

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'email', label: 'Email' },
    { key: 'phone_number', label: 'Phone' },
    {
      key: 'status',
      label: 'Status',
      render: (m: Member) => (
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            m.status === 'active'
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          {m.status}
        </span>
      ),
    },
    {
      key: 'schedule',
      label: 'Schedule',
      render: (m: Member) => {
        const resolvedTrainingDays = resolveTrainingDays(m);
        return resolvedTrainingDays.length > 0 ? (
          <span className="text-xs text-gray-600 whitespace-pre-line line-clamp-2">{resolvedTrainingDays.join(', ')}</span>
        ) : (
          <span className="text-xs text-gray-400 italic">—</span>
        );
      },
    },
    {
      key: 'target',
      label: 'Target',
      render: (m: Member) => <span className="text-xs text-gray-600">{m.target || '—'}</span>,
    },
    {
      key: 'monthly_payment_amount',
      label: 'Monthly Fee',
      render: (m: Member) => <span className="text-xs text-gray-600">{m.monthly_payment_amount ? `${gymCurrency} ${m.monthly_payment_amount}` : '—'}</span>,
    },
    ...(!isTrainer
      ? [{
          key: 'actions',
          label: 'Actions',
          render: (m: Member) => (
            <div className="flex gap-2">
              <button
                className="p-1 hover:text-emerald-500"
                onClick={(e) => {
                  e.stopPropagation();
                  void openPaymentDrawer(m);
                }}
                title="Manage payments"
              >
                <CreditCard size={16} />
              </button>
              <button
                className="p-1 hover:text-primary-600"
                onClick={(e) => {
                  e.stopPropagation();
                  openEditModal(m);
                }}
                title="Edit member"
              >
                <Edit size={16} />
              </button>
              <button
                className="p-1 hover:text-red-600"
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteConfirm(m.id);
                  setIsDeleteDrawerOpen(true);
                }}
                title="Remove member"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ),
        }]
      : []),
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-semibold text-white">Members</h1>
        <button
          onClick={() => setIsAddDrawerOpen(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-50"
          disabled={!gymId || loading}
          hidden={isTrainer}
        >
          <UserPlus size={18} />
          Add Member
        </button>
      </div>
      {error && <div className="mb-4 rounded-xl border border-red-500/35 bg-red-500/10 p-3 text-sm text-red-200">{error}</div>}
      <div>
        {loading ? (
          <p className="text-sm text-slate-400">Loading members...</p>
        ) : (
          <DataTable columns={columns} data={members} onRowClick={(member) => void openMemberDetails(member as Member)} />
        )}
      </div>

      <Drawer isOpen={isAddDrawerOpen} onClose={() => setIsAddDrawerOpen(false)} title="Add Member">
        <MemberForm
          form={addForm}
          onChange={setAddForm}
          onSubmit={handleAddMember}
          onCancel={() => setIsAddDrawerOpen(false)}
          submitLabel="Add Member"
          submitting={submitting}
        />
      </Drawer>

      <Drawer isOpen={isEditDrawerOpen} onClose={() => setIsEditDrawerOpen(false)} title="Edit Member">
        <MemberForm
          form={editForm}
          onChange={setEditForm}
          onSubmit={handleEditMember}
          onCancel={() => setIsEditDrawerOpen(false)}
          submitLabel="Save Changes"
          submitting={submitting}
        />
      </Drawer>

      <Drawer
        isOpen={isDeleteDrawerOpen && deleteConfirm !== null}
        onClose={() => {
          setIsDeleteDrawerOpen(false);
          setDeleteConfirm(null);
        }}
        title="Remove Member"
      >
        <p className="mb-6 text-sm text-slate-300">
          Are you sure you want to remove this member? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => {
              setIsDeleteDrawerOpen(false);
              setDeleteConfirm(null);
            }}
          >
            Cancel
          </button>
          <button
            type="button"
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700"
            onClick={() => {
              if (deleteConfirm !== null) {
                void handleDeleteMember(deleteConfirm);
              }
            }}
          >
            Remove
          </button>
        </div>
      </Drawer>

      <Drawer
        isOpen={isMemberDetailDrawerOpen}
        onClose={() => {
          setIsMemberDetailDrawerOpen(false);
          setSelectedMember(null);
          setAttendanceSummary(null);
          setRecentAttendance([]);
          setMonthAttendance({});
          setWorkoutXmlDraft('');
          setWorkoutPlan(null);
        }}
        title={selectedMember ? `Member Details - ${selectedMember.name}` : 'Member Details'}
      >
        {loadingMemberDetail ? (
          <p className="text-sm text-slate-400">Loading member details...</p>
        ) : !selectedMember ? (
          <p className="text-sm text-slate-400">Select a member to view details.</p>
        ) : (
          <div className="space-y-6">
            <div className="border border-slate-800 bg-slate-900/50 p-4">
              <h3 className="text-sm font-semibold text-slate-100">Attendance Summary</h3>
              <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-slate-300 sm:grid-cols-4">
                <div>
                  <p className="text-xs text-slate-500">Total</p>
                  <p>{attendanceSummary?.total_sessions ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Present</p>
                  <p>{attendanceSummary?.present_sessions ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Absent</p>
                  <p>{attendanceSummary?.absent_sessions ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Attendance Rate</p>
                  <p>{attendanceSummary?.attendance_rate ?? 0}%</p>
                </div>
              </div>
            </div>

            <div className="border border-slate-800 bg-slate-900/50 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold text-slate-100">Attendance Calendar</h3>
                <input
                  type="month"
                  className="input-field max-w-[190px]"
                  value={calendarMonth}
                  onChange={(e) => setCalendarMonth(e.target.value)}
                />
              </div>

              <div className="mb-3 grid grid-cols-5 gap-2 text-xs">
                <span className="border border-emerald-500/70 bg-emerald-500/15 px-2 py-1 text-emerald-200">Present</span>
                <span className="border border-red-500/70 bg-red-500/15 px-2 py-1 text-red-200">Absent</span>
                <span className="border border-cyan-500/70 bg-cyan-500/15 px-2 py-1 text-cyan-200">Planned</span>
                <span className="border border-amber-500/70 bg-amber-500/15 px-2 py-1 text-amber-200">Missed</span>
                <span className="border border-slate-700 bg-slate-900/40 px-2 py-1 text-slate-400">Off day</span>
              </div>

              <div className="mb-2 grid grid-cols-7 gap-2 text-center text-[11px] uppercase tracking-wide text-slate-500">
                {CALENDAR_DAY_LABELS.map((label) => (
                  <span key={label}>{label}</span>
                ))}
              </div>

              <div className="grid grid-cols-7 gap-2">
                {leadingEmptyCells.map((_, idx) => (
                  <div key={`empty-${idx}`} className="border border-transparent p-2" />
                ))}
                {calendarDates.map((dateIso) => {
                  const status = attendanceStatusForDate(dateIso);
                  const isSaving = savingAttendanceDate === dateIso;
                  return (
                    <div key={dateIso} className={`border p-2 text-xs ${attendanceStatusClasses[status]}`}>
                      <div className="mb-1 flex items-center justify-between">
                        <span className="font-semibold">{Number(dateIso.slice(-2))}</span>
                        <span className="uppercase text-[10px]">{status}</span>
                      </div>
                      {!isTrainer && (
                        <div className="flex gap-1">
                          <button
                            type="button"
                            className="flex-1 border border-emerald-500/60 px-1 py-0.5 text-[10px] text-emerald-200 disabled:opacity-50"
                            disabled={isSaving}
                            onClick={() => void handleMarkAttendance(dateIso, 'present')}
                          >
                            P
                          </button>
                          <button
                            type="button"
                            className="flex-1 border border-red-500/60 px-1 py-0.5 text-[10px] text-red-200 disabled:opacity-50"
                            disabled={isSaving}
                            onClick={() => void handleMarkAttendance(dateIso, 'absent')}
                          >
                            A
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {recentAttendance.length > 0 && (
                <div className="mt-4 space-y-2">
                  <p className="text-xs uppercase tracking-wide text-slate-500">Recent updates</p>
                  {recentAttendance.slice(0, 5).map((record) => (
                    <div key={record.id} className="flex items-center justify-between border border-slate-800 px-3 py-2 text-sm">
                      <span className="text-slate-300">{record.attendance_date}</span>
                      <span className={record.status === 'present' ? 'text-emerald-300' : 'text-amber-300'}>{record.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="border border-slate-800 bg-slate-900/50 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold text-slate-100">Workout Plan</h3>
                {!isTrainer && (
                  <div className="flex items-center gap-2">
                    <button type="button" className="btn-primary" onClick={() => void handleGenerateWorkoutPlan()} disabled={generatingWorkoutPlan}>
                      {generatingWorkoutPlan ? 'Generating...' : 'Regenerate with AI'}
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      disabled={!workoutPlan || savingWorkoutPlan}
                      onClick={() => void handleSaveWorkoutPlan()}
                    >
                      {savingWorkoutPlan ? 'Saving...' : 'Save XML'}
                    </button>
                  </div>
                )}
              </div>
              {workoutPlan ? (
                <>
                  <p className="mb-2 text-xs text-slate-400">
                    Source: {workoutPlan.provider || 'n/a'}
                    {workoutPlan.model ? ` · ${workoutPlan.model}` : ''}
                  </p>
                  <textarea
                    rows={14}
                    className="input-field font-mono text-xs"
                    value={workoutXmlDraft}
                    onChange={(e) => setWorkoutXmlDraft(e.target.value)}
                    placeholder="<workout_plan>...</workout_plan>"
                    readOnly={isTrainer}
                  />
                  {parsedWorkoutWeeks.length > 0 ? (
                    <div className="mt-4 space-y-3">
                      <p className="text-xs uppercase tracking-wide text-slate-500">Week to Week Plan</p>
                      {parsedWorkoutWeeks.map((week) => (
                        <div key={`week-${week.number}`} className="border border-slate-800 bg-slate-950/60 p-3">
                          <p className="text-sm font-semibold text-cyan-200">Week {week.number}</p>
                          <p className="mt-1 text-xs text-slate-400">Focus: {week.focus}</p>
                          <div className="mt-2 space-y-2">
                            {week.sessions.map((session, idx) => (
                              <div key={`${week.number}-${session.day}-${idx}`} className="border border-slate-800/80 p-2">
                                <p className="text-xs font-semibold text-slate-200">{session.day}</p>
                                <p className="text-xs text-slate-400">Warmup: {session.warmup || 'N/A'}</p>
                                <p className="text-xs text-slate-400">Main: {session.main || 'N/A'}</p>
                                <p className="text-xs text-slate-400">Conditioning: {session.conditioning || 'N/A'}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-2 text-xs text-amber-300">XML preview unavailable. Keep valid XML to render week-by-week cards.</p>
                  )}
                </>
              ) : (
                <p className="text-sm text-slate-400">No workout plan yet. It should auto-generate when member is added, or you can generate now.</p>
              )}
            </div>
          </div>
        )}
      </Drawer>

      <Drawer
        isOpen={isPaymentDrawerOpen}
        onClose={() => {
          setIsPaymentDrawerOpen(false);
          setSelectedMember(null);
          setMemberPayments([]);
        }}
        title={selectedMember ? `Payments - ${selectedMember.name}` : 'Member Payments'}
      >
        <form className="space-y-4" onSubmit={handleAddPayment}>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <input
              type="number"
              min="1"
              step="1"
              placeholder="Amount *"
              className="input-field"
              value={paymentForm.amount}
              onChange={(e) => setPaymentForm((prev) => ({ ...prev, amount: e.target.value }))}
              required
            />
            <input
              type="text"
              maxLength={8}
              placeholder={`Currency (${gymCurrency})`}
              className="input-field"
              value={paymentForm.currency}
              onChange={(e) => setPaymentForm((prev) => ({ ...prev, currency: e.target.value.toUpperCase() }))}
            />
            <input
              type="text"
              placeholder="Payment Method"
              className="input-field"
              value={paymentForm.paymentMethod}
              onChange={(e) => setPaymentForm((prev) => ({ ...prev, paymentMethod: e.target.value }))}
            />
            <select
              className="input-field"
              value={paymentForm.status}
              onChange={(e) => setPaymentForm((prev) => ({ ...prev, status: e.target.value }))}
            >
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
            </select>
            <input
              type="month"
              className="input-field"
              value={paymentForm.billingMonth}
              onChange={(e) => setPaymentForm((prev) => ({ ...prev, billingMonth: e.target.value }))}
              required
            />
          </div>
          <textarea
            rows={2}
            placeholder="Note"
            className="input-field min-h-[70px] resize-y"
            value={paymentForm.note}
            onChange={(e) => setPaymentForm((prev) => ({ ...prev, note: e.target.value }))}
          />
          <div className="flex justify-end">
            <button type="submit" className="btn-primary" disabled={submitting || !selectedMember}>
              {submitting ? 'Recording...' : 'Record Payment'}
            </button>
          </div>
        </form>

        <div className="mt-6">
          <h3 className="mb-3 text-sm font-semibold text-slate-200">Payment History</h3>
          {loadingPayments ? (
            <p className="text-sm text-slate-400">Loading payments...</p>
          ) : memberPayments.length === 0 ? (
            <p className="text-sm text-slate-400">No payments recorded yet.</p>
          ) : (
            <div className="space-y-2">
              {memberPayments.map((payment) => (
                <div key={payment.id} className="rounded-lg border border-slate-700/80 bg-slate-900/50 p-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-semibold text-slate-100">
                      {payment.currency} {payment.amount}
                    </span>
                    <span className="text-xs uppercase tracking-wide text-slate-400">{payment.status}</span>
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    {payment.payment_method || 'Method not set'}
                    {payment.paid_at ? ` · ${new Date(payment.paid_at).toLocaleString()}` : ''}
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    For month: {payment.billing_month || 'N/A'}
                    {typeof payment.balance_left === 'number' ? ` · Balance left: ${payment.currency} ${payment.balance_left}` : ''}
                  </div>
                  {payment.note && <p className="mt-1 text-xs text-slate-300">{payment.note}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      </Drawer>
    </div>
  );
}
