import { useEffect, useState } from 'react';

/**
 * Per-browser display preferences.
 *
 * These are choices about how ResilAI looks and opens on THIS device. They
 * are stored in the browser only: nothing here changes the organisation's
 * data, its score, or what other people on the team see.
 */
export type StartPage = '/morning-brief' | '/needs-attention' | '/operations' | '/network' | '/reports';
export type MapViewPreference = 'auto' | '3d' | '2d';

export interface Preferences {
  /** Page opened after sign-in. */
  startPage: StartPage;
  /** Network Map: `auto` opens 3D on wide screens and 2D on phones. */
  mapView: MapViewPreference;
  /** Network Map: re-read connected systems every 45 seconds while open. */
  mapLiveRefresh: boolean;
  /** Stop decorative animation (pulsing, sliding, auto-rotation). */
  reduceMotion: boolean;
}

export const DEFAULT_PREFERENCES: Preferences = {
  startPage: '/morning-brief',
  mapView: 'auto',
  mapLiveRefresh: true,
  reduceMotion: false,
};

export const START_PAGE_OPTIONS: Array<{ value: StartPage; label: string; hint: string }> = [
  { value: '/morning-brief', label: 'Today', hint: 'The morning brief: are we ready today?' },
  { value: '/needs-attention', label: 'Needs Attention', hint: 'The list of things to fix.' },
  { value: '/operations', label: 'Operations Center', hint: 'The technical overview.' },
  { value: '/network', label: 'Network Map', hint: 'Devices, networks and VPN links.' },
  { value: '/reports', label: 'Reports', hint: 'Generate and download reports.' },
];

const STORAGE_KEY = 'resilai_preferences_v1';
const CHANGE_EVENT = 'resilai:preferences';

function sanitize(raw: unknown): Preferences {
  const input = (raw && typeof raw === 'object' ? raw : {}) as Partial<Record<keyof Preferences, unknown>>;
  const startPages = START_PAGE_OPTIONS.map((o) => o.value);
  return {
    startPage: startPages.includes(input.startPage as StartPage) ? (input.startPage as StartPage) : DEFAULT_PREFERENCES.startPage,
    mapView: input.mapView === '3d' || input.mapView === '2d' ? input.mapView : 'auto',
    mapLiveRefresh: typeof input.mapLiveRefresh === 'boolean' ? input.mapLiveRefresh : DEFAULT_PREFERENCES.mapLiveRefresh,
    reduceMotion: typeof input.reduceMotion === 'boolean' ? input.reduceMotion : DEFAULT_PREFERENCES.reduceMotion,
  };
}

export function readPreferences(): Preferences {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    return sanitize(saved ? JSON.parse(saved) : null);
  } catch {
    return { ...DEFAULT_PREFERENCES };
  }
}

/** Reflect preferences that CSS needs onto <html>. Safe to call any time. */
export function applyPreferences(prefs: Preferences = readPreferences()): void {
  if (typeof document === 'undefined') return;
  if (prefs.reduceMotion) document.documentElement.setAttribute('data-reduce-motion', 'true');
  else document.documentElement.removeAttribute('data-reduce-motion');
}

export function writePreferences(patch: Partial<Preferences>): Preferences {
  const next = sanitize({ ...readPreferences(), ...patch });
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // Private windows can refuse storage; the choice then lasts for this page only.
  }
  applyPreferences(next);
  window.dispatchEvent(new CustomEvent(CHANGE_EVENT, { detail: next }));
  return next;
}

export function resetPreferences(): Preferences {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
  applyPreferences(DEFAULT_PREFERENCES);
  window.dispatchEvent(new CustomEvent(CHANGE_EVENT, { detail: DEFAULT_PREFERENCES }));
  return { ...DEFAULT_PREFERENCES };
}

/** True when either the person's device or their ResilAI preference asks for less motion. */
export function motionReduced(): boolean {
  if (typeof window === 'undefined') return false;
  return readPreferences().reduceMotion || !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}

/** Live view of the preferences; updates when they change in this tab or another one. */
export function usePreferences(): [Preferences, (patch: Partial<Preferences>) => void] {
  const [prefs, setPrefs] = useState<Preferences>(() => readPreferences());
  useEffect(() => {
    const sync = () => setPrefs(readPreferences());
    window.addEventListener(CHANGE_EVENT, sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener(CHANGE_EVENT, sync);
      window.removeEventListener('storage', sync);
    };
  }, []);
  return [prefs, (patch) => setPrefs(writePreferences(patch))];
}
