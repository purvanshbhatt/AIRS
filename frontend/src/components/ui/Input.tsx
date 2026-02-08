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
    
    const baseStyles = 'block w-full rounded-lg border px-3 py-2 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0 bg-white text-gray-900  ';
    
    const stateStyles = error
      ? 'border-danger-500 focus:border-danger-500 focus:ring-danger-500/20'
      : 'border-gray-300 focus:border-primary-500 focus:ring-primary-500/20';

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-gray-900  mb-1.5">
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
          <p className="mt-1.5 text-sm text-danger-600">{error}</p>
        )}
        {hint && !error && (
          <p className="mt-1.5 text-sm text-gray-900 ">{hint}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
