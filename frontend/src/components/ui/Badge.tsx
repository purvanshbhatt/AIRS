import { HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'ready' | 'drift' | 'critical' | 'outline' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md';
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center font-medium rounded-full';
    
    const variants = {
      default: 'bg-surface-container-high text-on-surface-variant',
      primary: 'bg-surface-bright text-on-surface',
      ready: 'bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/20',
      success: 'bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/20',
      drift: 'bg-drift-amber/10 text-drift-amber border border-drift-amber/20',
      warning: 'bg-drift-amber/10 text-drift-amber border border-drift-amber/20',
      critical: 'bg-critical-red/10 text-critical-red border border-critical-red/20',
      danger: 'bg-critical-red/10 text-critical-red border border-critical-red/20',
      outline: 'border border-outline-variant text-on-surface',
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
