import React from 'react';
import { Lock, Sparkles, ArrowRight } from 'lucide-react';
import Card from '../ui/Card';

export interface PaywallLockCardProps {
  /** Feature name to display */
  feature: string;
  /** Optional description of what the feature does */
  description?: string;
  /** Which plan is required */
  requiredPlan?: string;
  /** Current plan */
  currentPlan?: string;
  /** Called when user clicks upgrade */
  onUpgrade?: () => void;
  /** Compact mode for inline use */
  compact?: boolean;
}

export function PaywallLockCard({
  feature,
  description,
  requiredPlan = 'design-partner',
  currentPlan = 'free',
  onUpgrade,
  compact = false,
}: PaywallLockCardProps) {
  const planDisplayNames: Record<string, string> = {
    'free': 'Free',
    'design-partner': 'Design Partner',
    'growth': 'Growth',
    'enterprise': 'Enterprise',
  };

  const requiredPlanName = planDisplayNames[requiredPlan] || requiredPlan;
  const currentPlanName = planDisplayNames[currentPlan] || currentPlan;

  if (compact) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30 px-3 py-2 text-sm">
        <Lock className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />
        <span className="text-amber-800 dark:text-amber-200">
          {feature} requires {requiredPlanName} plan
        </span>
        {onUpgrade && (
          <button
            onClick={onUpgrade}
            className="ml-auto text-amber-700 dark:text-amber-300 hover:text-amber-900 dark:hover:text-amber-100 font-medium flex items-center gap-1"
          >
            Upgrade <ArrowRight className="h-3 w-3" />
          </button>
        )}
      </div>
    );
  }

  return (
    <Card className="relative overflow-hidden border-amber-200 dark:border-amber-800">
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-amber-50/50 to-orange-50/30 dark:from-amber-950/20 dark:to-orange-950/10" />

      <div className="relative p-6 flex flex-col items-center text-center gap-4">
        {/* Lock icon */}
        <div className="rounded-full bg-amber-100 dark:bg-amber-900/40 p-3">
          <Lock className="h-6 w-6 text-amber-600 dark:text-amber-400" />
        </div>

        {/* Feature name */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {feature}
          </h3>
          {description && (
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400 max-w-md">
              {description}
            </p>
          )}
        </div>

        {/* Plan badge */}
        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <span>Current plan: <strong className="text-gray-700 dark:text-gray-300">{currentPlanName}</strong></span>
          <span>·</span>
          <span>Required: <strong className="text-amber-700 dark:text-amber-300">{requiredPlanName}</strong></span>
        </div>

        {/* CTA */}
        {onUpgrade && (
          <button
            onClick={onUpgrade}
            className="mt-2 inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:from-amber-600 hover:to-orange-600 transition-all"
          >
            <Sparkles className="h-4 w-4" />
            Upgrade to {requiredPlanName}
            <ArrowRight className="h-4 w-4" />
          </button>
        )}
      </div>
    </Card>
  );
}
