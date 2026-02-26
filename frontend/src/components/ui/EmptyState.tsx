import { ReactNode } from 'react';
import { LucideIcon, Inbox, ArrowRight } from 'lucide-react';
import Button from './Button';

interface EmptyStateAction {
  label: string;
  href?: string;
  onClick?: () => void;
}

interface BlueprintStep {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: EmptyStateAction;
}

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: EmptyStateAction;
  /** Onboarding Blueprint steps — shown as a guided flow instead of a plain message */
  steps?: BlueprintStep[];
  children?: ReactNode;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  steps,
  children,
}: EmptyStateProps) {
  /* ── Blueprint variant ── */
  if (steps && steps.length > 0) {
    return (
      <div className="py-10 px-4 animate-fade-up">
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-14 h-14 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mb-3">
            <Icon className="w-7 h-7 text-primary-600 dark:text-primary-400" />
          </div>
          <h3 className="text-headline text-gray-900 dark:text-slate-100">{title}</h3>
          {description && (
            <p className="text-body text-gray-500 dark:text-slate-400 max-w-md mt-1">{description}</p>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-3xl mx-auto">
          {steps.map((step, idx) => {
            const StepIcon = step.icon;
            return (
              <div
                key={idx}
                className="relative flex flex-col items-center text-center p-6 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 hover:border-primary-300 dark:hover:border-primary-700 transition-colors"
              >
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary-500 text-white text-overline px-2.5 py-0.5 rounded-full">
                  Step {idx + 1}
                </span>
                <StepIcon className="w-8 h-8 text-primary-500 mb-3 mt-2" />
                <h4 className="text-title text-gray-900 dark:text-slate-100 mb-1">{step.title}</h4>
                <p className="text-body text-gray-500 dark:text-slate-400 mb-3">{step.description}</p>
                {step.action && (
                  step.action.href ? (
                    <a href={step.action.href} className="mt-auto">
                      <Button size="sm" variant="outline" className="gap-1">
                        {step.action.label} <ArrowRight className="w-3 h-3" />
                      </Button>
                    </a>
                  ) : (
                    <Button size="sm" variant="outline" className="gap-1 mt-auto" onClick={step.action.onClick}>
                      {step.action.label} <ArrowRight className="w-3 h-3" />
                    </Button>
                  )
                )}
              </div>
            );
          })}
        </div>

        {action && (
          <div className="flex justify-center mt-8">
            {action.href ? (
              <a href={action.href}><Button>{action.label}</Button></a>
            ) : (
              <Button onClick={action.onClick}>{action.label}</Button>
            )}
          </div>
        )}
        {children}
      </div>
    );
  }

  /* ── Classic variant ── */
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center animate-fade-up">
      <div className="w-16 h-16 bg-gray-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-gray-400 dark:text-slate-500" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-gray-500 dark:text-slate-400 max-w-sm mb-4">{description}</p>
      )}
      {action && (
        action.href ? (
          <a href={action.href}>
            <Button>{action.label}</Button>
          </a>
        ) : (
          <Button onClick={action.onClick}>{action.label}</Button>
        )
      )}
      {children}
    </div>
  );
}
