import { TrendingUp } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: string;
}

export function StatCard({ title, value, icon, trend }: StatCardProps) {
  return (
    <div className="bg-apple-surface rounded-apple-lg border border-apple-border p-4 shadow-apple">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-apple-text-secondary">{title}</p>
          <p className="text-2xl font-semibold text-apple-text mt-1">{value}</p>
        </div>
        {icon && (
          <div className="w-10 h-10 rounded-full bg-apple-blue-light flex items-center justify-center">
            {icon}
          </div>
        )}
      </div>
      {trend && (
        <div className="flex items-center gap-1 mt-2 text-xs text-green-600">
          <TrendingUp className="w-3 h-3" />
          <span>{trend}</span>
        </div>
      )}
    </div>
  );
}
