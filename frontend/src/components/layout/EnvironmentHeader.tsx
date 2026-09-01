import { useEffect } from 'react';
import { AlertTriangle, Lock } from 'lucide-react';
import { useToast } from '../ui/Toast';

export function EnvironmentHeader() {
  const { addToast } = useToast();
  
  useEffect(() => {
    const handleReadOnly = (e: Event) => {
      const customEvent = e as CustomEvent<{ message: string }>;
      addToast({
        title: 'Read-Only Demo',
        message: customEvent.detail?.message || 'Changes cannot be saved in the interactive demo.',
        type: "drift",
        duration: 5000,
      });
    };
    window.addEventListener('resilai-readonly-action', handleReadOnly);
    return () => window.removeEventListener('resilai-readonly-action', handleReadOnly);
  }, [addToast]);

  const host = typeof window !== 'undefined' ? window.location.hostname : '';
  const search = typeof window !== 'undefined' ? window.location.search : '';
  
  const isStaging = host === 'staging.resilai.org' || 
                    host.includes('staging') || 
                    search.includes('env=staging') ||
                    import.meta.env.VITE_APP_ENV === 'staging' || 
                    import.meta.env.MODE === 'staging';

  const isDemo = host === 'demo.resilai.org' || 
                 host.includes('demo') || 
                 search.includes('env=demo') ||
                 import.meta.env.VITE_APP_ENV === 'demo' || 
                 import.meta.env.MODE === 'demo';

  // Control top-level viewport offsets dynamically when banners are visible
  useEffect(() => {
    if (isStaging || isDemo) {
      document.documentElement.style.setProperty('--banner-height', '36px');
    } else {
      document.documentElement.style.setProperty('--banner-height', '0px');
    }
    return () => {
      document.documentElement.style.setProperty('--banner-height', '0px');
    };
  }, [isStaging, isDemo]);

  if (isStaging) {
    return (
      <div className="h-[36px] overflow-hidden bg-amber-100 dark:bg-amber-950 border-b border-amber-300 dark:border-amber-900/60 text-amber-800 dark:text-amber-200 text-xs font-semibold flex items-center justify-center gap-2 select-none z-[60] sticky top-0 shadow-sm">
        <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 animate-pulse" />
        <span className="truncate px-2">
          <span className="md:hidden">STAGING ACTIVE</span>
          <span className="hidden md:inline">STAGING ENVIRONMENT - GOVERNANCE SPRINT ACTIVE. DATA MAY BE FLUSHED.</span>
        </span>
      </div>
    );
  }

  if (isDemo) {
    return (
      <div className="h-[36px] overflow-hidden bg-blue-100 dark:bg-blue-950 border-b border-blue-300 dark:border-blue-900/60 text-blue-800 dark:text-blue-200 text-xs font-semibold flex items-center justify-center gap-2 select-none z-[60] sticky top-0 shadow-sm">
        <Lock className="w-4 h-4 text-blue-500 shrink-0" />
        <span className="truncate px-2">
          <span className="md:hidden">DEMO - NIST CSF 2.0</span>
          <span className="hidden md:inline">DEMO ENVIRONMENT - LOCKED AT NIST CSF 2.0 MILESTONE.</span>
        </span>
      </div>
    );
  }

  return null;
}

export default EnvironmentHeader;
