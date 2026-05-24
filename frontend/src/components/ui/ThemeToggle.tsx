import { Sun, Moon, Monitor } from 'lucide-react';
import { clsx } from 'clsx';
import { useTheme, type Theme } from '../../contexts/ThemeContext';

const themeOptions: { value: Theme; icon: typeof Sun; label: string }[] = [
    { value: 'light', icon: Sun, label: 'Light' },
    { value: 'system', icon: Monitor, label: 'System' },
    { value: 'dark', icon: Moon, label: 'Dark' },
];

export function ThemeToggle() {
    const { theme, setTheme } = useTheme();

    return (
        <div className="inline-flex items-center gap-1 rounded-lg bg-slate-100 dark:bg-slate-800 p-1">
            {themeOptions.map(({ value, icon: Icon, label }) => (
                <button
                    key={value}
                    type="button"
                    onClick={() => setTheme(value)}
                    className={clsx(
                        'p-1.5 rounded-md transition-colors',
                        theme === value
                            ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm'
                            : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                    )}
                    title={label}
                    aria-label={`Switch to ${label} theme`}
                >
                    <Icon className="h-4 w-4" />
                </button>
            ))}
        </div>
    );
}

export default ThemeToggle;
