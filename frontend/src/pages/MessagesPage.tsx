import { MessageSquare } from 'lucide-react';
import DataTable from '../components/DataTable';

export default function MessagesPage() {
  const columns = [
    { key: 'sender', label: 'Sender' },
    { key: 'recipient', label: 'Recipient' },
    { key: 'content', label: 'Message' },
    { key: 'message_type', label: 'Type' },
    { key: 'created_at', label: 'Date' },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <MessageSquare size={24} />
        Message History
      </h1>
      <div className="card">
        <DataTable columns={columns} data={[]} />
      </div>
    </div>
  );
}
