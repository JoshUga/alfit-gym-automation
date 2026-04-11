import { useEffect, useMemo, useState } from 'react';
import { authService, gymService, memberService } from '../services/api';
import { useAuthStore } from '../stores/authStore';

interface Trainer {
  id: number;
  full_name?: string | null;
  email: string;
}

interface Member {
  id: number;
  name: string;
}

interface TrainerAssignment {
  id: number;
  member_id: number;
  trainer_user_id: number;
}

export default function StaffPage() {
  const user = useAuthStore((state) => state.user);
  const [gymId, setGymId] = useState<number | null>(null);
  const [trainers, setTrainers] = useState<Trainer[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [assignments, setAssignments] = useState<TrainerAssignment[]>([]);
  const [trainerForm, setTrainerForm] = useState({ fullName: '', email: '', password: '' });
  const [assignmentDrafts, setAssignmentDrafts] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const assignmentByMember = useMemo(() => {
    const map = new Map<number, TrainerAssignment>();
    assignments.forEach((assignment) => map.set(assignment.member_id, assignment));
    return map;
  }, [assignments]);

  useEffect(() => {
    void loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const gymRes = await gymService.getMine();
      const resolvedGymId = gymRes.data.data.id as number;
      setGymId(resolvedGymId);

      const [trainersRes, membersRes, assignmentsRes] = await Promise.all([
        authService.listTrainers(),
        memberService.list(resolvedGymId),
        memberService.listTrainerAssignments(resolvedGymId),
      ]);
      setTrainers(trainersRes.data.data || []);
      setMembers((membersRes.data.data || []).map((m: Member) => ({ id: m.id, name: m.name })));
      setAssignments(assignmentsRes.data.data || []);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to load staff settings');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTrainer = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      await authService.createTrainer({
        full_name: trainerForm.fullName || undefined,
        email: trainerForm.email,
        password: trainerForm.password,
      });
      setTrainerForm({ fullName: '', email: '', password: '' });
      setSuccess('Trainer account created.');
      await loadData();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to create trainer');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveAssignment = async (memberId: number) => {
    const nextTrainerId = Number(assignmentDrafts[memberId] ?? '');
    const current = assignmentByMember.get(memberId);
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      if (current && (!nextTrainerId || nextTrainerId !== current.trainer_user_id)) {
        await memberService.removeTrainer(memberId, current.trainer_user_id);
      }
      if (nextTrainerId && (!current || current.trainer_user_id !== nextTrainerId)) {
        await memberService.assignTrainer(memberId, nextTrainerId);
      }
      setSuccess('Trainer assignment updated.');
      await loadData();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to update assignment');
    } finally {
      setSubmitting(false);
    }
  };

  if (user?.role !== 'gym_owner') {
    return (
      <div>
        <h1 className="mb-4 text-3xl font-semibold text-white">Staff</h1>
        <p className="text-sm text-slate-400">Only gym owners can manage trainers.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-white">Staff</h1>
        <p className="mt-2 text-sm text-slate-400">Create trainer accounts and assign trainers to members.</p>
      </div>
      {error && <div className="rounded-xl border border-red-500/35 bg-red-500/10 p-3 text-sm text-red-200">{error}</div>}
      {success && <div className="rounded-xl border border-emerald-500/35 bg-emerald-500/10 p-3 text-sm text-emerald-200">{success}</div>}

      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
        <h2 className="mb-4 text-lg font-semibold text-slate-100">Add Trainer</h2>
        <form className="grid grid-cols-1 gap-3 md:grid-cols-4" onSubmit={handleCreateTrainer}>
          <input
            className="input-field"
            placeholder="Full name"
            value={trainerForm.fullName}
            onChange={(e) => setTrainerForm((prev) => ({ ...prev, fullName: e.target.value }))}
          />
          <input
            className="input-field"
            type="email"
            required
            placeholder="trainer@gym.com"
            value={trainerForm.email}
            onChange={(e) => setTrainerForm((prev) => ({ ...prev, email: e.target.value }))}
          />
          <input
            className="input-field"
            type="password"
            required
            minLength={8}
            placeholder="Temporary password"
            value={trainerForm.password}
            onChange={(e) => setTrainerForm((prev) => ({ ...prev, password: e.target.value }))}
          />
          <button type="submit" className="btn-primary" disabled={submitting || loading}>
            {submitting ? 'Saving...' : 'Create Trainer'}
          </button>
        </form>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
        <h2 className="mb-4 text-lg font-semibold text-slate-100">Trainers</h2>
        {loading ? (
          <p className="text-sm text-slate-400">Loading trainers...</p>
        ) : trainers.length === 0 ? (
          <p className="text-sm text-slate-400">No trainers created yet.</p>
        ) : (
          <div className="space-y-2">
            {trainers.map((trainer) => (
              <div key={trainer.id} className="rounded-lg border border-slate-800 px-3 py-2 text-sm text-slate-200">
                {trainer.full_name || 'Unnamed trainer'} · {trainer.email}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
        <h2 className="mb-4 text-lg font-semibold text-slate-100">Assign Trainers to Members</h2>
        {!gymId || loading ? (
          <p className="text-sm text-slate-400">Loading members...</p>
        ) : members.length === 0 ? (
          <p className="text-sm text-slate-400">No members found.</p>
        ) : (
          <div className="space-y-3">
            {members.map((member) => {
              const current = assignmentByMember.get(member.id);
              const draftValue = assignmentDrafts[member.id] ?? String(current?.trainer_user_id ?? '');
              return (
                <div key={member.id} className="grid grid-cols-1 gap-2 rounded-lg border border-slate-800 p-3 md:grid-cols-[1fr_280px_auto]">
                  <div className="text-sm text-slate-200">{member.name}</div>
                  <select
                    className="input-field"
                    value={draftValue}
                    onChange={(e) => setAssignmentDrafts((prev) => ({ ...prev, [member.id]: e.target.value }))}
                  >
                    <option value="">Unassigned</option>
                    {trainers.map((trainer) => (
                      <option key={trainer.id} value={trainer.id}>
                        {trainer.full_name || trainer.email}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => void handleSaveAssignment(member.id)}
                    disabled={submitting}
                  >
                    Save
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
