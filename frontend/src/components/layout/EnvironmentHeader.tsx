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
        type: 'warning',
        duration: 5000,
      });
    };
    window.addEventListener('resilai-readonly-action', handleReadOnly);
    return () => window.removeEventListener('resilai-readonly-action', handleReadOnly);
  }, [addToast]);

  const host = typeof window !== 'undefined' ? window.location.hostname : '';
  
  const isStaging = host === 'staging.resilai.org' || 
                    host.includes('staging') || 
                    import.meta.env.VITE_APP_ENV === 'staging' || 
                    import.meta.env.MODE === 'staging';

  const isDemo = host === 'demo.resilai.org' || 
                 host.includes('demo') || 
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
      <div className="h-[36px] bg-amber-500/10 border-b border-amber-500/50 text-amber-600 dark:text-amber-400 text-xs font-semibold flex items-center justify-center gap-2 select-none z-[60] sticky top-0 backdrop-blur-sm">
        <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 animate-pulse" />
        <span>STAGING ENVIRONMENT - GOVERNANCE SPRINT ACTIVE. DATA MAY BE FLUSHED.</span>
      </div>
    );
  }

  if (isDemo) {
    return (
      <div className="h-[36px] bg-blue-500/10 border-b border-blue-500/50 text-blue-600 dark:text-blue-400 text-xs font-semibold flex items-center justify-center gap-2 select-none z-[60] sticky top-0 backdrop-blur-sm">
        <Lock className="w-4 h-4 text-blue-500 shrink-0" />
        <span>DEMO ENVIRONMENT - LOCKED AT NIST CSF 2.0 MILESTONE.</span>
      </div>
    );
  }

  return null;
}

export default EnvironmentHeader;
