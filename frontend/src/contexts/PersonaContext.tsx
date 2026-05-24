import { createContext, useContext, useState, ReactNode, useMemo } from 'react';

export type Persona = 'EXECUTIVE' | 'FORENSIC';

interface PersonaContextValue {
  persona: Persona;
  setPersona: (persona: Persona) => void;
}

const PersonaContext = createContext<PersonaContextValue | null>(null);

interface PersonaProviderProps {
  children: ReactNode;
}

export function PersonaProvider({ children }: PersonaProviderProps) {
  const [persona, setPersonaInternal] = useState<Persona>(() => {
    try {
      const saved = localStorage.getItem('resilai-dashboard-persona');
      return (saved as Persona) === 'FORENSIC' ? 'FORENSIC' : 'EXECUTIVE';
    } catch {
      return 'EXECUTIVE';
    }
  });

  const setPersona = (newPersona: Persona) => {
    setPersonaInternal(newPersona);
    try {
      localStorage.setItem('resilai-dashboard-persona', newPersona);
    } catch (e) {
      console.warn('[PersonaContext] Failed to persist view preference:', e);
    }
  };

  const value = useMemo(() => ({
    persona,
    setPersona,
  }), [persona]);

  return (
    <PersonaContext.Provider value={value}>
      {children}
    </PersonaContext.Provider>
  );
}

export function usePersona(): PersonaContextValue {
  const context = useContext(PersonaContext);
  if (!context) {
    throw new Error('usePersona must be used within a PersonaProvider');
  }
  return context;
}
