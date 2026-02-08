import { Sun, Moon, Monitor } from 'lucide-react';
import { clsx } from 'clsx';
import { useTheme, type Theme } from '../../contexts/ThemeContext';

const themeOptions: { value: Theme; icon: typeof Sun; label: string }[] = [
    { value: 'light', icon: Sun, label: 'Light' },
    { value: 'system', icon: Monitor, label: 'System' },
    { value: 'dark', icon: Moon, label: 'Dark' },
];

export function ThemeToggle() {
    // Hidden: Force light mode
    return null;
}

export default ThemeToggle;
