import { useEffect, useMemo, useState } from 'react';
import { attendanceService, gymService, memberService } from '../services/api';
import { useThemeStore } from '../stores/themeStore';

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
  training_days?: string[];
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function dayNameFromIso(iso: string): string {
  const dayIndex = new Date(`${iso}T00:00:00Z`).getUTCDay();
  const weekDays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  return weekDays[dayIndex];
}

export default function AttendancePage() {
  const isDark = useThemeStore((state) => state.isDark);
  const [gymId, setGymId] = useState<number | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [selectedDate, setSelectedDate] = useState(today());
  const [search, setSearch] = useState('');
  const [savingMemberId, setSavingMemberId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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

      const [memberRes, attendanceRes] = await Promise.all([
        memberService.list(resolvedGymId),
        attendanceService.listRecords(resolvedGymId),
      ]);
      setMembers(memberRes.data.data || []);
      setRecords(attendanceRes.data.data || []);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to load attendance data');
    } finally {
      setLoading(false);
    }
  };

  const memberStatusMap = useMemo(() => {
    const map = new Map<number, AttendanceStatus>();
    records
      .filter((record) => record.attendance_date === selectedDate)
      .forEach((record) => map.set(record.member_id, record.status));
    return map;
  }, [records, selectedDate]);

  const visibleMembers = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return members;
    return members.filter((member) => member.name.toLowerCase().includes(query));
  }, [members, search]);

  const selectedDayName = dayNameFromIso(selectedDate);

  const stats = useMemo(() => {
    const present = visibleMembers.filter((member) => memberStatusMap.get(member.id) === 'present').length;
    const absent = visibleMembers.filter((member) => memberStatusMap.get(member.id) === 'absent').length;
    const planned = visibleMembers.filter((member) => {
      if (memberStatusMap.has(member.id)) return false;
      return (member.training_days || []).includes(selectedDayName);
    }).length;
    const notMarked = visibleMembers.length - present - absent;
    return { present, absent, planned, notMarked };
  }, [memberStatusMap, selectedDayName, visibleMembers]);

  const handleMark = async (memberId: number, status: AttendanceStatus) => {
    if (!gymId) {
      setError('Gym not found for attendance');
      return;
    }

    setSavingMemberId(memberId);
    setError('');
    try {
      await attendanceService.createRecord({
        gym_id: gymId,
        member_id: memberId,
        attendance_date: selectedDate,
        status,
      });
      const refresh = await attendanceService.listRecords(gymId);
      setRecords(refresh.data.data || []);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Unable to save attendance');
    } finally {
      setSavingMemberId(null);
    }
  };

  const cardClass = isDark ? 'border-slate-800 bg-slate-900/55 text-slate-100' : 'border-slate-200 bg-white text-slate-900';

  return (
    <div className="space-y-6">
      <div>
        <h1 className={`text-3xl font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Attendance</h1>
        <p className={`mt-2 text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
          Daily operations view. Pick a date and review or mark attendance for all members in one place.
        </p>
      </div>

      {error && <div className={`rounded-xl border p-3 text-sm ${isDark ? 'border-red-500/40 bg-red-500/10 text-red-200' : 'border-red-300 bg-red-50 text-red-700'}`}>{error}</div>}

      <div className={`grid grid-cols-1 gap-3 rounded-2xl border p-4 md:grid-cols-[220px_1fr] ${cardClass}`}>
        <input
          type="date"
          className="input-field"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
        />
        <input
          type="text"
          className="input-field"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search member by name"
        />
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className={`rounded-xl border p-3 ${cardClass}`}><p className="text-xs opacity-70">Present</p><p className="text-2xl font-semibold">{stats.present}</p></div>
        <div className={`rounded-xl border p-3 ${cardClass}`}><p className="text-xs opacity-70">Absent</p><p className="text-2xl font-semibold">{stats.absent}</p></div>
        <div className={`rounded-xl border p-3 ${cardClass}`}><p className="text-xs opacity-70">Planned</p><p className="text-2xl font-semibold">{stats.planned}</p></div>
        <div className={`rounded-xl border p-3 ${cardClass}`}><p className="text-xs opacity-70">Not Marked</p><p className="text-2xl font-semibold">{stats.notMarked}</p></div>
      </div>

      <div className={`rounded-2xl border ${cardClass}`}>
        <div className={`grid grid-cols-[1fr_auto_auto_auto] gap-2 border-b px-4 py-3 text-xs uppercase tracking-[0.14em] ${isDark ? 'border-slate-800 text-slate-400' : 'border-slate-200 text-slate-500'}`}>
          <span>Member</span>
          <span>Status</span>
          <span className="text-center">Present</span>
          <span className="text-center">Absent</span>
        </div>
        <div className="divide-y divide-slate-200/20">
          {loading ? (
            <p className={`p-4 text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Loading attendance...</p>
          ) : visibleMembers.length === 0 ? (
            <p className={`p-4 text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>No matching members.</p>
          ) : (
            visibleMembers.map((member) => {
              const status = memberStatusMap.get(member.id);
              const planned = (member.training_days || []).includes(selectedDayName);
              const saving = savingMemberId === member.id;

              return (
                <div key={member.id} className="grid grid-cols-[1fr_auto_auto_auto] items-center gap-2 px-4 py-3">
                  <div>
                    <p className={`text-sm font-medium ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>{member.name}</p>
                    <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-500'}`}>
                      Planned day: {planned ? 'Yes' : 'No'}
                    </p>
                  </div>
                  <span className={`rounded-full px-2 py-1 text-xs ${
                    status === 'present'
                      ? isDark ? 'bg-emerald-500/15 text-emerald-300' : 'bg-emerald-100 text-emerald-700'
                      : status === 'absent'
                        ? isDark ? 'bg-amber-500/15 text-amber-300' : 'bg-amber-100 text-amber-700'
                        : isDark ? 'bg-slate-800 text-slate-400' : 'bg-slate-100 text-slate-600'
                  }`}>
                    {status || 'not marked'}
                  </span>
                  <button type="button" aria-label={`Mark ${member.name} as present`} className="btn-secondary text-xs" disabled={saving} onClick={() => void handleMark(member.id, 'present')}>Present</button>
                  <button type="button" aria-label={`Mark ${member.name} as absent`} className="btn-secondary text-xs" disabled={saving} onClick={() => void handleMark(member.id, 'absent')}>Absent</button>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
