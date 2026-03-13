interface CardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
}

export default function Card({ title, value, icon, color = 'text-primary-600' }: CardProps) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-lg bg-gray-100 dark:bg-gray-700 ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </div>
  );
}
