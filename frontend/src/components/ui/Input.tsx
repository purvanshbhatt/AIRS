import { InputHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    
    const baseStyles = 'block w-full rounded-lg border bg-white text-gray-900 placeholder:text-gray-400 caret-gray-900 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:caret-slate-100 px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0';
    
    const stateStyles = error
      ? 'border-danger-500 focus:border-danger-500 focus:ring-danger-500/20'
      : 'border-gray-300 dark:border-slate-700 focus:border-primary-500 focus:ring-primary-500/20';

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-1.5">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(baseStyles, stateStyles, className)}
          {...props}
        />
        {error && (
          <p className="mt-1.5 text-sm text-danger-600 dark:text-danger-400">{error}</p>
        )}
        {hint && !error && (
          <p className="mt-1.5 text-sm text-gray-500 dark:text-slate-400">{hint}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
