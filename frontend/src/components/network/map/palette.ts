import type {
  NetworkEdgeKind,
  NetworkNodeStatus,
  NetworkNodeType,
  NetworkTopologyEdge,
  NetworkTopologyNode,
  NetworkZone,
} from '../../../api';

/** Plain-English names for the zones the backend groups systems into. */
export const ZONE_LABELS: Record<NetworkZone, string> = {
  internet: 'Internet',
  cloud: 'Cloud platform',
  security: 'Security tooling',
  servers: 'Servers',
  workstations: 'Staff computers',
  data: 'Data & databases',
  backups: 'Backups',
  identity: 'People & accounts',
};

export const ZONE_ORDER: NetworkZone[] = [
  'internet', 'security', 'cloud', 'servers', 'data', 'backups', 'workstations', 'identity',
];

/** Zone hue — fixed values so the map reads the same in both themes. */
export const ZONE_COLORS: Record<NetworkZone, string> = {
  internet: '#ef4444',
  cloud: '#6366f1',
  security: '#0ea5e9',
  servers: '#8b5cf6',
  workstations: '#14b8a6',
  data: '#f97316',
  backups: '#84cc16',
  identity: '#ec4899',
};

export const TYPE_LABELS: Record<NetworkNodeType, string> = {
  connector: 'Connected system',
  server: 'Server',
  workstation: 'Computer',
  database: 'Database',
  bucket: 'File storage',
  identity: 'Account',
  security_group: 'Firewall rules',
  internet: 'Internet',
};

export const STATUS_LABELS: Record<NetworkNodeStatus, string> = {
  healthy: 'Looks fine',
  warning: 'Worth a look',
  attention: 'Needs attention',
  error: 'Not reporting',
  unknown: 'Not checked',
};

export const STATUS_ORDER: NetworkNodeStatus[] = ['attention', 'error', 'warning', 'healthy', 'unknown'];

export const EDGE_LABELS: Record<NetworkEdgeKind, string> = {
  monitors: 'watches over',
  backs_up: 'backs up',
  authenticates: 'signs in',
  exposed_to_internet: 'reachable from the internet',
};

/** Tailwind token classes for status text (design tokens only, no new palette). */
export const STATUS_TEXT_CLASS: Record<NetworkNodeStatus, string> = {
  healthy: 'text-ready-emerald',
  warning: 'text-drift-amber',
  attention: 'text-red-500',
  error: 'text-red-500',
  unknown: 'text-on-surface-variant',
};

export const STATUS_DOT_CLASS: Record<NetworkNodeStatus, string> = {
  healthy: 'bg-ready-emerald',
  warning: 'bg-drift-amber',
  attention: 'bg-red-500',
  error: 'bg-red-500',
  unknown: 'bg-on-surface-variant/40',
};

/** Read a CSS custom property from :root at runtime (theme aware). */
export function cssVar(name: string, fallback: string): string {
  if (typeof window === 'undefined' || typeof getComputedStyle !== 'function') return fallback;
  try {
    const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value || fallback;
  } catch {
    return fallback;
  }
}

export interface ThemeColors {
  background: string;
  text: string;
  mutedText: string;
  edge: string;
  emerald: string;
  amber: string;
  red: string;
  isDark: boolean;
}

export function readThemeColors(): ThemeColors {
  const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
  return {
    background: cssVar('--color-surface-container-lowest', isDark ? '#060e20' : '#ffffff'),
    text: cssVar('--color-on-surface', isDark ? '#dae2fd' : '#0f172a'),
    mutedText: cssVar('--color-on-surface-variant', isDark ? '#bbcabf' : '#475569'),
    edge: cssVar('--color-outline-variant', isDark ? '#3c4a42' : '#e2e8f0'),
    emerald: cssVar('--color-ready-emerald', '#10B981'),
    amber: cssVar('--color-drift-amber', '#F59E0B'),
    red: '#ef4444',
    isDark,
  };
}

export function statusColor(status: NetworkNodeStatus, theme: ThemeColors): string {
  switch (status) {
    case 'healthy':
      return theme.emerald;
    case 'warning':
      return theme.amber;
    case 'attention':
    case 'error':
      return theme.red;
    default:
      return theme.mutedText;
  }
}

export function nodeRadius(node: NetworkTopologyNode): number {
  switch (node.type) {
    case 'internet':
      return 9;
    case 'connector':
      return 8;
    case 'server':
    case 'database':
      return 6.5;
    case 'bucket':
    case 'security_group':
      return 5.5;
    default:
      return 5;
  }
}

export function edgeColor(edge: NetworkTopologyEdge, theme: ThemeColors): string {
  switch (edge.kind) {
    case 'exposed_to_internet':
      return theme.red;
    case 'backs_up':
      return ZONE_COLORS.backups;
    case 'authenticates':
      return ZONE_COLORS.identity;
    default:
      return theme.edge;
  }
}

/** One short line: what this thing is, for the hover tooltip and the panel header. */
export function describeNode(node: NetworkTopologyNode): string {
  const type = TYPE_LABELS[node.type] || node.type;
  const zone = ZONE_LABELS[node.zone] || node.zone;
  if (node.type === 'internet') return 'Everything outside your organisation.';
  if (node.type === 'connector') return `${type} feeding this map (${zone.toLowerCase()}).`;
  return `${type} in “${zone}”.`;
}

export function formatRelative(iso?: string | null): string {
  if (!iso) return 'not recorded';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return iso;
  const diffMs = Date.now() - then;
  const minutes = Math.round(diffMs / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  return `${days} days ago`;
}
