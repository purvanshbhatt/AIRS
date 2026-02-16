import { HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'outline';
  size?: 'sm' | 'md';
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center font-medium rounded-full';
    
    const variants = {
      default: 'bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200',
      primary: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300',
      success: 'bg-success-50 text-success-600 dark:bg-success-900/30 dark:text-success-300',
      warning: 'bg-warning-50 text-warning-600 dark:bg-warning-900/30 dark:text-warning-300',
      danger: 'bg-danger-50 text-danger-600 dark:bg-danger-900/30 dark:text-danger-300',
      outline: 'border border-gray-300 text-gray-700 dark:border-slate-700 dark:text-slate-200',
    };

    const sizes = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-1 text-xs',
    };

    return (
      <span
        ref={ref}
        className={clsx(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

export default Badge;
