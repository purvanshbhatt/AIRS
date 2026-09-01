import { ButtonHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'verified' | 'at-risk' | 'unable-to-verify';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, disabled, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-surface-bright active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100';
    
    const variants = {
      primary: 'bg-surface-bright text-on-surface hover:brightness-110 border border-surface-bright/50',
      secondary: 'bg-surface-container-high text-on-surface-variant hover:bg-surface-bright border border-transparent',
      outline: 'bg-transparent border border-outline text-on-surface hover:bg-surface-container-lowest',
      ghost: 'bg-transparent text-on-surface-variant hover:bg-surface-container-low border border-transparent',
      danger: 'bg-critical-red text-white hover:brightness-110 focus:ring-critical-red',
      verified: 'bg-ready-emerald text-surface-container-lowest hover:brightness-110 focus:ring-ready-emerald',
      'at-risk': 'bg-drift-amber text-surface-container-lowest hover:brightness-110 focus:ring-drift-amber',
      'unable-to-verify': 'bg-surface-container-high text-drift-amber hover:bg-surface-bright border border-drift-amber/30',
    };

    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-sm',
      lg: 'px-6 py-3 text-base',
    };

    return (
      <button
        ref={ref}
        className={clsx(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
