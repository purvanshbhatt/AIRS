// src/lib/design-tokens.ts
// Single source of truth for the ResilAI Visual Design Philosophy (Apple Health / Linear inspired)

export const tokens = {
  // Spacing & Layout
  layout: {
    pageContainer: 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8',
    sectionGap: 'space-y-12',
    cardGap: 'gap-6',
  },
  
  // Typography
  typography: {
    hero: 'text-4xl font-semibold tracking-tight text-slate-900 dark:text-white',
    sectionTitle: 'text-2xl font-medium tracking-tight text-slate-900 dark:text-white',
    cardTitle: 'text-lg font-medium text-slate-900 dark:text-white',
    body: 'text-base text-slate-600 dark:text-slate-300',
    small: 'text-sm text-slate-500 dark:text-slate-400',
    label: 'text-xs font-medium tracking-wide uppercase text-slate-500 dark:text-slate-400',
  },

  // Surface & Elevation (Cards, Panels)
  surface: {
    base: 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl',
    glass: 'bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border border-slate-200/50 dark:border-slate-800/50 rounded-xl',
    drawer: 'bg-white dark:bg-slate-950 border-l border-slate-200 dark:border-slate-800 shadow-2xl',
  },

  // Interactive & Animation
  interaction: {
    hover: 'transition-all duration-200 ease-out hover:shadow-md hover:-translate-y-0.5',
    tap: 'active:scale-95 transition-transform duration-75',
    focus: 'focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 dark:focus:ring-offset-slate-900',
  },

  // Status Badges & Colors
  status: {
    ready: {
      bg: 'bg-emerald-50 dark:bg-emerald-500/10',
      text: 'text-emerald-700 dark:text-emerald-400',
      border: 'border-emerald-200 dark:border-emerald-500/20',
      icon: 'text-emerald-600 dark:text-emerald-500',
    },
    warning: {
      bg: 'bg-amber-50 dark:bg-amber-500/10',
      text: 'text-amber-700 dark:text-amber-400',
      border: 'border-amber-200 dark:border-amber-500/20',
      icon: 'text-amber-600 dark:text-amber-500',
    },
    error: {
      bg: 'bg-rose-50 dark:bg-rose-500/10',
      text: 'text-rose-700 dark:text-rose-400',
      border: 'border-rose-200 dark:border-rose-500/20',
      icon: 'text-rose-600 dark:text-rose-500',
    },
    neutral: {
      bg: 'bg-slate-50 dark:bg-slate-500/10',
      text: 'text-slate-700 dark:text-slate-400',
      border: 'border-slate-200 dark:border-slate-500/20',
      icon: 'text-slate-500 dark:text-slate-400',
    },
  },

  // Button Variants
  button: {
    primary: 'inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-lg bg-slate-900 text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100 transition-colors',
    secondary: 'inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 dark:bg-slate-900 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800 transition-colors',
    ghost: 'inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white transition-colors',
    aiExplain: 'inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100 hover:bg-indigo-100 dark:bg-indigo-500/10 dark:text-indigo-300 dark:border-indigo-500/20 dark:hover:bg-indigo-500/20 transition-all hover:scale-105 cursor-pointer',
  }
};
