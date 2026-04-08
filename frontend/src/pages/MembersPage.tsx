import { useEffect, useState, useCallback } from 'react';
import { UserPlus, Edit, Trash2, CreditCard } from 'lucide-react';
import DataTable from '../components/DataTable';
import Drawer from '../components/Drawer';
import { gymService, memberService } from '../services/api';

interface Member {
  id: number;
  name: string;
  email: string;
  phone_number: string;
  status: string;
  schedule: string;
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
  paid_at?: string;
  note?: string;
}

function blankForm() {
  return { name: '', email: '', phoneNumber: '', schedule: '' };
}

function blankPaymentForm() {
  return { amount: '', currency: 'USD', paymentMethod: '', status: 'completed', note: '' };
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
        <label className="block text-sm font-medium text-gray-700 mb-1">Training Schedule</label>
        <textarea
          placeholder={"e.g.\nMonday: Chest & Triceps - 7am\nWednesday: Back & Biceps - 7am\nFriday: Legs - 7am"}
          className="input-field min-h-[100px] resize-y"
          value={form.schedule}
          onChange={(e) => onChange({ ...form, schedule: e.target.value })}
          rows={4}
        />
        <p className="text-xs text-gray-400 mt-1">
          This schedule will be included in the WhatsApp welcome message when delivery succeeds.
        </p>
      </div>
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
  const [members, setMembers] = useState<Member[]>([]);
  const [gymId, setGymId] = useState<number | null>(() => {
    const savedGymId = localStorage.getItem('active_gym_id');
    return savedGymId ? Number(savedGymId) : null;
  });
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
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [memberPayments, setMemberPayments] = useState<MemberPayment[]>([]);
  const [paymentForm, setPaymentForm] = useState(blankPaymentForm());
  const [loadingPayments, setLoadingPayments] = useState(false);

  useEffect(() => {
    void loadMembers();
  }, []);

  const loadMembers = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const storedGymId = localStorage.getItem('active_gym_id');
      if (storedGymId) {
        const parsedGymId = Number(storedGymId);
        if (Number.isFinite(parsedGymId)) {
          setGymId(parsedGymId);
          const membersRes = await memberService.list(parsedGymId);
          setMembers(membersRes.data.data);
        }
      }

      const gymRes = await gymService.getMine();
      const resolvedGymId = gymRes.data.data.id as number;
      setGymId(resolvedGymId);
      localStorage.setItem('active_gym_id', String(resolvedGymId));

      const membersRes = await memberService.list(resolvedGymId);
      setMembers(membersRes.data.data);
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

    setSubmitting(true);
    setError('');
    try {
      const res = await memberService.create({
        gym_id: gymId,
        name: addForm.name,
        phone_number: addForm.phoneNumber,
        email: addForm.email || undefined,
        schedule: addForm.schedule || undefined,
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
    setEditingMember(member);
    setEditForm({
      name: member.name,
      email: member.email ?? '',
      phoneNumber: member.phone_number,
      schedule: member.schedule ?? '',
    });
    setIsEditDrawerOpen(true);
  };

  const handleEditMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingMember) return;
    setSubmitting(true);
    setError('');
    try {
      const res = await memberService.update(editingMember.id, {
        name: editForm.name,
        phone_number: editForm.phoneNumber,
        email: editForm.email || undefined,
        schedule: editForm.schedule || undefined,
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
    setPaymentForm(blankPaymentForm());
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

    setSubmitting(true);
    setError('');
    try {
      const res = await memberService.createPayment(selectedMember.id, {
        amount: Math.round(numericAmount),
        currency: paymentForm.currency || 'USD',
        payment_method: paymentForm.paymentMethod || undefined,
        status: paymentForm.status || 'completed',
        note: paymentForm.note || undefined,
      });
      setMemberPayments((prev) => [res.data.data, ...prev]);
      setPaymentForm(blankPaymentForm());
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to record payment');
    } finally {
      setSubmitting(false);
    }
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
      render: (m: Member) =>
        m.schedule ? (
          <span className="text-xs text-gray-600 whitespace-pre-line line-clamp-2">{m.schedule}</span>
        ) : (
          <span className="text-xs text-gray-400 italic">—</span>
        ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (m: Member) => (
        <div className="flex gap-2">
          <button className="p-1 hover:text-emerald-500" onClick={() => void openPaymentDrawer(m)} title="Manage payments">
            <CreditCard size={16} />
          </button>
          <button className="p-1 hover:text-primary-600" onClick={() => openEditModal(m)} title="Edit member">
            <Edit size={16} />
          </button>
          <button
            className="p-1 hover:text-red-600"
            onClick={() => {
              setDeleteConfirm(m.id);
              setIsDeleteDrawerOpen(true);
            }}
            title="Remove member"
          >
            <Trash2 size={16} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-semibold text-white">Members</h1>
        <button
          onClick={() => setIsAddDrawerOpen(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-50"
          disabled={!gymId || loading}
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
          <DataTable columns={columns} data={members} />
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
              placeholder="Currency (USD)"
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
