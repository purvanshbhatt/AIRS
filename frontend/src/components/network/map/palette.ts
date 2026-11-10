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
  network: 'Networks & VPN',
};

export const ZONE_ORDER: NetworkZone[] = [
  'internet', 'network', 'security', 'cloud', 'servers', 'data', 'backups', 'workstations', 'identity',
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
  network: '#06b6d4',
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
  network: 'Network',
  subnet: 'Network segment',
  vpn: 'VPN',
  gateway: 'Gateway',
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
  member_of: 'is on',
  part_of: 'is part of',
  vpn_tunnel: 'tunnels to',
  routes_to: 'sends traffic through',
  protects: 'filters traffic for',
  talks_to: 'talks to',
};

/**
 * Floors of the 3D map, top to bottom. Each node type lives on one floor so the
 * picture reads like a building: internet on the roof, people on the ground.
 */
export type NetworkTier = 'internet' | 'edge' | 'networks' | 'systems' | 'people' | 'tools';

export const TIER_ORDER: NetworkTier[] = ['internet', 'edge', 'networks', 'systems', 'people', 'tools'];

export const TIER_LABELS: Record<NetworkTier, string> = {
  internet: 'Internet',
  edge: 'Gateways & VPN',
  networks: 'Networks',
  systems: 'Devices & data',
  people: 'People & accounts',
  tools: 'Security tools watching',
};

/** Height of each floor in scene units (y is up). */
export const TIER_HEIGHT: Record<NetworkTier, number> = {
  internet: 160,
  edge: 90,
  networks: 25,
  systems: -45,
  people: -110,
  tools: -175,
};

export function nodeTier(node: Pick<NetworkTopologyNode, 'type'>): NetworkTier {
  switch (node.type) {
    case 'internet':
      return 'internet';
    case 'gateway':
    case 'vpn':
      return 'edge';
    case 'network':
    case 'subnet':
    case 'security_group':
      return 'networks';
    case 'identity':
      return 'people';
    case 'connector':
      return 'tools';
    default:
      return 'systems';
  }
}

/** A node counts as "live" when a connected system reported it in the last 15 minutes. */
export function isFresh(node: Pick<NetworkTopologyNode, 'meta'>, now: number = Date.now()): boolean {
  const seen = node.meta?.last_seen;
  if (!seen) return false;
  const then = new Date(seen).getTime();
  return !Number.isNaN(then) && now - then < 15 * 60 * 1000;
}

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
    case 'network':
      return 8.5;
    case 'vpn':
    case 'gateway':
      return 7;
    case 'subnet':
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
    case 'vpn_tunnel':
      return theme.emerald;
    case 'talks_to':
      return ZONE_COLORS.servers;
    case 'routes_to':
    case 'member_of':
    case 'part_of':
      return ZONE_COLORS.network;
    case 'protects':
      return theme.amber;
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
  if (node.type === 'network') {
    return node.meta?.inferred
      ? 'A network worked out from the addresses your devices report.'
      : 'A network your devices sit on.';
  }
  if (node.type === 'subnet') return 'One segment of a larger network.';
  if (node.type === 'vpn') {
    return node.meta?.vpn_kind === 'client'
      ? 'A VPN that remote staff connect through.'
      : 'An encrypted tunnel joining two of your networks.';
  }
  if (node.type === 'gateway') return 'The door traffic uses to enter or leave a network.';
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
