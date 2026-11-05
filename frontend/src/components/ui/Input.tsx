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
    
    const baseStyles = 'block w-full rounded-md border bg-surface-container text-on-surface placeholder:text-on-surface-variant caret-on-surface px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0';
    
    const stateStyles = error
      ? 'border-critical-red focus:border-critical-red focus:ring-critical-red/20'
      : 'border-outline-variant focus:border-surface-bright focus:ring-surface-bright/20';

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-on-surface mb-1.5">
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
          <p className="mt-1.5 text-sm text-critical-red">{error}</p>
        )}
        {hint && !error && (
          <p className="mt-1.5 text-sm text-on-surface-variant">{hint}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
