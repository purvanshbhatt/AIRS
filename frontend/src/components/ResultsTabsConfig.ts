/**
 * Configuration for Results page tabs.
 * Separated to avoid importing the heavy ResultsTabs component just for tab config.
 */
import { Target, AlertTriangle, Shield, Calendar, Route } from 'lucide-react'

export const RESULT_TABS = [
  { id: 'overview', label: 'Overview', icon: Target },
  { id: 'findings', label: 'Findings', icon: AlertTriangle },
  { id: 'framework', label: 'Framework Mapping', icon: Shield },
  { id: 'roadmap', label: 'Roadmap', icon: Calendar },
  { id: 'analytics', label: 'Analytics', icon: Route },
] as const

export type ResultTabId = typeof RESULT_TABS[number]['id']
