// src/lib/design-tokens.ts
// Single source of truth for the ResilAI Visual Design Philosophy (Stitch Healthcare Readiness Platform / Apple Health / Linear inspired)

export const tokens = {
  // Spacing & Layout
  layout: {
    pageContainer: 'max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12',
    sectionGap: 'space-y-12',
    cardGap: 'gap-6',
  },
  
  // Typography
  typography: {
    hero: 'text-3xl md:text-5xl font-bold tracking-tight text-on-surface',
    sectionTitle: 'text-xl md:text-2xl font-semibold tracking-tight text-on-surface',
    cardTitle: 'text-base md:text-lg font-semibold text-on-surface',
    body: 'text-sm md:text-base text-on-surface-variant leading-relaxed',
    small: 'text-xs text-on-surface-variant',
    label: 'text-[11px] font-mono font-bold tracking-wider uppercase text-on-surface-variant',
    mono: 'text-xs font-mono text-on-surface',
  },

  // Surface & Elevation (Cards, Panels, Modals, Drawers)
  surface: {
    base: 'bg-surface-container-low border border-surface-bright/60 rounded-xl',
    card: 'bg-surface-container-low border border-surface-bright/60 rounded-xl hover:bg-surface-container transition-colors duration-200',
    container: 'bg-surface-container border border-surface-bright/40 rounded-xl',
    containerHigh: 'bg-surface-container-high border border-outline-variant/40 rounded-xl',
    containerLowest: 'bg-surface-container-lowest border border-outline-variant/30 rounded-xl',
    glass: 'bg-surface-container-low/90 backdrop-blur-xl border border-surface-bright/50 rounded-xl',
    drawer: 'bg-surface-container-lowest border-l border-surface-bright shadow-2xl',
  },

  // Interactive & Animation
  interaction: {
    hover: 'transition-all duration-200 ease-out hover:border-ready-emerald/40 hover:shadow-md hover:-translate-y-0.5',
    tap: 'active:scale-[0.98] transition-transform duration-75',
    focus: 'focus:outline-none focus:ring-2 focus:ring-ready-emerald/50 focus:ring-offset-2 focus:ring-offset-background',
  },

  // Status Badges & Colors
  status: {
    ready: {
      bg: 'bg-ready-emerald/10',
      text: 'text-ready-emerald',
      border: 'border-ready-emerald/30',
      icon: 'text-ready-emerald',
      glow: 'drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]',
    },
    warning: {
      bg: 'bg-drift-amber/10',
      text: 'text-drift-amber',
      border: 'border-drift-amber/30',
      icon: 'text-drift-amber',
      glow: 'drop-shadow-[0_0_15px_rgba(245,158,11,0.5)]',
    },
    error: {
      bg: 'bg-critical-red/10',
      text: 'text-critical-red',
      border: 'border-critical-red/30',
      icon: 'text-critical-red',
      glow: 'drop-shadow-[0_0_15px_rgba(239,68,68,0.5)]',
    },
    neutral: {
      bg: 'bg-surface-container-high/60',
      text: 'text-on-surface-variant',
      border: 'border-outline-variant/40',
      icon: 'text-outline',
      glow: '',
    },
  },

  // Button Variants
  button: {
    primary: 'inline-flex items-center justify-center px-4 py-2 text-sm font-semibold rounded-lg bg-ready-emerald text-surface-container-lowest hover:bg-ready-emerald/90 transition-colors shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
    secondary: 'inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-lg bg-surface-container-high border border-outline-variant/40 text-on-surface hover:bg-surface-bright transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
    ghost: 'inline-flex items-center justify-center px-3 py-1.5 text-sm font-medium rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors cursor-pointer',
    aiExplain: 'inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-full bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/30 hover:bg-ready-emerald/20 hover:border-ready-emerald/50 transition-all hover:scale-105 cursor-pointer shadow-xs',
    danger: 'inline-flex items-center justify-center px-4 py-2 text-sm font-semibold rounded-lg bg-critical-red text-white hover:bg-critical-red/90 transition-colors cursor-pointer',
  }
};
