import { Bell, CalendarPlus } from 'lucide-react';

export default function NotificationsPage() {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Notifications</h1>
        <button className="btn-primary flex items-center gap-2">
          <CalendarPlus size={18} />
          Schedule Notification
        </button>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Bell size={20} />
            Upcoming Notifications
          </h2>
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">
            No scheduled notifications
          </p>
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Templates</h2>
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">
            No templates created yet
          </p>
        </div>
      </div>
    </div>
  );
}
