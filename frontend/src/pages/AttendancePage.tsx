import { useEffect, useMemo, useState } from 'react';
import { memberService, gymService, attendanceService } from '../services/api';

type AttendanceStatus = 'present' | 'absent';

interface AttendanceRecord {
  id: number;
  member_id: number;
  attendance_date: string;
  status: AttendanceStatus;
}

interface Member {
  id: number;
  name: string;
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

export default function AttendancePage() {
  const [gymId, setGymId] = useState<number | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [records, setRecords] = useState<Array<{ member_name: string; date: string; status: AttendanceStatus }>>([]);
  const [selectedMemberId, setSelectedMemberId] = useState('');
  const [date, setDate] = useState(today());
  const [status, setStatus] = useState<AttendanceStatus>('present');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const memberMap = useMemo(() => {
    return new Map(members.map((member) => [member.id, member.name]));
  }, [members]);

  useEffect(() => {
    void loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      let resolvedGymId: number;
      const storedGymId = localStorage.getItem('active_gym_id');
      if (storedGymId && Number.isFinite(Number(storedGymId))) {
        resolvedGymId = Number(storedGymId);
      } else {
        const gymRes = await gymService.getMine();
        resolvedGymId = gymRes.data.data.id as number;
        localStorage.setItem('active_gym_id', String(resolvedGymId));
      }
      setGymId(resolvedGymId);

      const memberRes = await memberService.list(resolvedGymId);
      const nextMembers = (memberRes.data.data || []).map((member: { id: number; name: string }) => ({
        id: member.id,
        name: member.name,
      }));
      setMembers(nextMembers);
      setSelectedMemberId(nextMembers.length > 0 ? String(nextMembers[0].id) : '');

      const attendanceRes = await attendanceService.listRecords(resolvedGymId);
      const attendanceRecords = (attendanceRes.data.data || []) as AttendanceRecord[];
      setRecords(
        attendanceRecords.map((record) => ({
          member_name: nextMembers.find((member: Member) => member.id === record.member_id)?.name || `Member #${record.member_id}`,
          date: record.attendance_date,
          status: record.status,
        }))
      );
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to load attendance data');
    } finally {
      setLoading(false);
    }
  };

  const refreshRecords = async (resolvedGymId: number, map = memberMap) => {
    const attendanceRes = await attendanceService.listRecords(resolvedGymId);
    const attendanceRecords = (attendanceRes.data.data || []) as AttendanceRecord[];
    setRecords(
      attendanceRecords.map((record) => ({
        member_name: map.get(record.member_id) || `Member #${record.member_id}`,
        date: record.attendance_date,
        status: record.status,
      }))
    );
  };

  const handleRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gymId) {
      setError('Gym not found for attendance');
      return;
    }
    const parsedMemberId = Number(selectedMemberId);
    if (!parsedMemberId) {
      setError('Select a member first');
      return;
    }

    try {
      await attendanceService.createRecord({
        gym_id: gymId,
        member_id: parsedMemberId,
        attendance_date: date,
        status,
      });
      await refreshRecords(gymId);
      setError('');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to save attendance');
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-semibold text-white">Attendance</h1>
        <p className="mt-2 text-sm text-slate-400">Track member attendance and keep a clean check-in history.</p>
      </div>

      {error && <div className="mb-4 border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">{error}</div>}

      <div className="mb-6 border border-slate-800 bg-slate-900/50 p-4">
        <form className="grid grid-cols-1 gap-3 sm:grid-cols-4" onSubmit={handleRecord}>
          <select
            className="input-field"
            value={selectedMemberId}
            onChange={(e) => setSelectedMemberId(e.target.value)}
            required
          >
            {members.length === 0 ? (
              <option value="">No members</option>
            ) : (
              members.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.name}
                </option>
              ))
            )}
          </select>
          <input type="date" className="input-field" value={date} onChange={(e) => setDate(e.target.value)} required />
          <select
            className="input-field"
            value={status}
            onChange={(e) => setStatus(e.target.value as AttendanceStatus)}
          >
            <option value="present">Present</option>
            <option value="absent">Absent</option>
          </select>
          <button type="submit" className="btn-primary" disabled={loading || members.length === 0}>
            Save Attendance
          </button>
        </form>
      </div>

      <div className="border border-slate-800 bg-slate-900/40">
        <div className="grid grid-cols-3 border-b border-slate-800 bg-slate-950/60 px-4 py-3 text-xs uppercase tracking-[0.14em] text-slate-400">
          <span>Member</span>
          <span>Date</span>
          <span>Status</span>
        </div>
        {records.length === 0 ? (
          <p className="px-4 py-6 text-sm text-slate-400">No attendance records yet.</p>
        ) : (
          records.map((record, idx) => (
            <div key={`${record.member_name}-${record.date}-${idx}`} className="grid grid-cols-3 border-b border-slate-800/70 px-4 py-3 text-sm text-slate-200">
              <span>{record.member_name}</span>
              <span>{record.date}</span>
              <span className={record.status === 'present' ? 'text-emerald-300' : 'text-amber-300'}>{record.status}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
