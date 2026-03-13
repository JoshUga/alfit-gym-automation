import { useState } from 'react';
import { UserPlus, Edit, Trash2 } from 'lucide-react';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';

interface Member {
  id: number;
  name: string;
  email: string;
  phone_number: string;
  status: string;
  [key: string]: unknown;
}

export default function MembersPage() {
  const [members] = useState<Member[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

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
      key: 'actions',
      label: 'Actions',
      render: () => (
        <div className="flex gap-2">
          <button className="p-1 hover:text-primary-600">
            <Edit size={16} />
          </button>
          <button className="p-1 hover:text-red-600">
            <Trash2 size={16} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Members</h1>
        <button onClick={() => setIsModalOpen(true)} className="btn-primary flex items-center gap-2">
          <UserPlus size={18} />
          Add Member
        </button>
      </div>
      <div className="card">
        <DataTable columns={columns} data={members} />
      </div>
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Add Member">
        <form className="space-y-4">
          <input type="text" placeholder="Name" className="input-field" required />
          <input type="email" placeholder="Email" className="input-field" />
          <input type="tel" placeholder="Phone Number" className="input-field" required />
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={() => setIsModalOpen(false)} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Add Member
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
