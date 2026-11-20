import { describe, it, expect } from 'vitest';
import { layoutScene } from '../components/network/map/Graph3DLite';
import { TIER_HEIGHT } from '../components/network/map/palette';
import type { NetworkTopologyEdge, NetworkTopologyNode } from '../api';

const node = (id: string, type: NetworkTopologyNode['type']): NetworkTopologyNode => ({
  id,
  type,
  label: id,
  sublabel: '',
  status: 'healthy',
  zone: 'servers',
  meta: { issues: [], seen_by: [], last_seen: null },
});

const nodes: NetworkTopologyNode[] = [
  node('internet', 'internet'),
  node('gw', 'gateway'),
  node('net', 'network'),
  node('sub-a', 'subnet'),
  node('srv-1', 'server'),
  node('srv-2', 'server'),
  node('pc-1', 'workstation'),
  node('user-1', 'identity'),
  node('tool', 'connector'),
];
const edges: NetworkTopologyEdge[] = [
  { source: 'internet', target: 'gw', kind: 'routes_to', label: '' },
  { source: 'gw', target: 'net', kind: 'routes_to', label: '' },
  { source: 'sub-a', target: 'net', kind: 'part_of', label: '' },
  { source: 'srv-1', target: 'sub-a', kind: 'member_of', label: '' },
  { source: 'srv-2', target: 'sub-a', kind: 'member_of', label: '' },
  { source: 'pc-1', target: 'sub-a', kind: 'member_of', label: '' },
  { source: 'tool', target: 'srv-1', kind: 'monitors', label: '' },
];

describe('layoutScene (3D map without WebGL)', () => {
  it('puts every system on the floor for its kind', () => {
    const pos = layoutScene(nodes, edges);
    expect(pos.size).toBe(nodes.length);
    const lift = pos.get('internet')!.y - TIER_HEIGHT.internet;
    expect(pos.get('gw')!.y).toBe(TIER_HEIGHT.edge + lift);
    expect(pos.get('net')!.y).toBe(TIER_HEIGHT.networks + lift);
    expect(pos.get('srv-1')!.y).toBe(TIER_HEIGHT.systems + lift);
    expect(pos.get('user-1')!.y).toBe(TIER_HEIGHT.people + lift);
    expect(pos.get('tool')!.y).toBe(TIER_HEIGHT.tools + lift);
    pos.forEach((p) => {
      expect(Number.isFinite(p.x)).toBe(true);
      expect(Number.isFinite(p.z)).toBe(true);
    });
  });

  it('is deterministic: the same organisation always draws the same map', () => {
    const a = layoutScene(nodes, edges);
    const b = layoutScene(nodes, edges);
    nodes.forEach((n) => expect(b.get(n.id)).toEqual(a.get(n.id)));
  });

  it('does not stack two devices on the same spot of one floor', () => {
    const pos = layoutScene(nodes, edges);
    const a = pos.get('srv-1')!;
    const b = pos.get('srv-2')!;
    expect(Math.hypot(a.x - b.x, a.z - b.z)).toBeGreaterThan(12);
  });

  it('keeps existing positions close when one device is added on a live refresh', () => {
    const before = layoutScene(nodes, edges);
    const after = layoutScene([...nodes, node('pc-2', 'workstation')], edges, before);
    nodes.forEach((n) => {
      const p = before.get(n.id)!;
      const q = after.get(n.id)!;
      expect(Math.hypot(p.x - q.x, p.z - q.z)).toBeLessThan(40);
    });
    expect(after.has('pc-2')).toBe(true);
  });
});
