import { Users, Phone, Bell, MessageSquare } from 'lucide-react';
import Card from '../components/Card';

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card title="Total Members" value={0} icon={<Users size={24} />} />
        <Card
          title="Active Phone Numbers"
          value={0}
          icon={<Phone size={24} />}
          color="text-green-600"
        />
        <Card
          title="Notifications Sent"
          value={0}
          icon={<Bell size={24} />}
          color="text-yellow-600"
        />
        <Card
          title="Messages (7d)"
          value={0}
          icon={<MessageSquare size={24} />}
          color="text-blue-600"
        />
      </div>
    </div>
  );
}
