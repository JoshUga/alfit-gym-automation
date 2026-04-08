export type AttendanceStatus = 'present' | 'absent';

export interface AttendanceRecord {
  gymId: number;
  memberId: number;
  date: string;
  status: AttendanceStatus;
  createdAt: string;
}

const STORAGE_KEY = 'attendance_records_v1';

function readAllRecords(): AttendanceRecord[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as AttendanceRecord[]) : [];
  } catch {
    return [];
  }
}

function writeAllRecords(records: AttendanceRecord[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
}

export function addAttendanceRecord(
  gymId: number,
  memberId: number,
  date: string,
  status: AttendanceStatus
): AttendanceRecord {
  const records = readAllRecords().filter(
    (record) => !(record.gymId === gymId && record.memberId === memberId && record.date === date)
  );
  const next: AttendanceRecord = {
    gymId,
    memberId,
    date,
    status,
    createdAt: new Date().toISOString(),
  };
  records.push(next);
  writeAllRecords(records);
  return next;
}

export function listAttendanceRecords(gymId: number): AttendanceRecord[] {
  return readAllRecords()
    .filter((record) => record.gymId === gymId)
    .sort((a, b) => (a.date < b.date ? 1 : -1));
}

export function listMemberAttendance(gymId: number, memberId: number): AttendanceRecord[] {
  return listAttendanceRecords(gymId).filter((record) => record.memberId === memberId);
}

export function getMemberAttendanceSummary(gymId: number, memberId: number) {
  const records = listMemberAttendance(gymId, memberId);
  const present = records.filter((record) => record.status === 'present').length;
  const absent = records.filter((record) => record.status === 'absent').length;
  const total = records.length;
  const rate = total > 0 ? Math.round((present / total) * 100) : 0;
  return { total, present, absent, rate };
}
