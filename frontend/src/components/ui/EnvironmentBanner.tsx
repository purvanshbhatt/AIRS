import { useEffect } from 'react';
import { AlertTriangle, Lock } from 'lucide-react';
import { useToast } from './Toast';

export function EnvironmentBanner() {
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

  if (isStaging) {
    return (
      <div className="bg-amber-600 text-white py-2.5 px-4 text-center text-xs font-bold flex items-center justify-center gap-2 shadow-md border-b border-amber-700 select-none z-55 sticky top-0">
        <AlertTriangle className="w-4 h-4 text-white shrink-0 animate-bounce" />
        <span>STAGING ENVIRONMENT - Active Development Branch.</span>
      </div>
    );
  }

  if (isDemo) {
    return (
      <div className="bg-indigo-600 text-white py-2.5 px-4 text-center text-xs font-bold flex items-center justify-center gap-2 shadow-md border-b border-indigo-700 select-none z-55 sticky top-0">
        <Lock className="w-4 h-4 text-white shrink-0" />
        <span>INTERACTIVE DEMO - System Data is Simulated.</span>
      </div>
    );
  }

  return null;
}

export default EnvironmentBanner;
