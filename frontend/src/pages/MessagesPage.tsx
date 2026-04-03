import { MessageSquare } from 'lucide-react';
import DataTable from '../components/DataTable';
import { useThemeStore } from '../stores/themeStore';

export default function MessagesPage() {
  const isDark = useThemeStore((state) => state.isDark);

  const columns = [
    { key: 'sender', label: 'Sender' },
    { key: 'recipient', label: 'Recipient' },
    { key: 'content', label: 'Message' },
    { key: 'message_type', label: 'Type' },
    { key: 'created_at', label: 'Date' },
  ];

  return (
    <div>
      <h1 className={`mb-6 flex items-center gap-2 text-3xl font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>
        <MessageSquare size={24} />
        Message History
      </h1>
      <div>
        <DataTable columns={columns} data={[]} />
      </div>
    </div>
  );
}
