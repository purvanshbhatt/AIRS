import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

type Theme = 'light' | 'dark' | 'system';
type ResolvedTheme = 'light' | 'dark';

interface ThemeContextValue {
    theme: Theme;
    setTheme: (theme: Theme) => void;
    resolvedTheme: ResolvedTheme;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = 'ResilAI-theme';

function getSystemTheme(): ResolvedTheme {
    if (typeof window === 'undefined') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function getStoredTheme(): Theme {
    if (typeof window === 'undefined') return 'system';
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
        return stored;
    }
    return 'system';
}

interface ThemeProviderProps {
    children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
    // FORCE LIGHT MODE
    const theme: Theme = 'light';
    const resolvedTheme: ResolvedTheme = 'light';
    
    // Disable theme switching
    const setTheme = (newTheme: Theme) => {
        console.log('Theme switching is disabled. Requested:', newTheme);
    };

    // Ensure dark class is removed
    useEffect(() => {
        document.documentElement.classList.remove('dark');
    }, []);

    return (
        <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}

export { ThemeContext };
export type { Theme, ResolvedTheme };

