import React from 'react';
import { Check, ShieldCheck, Zap, Server, Activity } from 'lucide-react';
import { cn } from '../../lib/utils';
import { tokens } from '../../lib/design-tokens';

interface JourneyStep {
  id: string;
  time: string;
  title: string;
  verified: boolean;
  icon: React.ElementType;
}

export function ReadinessJourney() {
  // Mock data for the journey
  const steps: JourneyStep[] = [
    { id: '1', time: '01:15 AM', title: 'Network Firewall Healthy', verified: true, icon: ShieldCheck },
    { id: '2', time: '02:30 AM', title: 'M365 Email Sync Completed', verified: true, icon: Activity },
    { id: '3', time: '04:00 AM', title: 'EHR Cloud Backup Verified', verified: true, icon: Server },
    { id: '4', time: '05:45 AM', title: 'Endpoint Security Active', verified: true, icon: ShieldCheck },
    { id: '5', time: '07:15 AM', title: 'Morning Connectivity Test Passed', verified: true, icon: Zap },
  ];

  return (
    <div className={cn(tokens.surface.base, "p-8 max-w-lg mx-auto")}>
      <h3 className="text-sm font-bold tracking-wider text-slate-400 uppercase mb-8">Overnight Journey</h3>
      
      <div className="space-y-6 relative">
        {/* Timeline Line */}
        <div className="absolute top-4 bottom-4 left-3 w-0.5 bg-slate-100 dark:bg-slate-800" />
        
        {steps.map((step, idx) => (
          <div key={step.id} className="relative flex items-center gap-4 group">
            <div className="relative z-10 w-6 h-6 rounded-full bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 ring-4 ring-white dark:ring-slate-900 transition-transform group-hover:scale-110">
              <Check className="w-3.5 h-3.5 stroke-[3]" />
            </div>
            
            <div className="flex-1 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <step.icon className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                <span className={cn(tokens.typography.body, "font-medium")}>
                  {step.title}
                </span>
              </div>
              <span className={cn(tokens.typography.small, "font-mono opacity-60")}>
                {step.time}
              </span>
            </div>
          </div>
        ))}

        {/* Final State */}
        <div className="relative flex items-center gap-4 mt-8 pt-6 border-t border-slate-100 dark:border-slate-800">
          <div className="relative z-10 w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center shrink-0 ring-4 ring-white dark:ring-slate-900">
            <SparklesIcon className="w-3.5 h-3.5" />
          </div>
          <div className="flex-1">
            <h4 className={cn(tokens.typography.cardTitle, "text-indigo-900 dark:text-indigo-300")}>
              Ready for Patients
            </h4>
          </div>
        </div>
      </div>
    </div>
  );
}

function SparklesIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
      <path d="M5 3v4"/>
      <path d="M19 17v4"/>
      <path d="M3 5h4"/>
      <path d="M17 19h4"/>
    </svg>
  );
}
