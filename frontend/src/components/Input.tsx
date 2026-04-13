import { cn } from '../utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className, ...props }: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-apple-text mb-1.5">
          {label}
        </label>
      )}
      <input
        className={cn(
          'w-full px-4 py-2 bg-apple-surface border border-apple-border rounded-apple',
          'focus:outline-none focus:ring-2 focus:ring-apple-blue focus:border-transparent',
          'placeholder:text-apple-text-secondary',
          'transition-all duration-200',
          error && 'border-red-500 focus:ring-red-500',
          className
        )}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
    </div>
  );
}
