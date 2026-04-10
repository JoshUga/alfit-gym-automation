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

const WEEK_DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function formatMonthLabel(date: Date) {
  return date.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
}

function toISODate(date: Date) {
  return date.toISOString().slice(0, 10);
}

function getMonthGrid(viewDate: Date) {
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const firstDay = new Date(year, month, 1);
  const firstWeekDay = firstDay.getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const cells: Array<{ date: string; day: number; inCurrentMonth: boolean }> = [];

  for (let i = 0; i < firstWeekDay; i += 1) {
    const d = new Date(year, month, i - firstWeekDay + 1);
    cells.push({ date: toISODate(d), day: d.getDate(), inCurrentMonth: false });
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const d = new Date(year, month, day);
    cells.push({ date: toISODate(d), day, inCurrentMonth: true });
  }

  while (cells.length % 7 !== 0) {
    const d = new Date(year, month + 1, cells.length % 7 === 0 ? 1 : cells.length - (firstWeekDay + daysInMonth) + 1);
    cells.push({ date: toISODate(d), day: d.getDate(), inCurrentMonth: false });
  }

  return cells;
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
  const [viewMonth, setViewMonth] = useState(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1);
  });
  const [selectedDate, setSelectedDate] = useState(today());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const memberMap = useMemo(() => {
    return new Map(members.map((member) => [member.id, member.name]));
  }, [members]);

  const groupedByDate = useMemo(() => {
    const map = new Map<string, Array<{ member_name: string; date: string; status: AttendanceStatus }>>();
    records.forEach((record) => {
      const bucket = map.get(record.date) || [];
      bucket.push(record);
      map.set(record.date, bucket);
    });
    return map;
  }, [records]);

  const monthCells = useMemo(() => getMonthGrid(viewMonth), [viewMonth]);
  const selectedDateRecords = useMemo(() => groupedByDate.get(selectedDate) || [], [groupedByDate, selectedDate]);

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

      <div className="border border-slate-800 bg-slate-900/40 p-4">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-white">Monthly Attendance Calendar</h2>
          <div className="flex items-center gap-2 text-sm">
            <button
              type="button"
              className="border border-slate-700 bg-slate-900 px-3 py-1 text-slate-200 hover:border-slate-500"
              onClick={() => setViewMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1))}
            >
              Prev
            </button>
            <button
              type="button"
              className="border border-slate-700 bg-slate-900 px-3 py-1 text-slate-200 hover:border-slate-500"
              onClick={() => {
                const now = new Date();
                setViewMonth(new Date(now.getFullYear(), now.getMonth(), 1));
                setSelectedDate(today());
              }}
            >
              Today
            </button>
            <button
              type="button"
              className="border border-slate-700 bg-slate-900 px-3 py-1 text-slate-200 hover:border-slate-500"
              onClick={() => setViewMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1))}
            >
              Next
            </button>
            <span className="ml-2 min-w-40 text-center font-medium text-cyan-300">{formatMonthLabel(viewMonth)}</span>
          </div>
        </div>

        <div className="mb-2 grid grid-cols-7 gap-2 text-center text-xs uppercase tracking-[0.1em] text-slate-400">
          {WEEK_DAYS.map((day) => (
            <div key={day} className="py-1">{day}</div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-2">
          {monthCells.map((cell) => {
            const dayRecords = groupedByDate.get(cell.date) || [];
            const presentCount = dayRecords.filter((r) => r.status === 'present').length;
            const absentCount = dayRecords.filter((r) => r.status === 'absent').length;
            const isSelected = selectedDate === cell.date;

            return (
              <button
                key={cell.date}
                type="button"
                onClick={() => setSelectedDate(cell.date)}
                className={`min-h-24 border p-2 text-left transition ${
                  isSelected
                    ? 'border-cyan-400 bg-cyan-500/10'
                    : cell.inCurrentMonth
                      ? 'border-slate-800 bg-slate-950/60 hover:border-slate-600'
                      : 'border-slate-900 bg-slate-950/30 text-slate-600'
                }`}
              >
                <div className="text-sm font-medium">{cell.day}</div>
                <div className="mt-2 space-y-1 text-[11px]">
                  <div className="text-emerald-300">P: {presentCount}</div>
                  <div className="text-amber-300">A: {absentCount}</div>
                </div>
              </button>
            );
          })}
        </div>

        <div className="mt-5 border border-slate-800 bg-slate-950/50 p-4">
          <p className="text-sm font-medium text-slate-200">Details for {selectedDate}</p>
          {selectedDateRecords.length === 0 ? (
            <p className="mt-2 text-sm text-slate-400">No attendance records for this date.</p>
          ) : (
            <div className="mt-3 space-y-2">
              {selectedDateRecords.map((record, idx) => (
                <div key={`${record.member_name}-${record.date}-${idx}`} className="flex items-center justify-between border border-slate-800 px-3 py-2 text-sm">
                  <span className="text-slate-200">{record.member_name}</span>
                  <span className={record.status === 'present' ? 'text-emerald-300' : 'text-amber-300'}>{record.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
