import { cn } from '../utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export function Card({ children, padding = 'md', className, ...props }: CardProps) {
  const paddings = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  return (
    <div
      className={cn(
        'bg-apple-surface rounded-apple-lg border border-apple-border shadow-apple',
        paddings[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
