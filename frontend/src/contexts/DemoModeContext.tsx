import { createContext, useContext, useEffect, useState, ReactNode, useMemo } from 'react';
import { getSystemStatus } from '../api';
import type { SystemStatus } from '../types';

interface DemoModeContextValue {
  /** Whether the backend is in demo mode */
  isDemoMode: boolean;
  /** Whether writes are disabled (demo mode = read-only) */
  isReadOnly: boolean;
  /** Full system status from backend */
  systemStatus: SystemStatus | null;
  /** Whether the context is still loading */
  isLoading: boolean;
  /** Force refresh the system status */
  refresh: () => Promise<void>;
}

const DemoModeContext = createContext<DemoModeContextValue | null>(null);

interface DemoModeProviderProps {
  children: ReactNode;
}

export function DemoModeProvider({ children }: DemoModeProviderProps) {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const status = await getSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.warn('[DemoMode] Failed to fetch system status:', error);
      // Default to non-demo mode on error
      setSystemStatus(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const value = useMemo<DemoModeContextValue>(() => ({
    isDemoMode: systemStatus?.demo_mode ?? false,
    isReadOnly: systemStatus?.is_read_only ?? false,
    systemStatus,
    isLoading,
    refresh: fetchStatus,
  }), [systemStatus, isLoading]);

  return (
    <DemoModeContext.Provider value={value}>
      {children}
    </DemoModeContext.Provider>
  );
}

export function useDemoMode(): DemoModeContextValue {
  const context = useContext(DemoModeContext);
  if (!context) {
    throw new Error('useDemoMode must be used within a DemoModeProvider');
  }
  return context;
}

/**
 * Hook that returns true if the app is in read-only mode (demo environment).
 * Use this to conditionally hide create/edit/delete buttons.
 */
export function useIsReadOnly(): boolean {
  const { isReadOnly } = useDemoMode();
  return isReadOnly;
}
