import React, { forwardRef, useEffect, useImperativeHandle, useMemo, useRef } from 'react';
import type { NetworkTopologyEdge, NetworkTopologyNode } from '../../../api';
import type { GraphHandle, GraphViewProps } from './Graph2D';
import { motionReduced } from '../../../lib/preferences';
import {
  TIER_HEIGHT,
  TIER_LABELS,
  TIER_ORDER,
  ZONE_COLORS,
  edgeColor,
  nodeRadius,
  nodeTier,
  statusColor,
  type NetworkTier,
} from './palette';

/**
 * 3D map drawn with the plain 2D canvas: no WebGL, no three.js.
 *
 * Chrome on Linux, virtual machines, remote desktops and locked-down office
 * PCs often have graphics acceleration switched off, and there WebGL simply
 * does not exist. This view does the 3D maths itself (orbit camera,
 * perspective, depth sorting) so the same floors-and-links building still
 * turns, zooms and opens on click on any browser that can draw a canvas.
 *
 * Same contract as Graph3D / Graph2D (`GraphViewProps`, `GraphHandle`).
 */

interface Vec3 {
  x: number;
  y: number;
  z: number;
}

interface Camera {
  yaw: number;
  pitch: number;
  dist: number;
  target: Vec3;
}

interface Projected {
  node: NetworkTopologyNode;
  sx: number;
  sy: number;
  r: number;
  depth: number;
}

const PITCH_MIN = 0.12;
const PITCH_MAX = 1.35;
const NODE_LIFT = 6;

const TIER_RING: Record<NetworkTier, number> = {
  internet: 0,
  edge: 70,
  networks: 110,
  systems: 190,
  people: 150,
  tools: 200,
};

const SPRING_LENGTH: Partial<Record<NetworkTopologyEdge['kind'], number>> = {
  member_of: 62,
  part_of: 66,
  protects: 56,
  vpn_tunnel: 92,
  routes_to: 80,
};

function hash(text: string): number {
  let h = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) / 4294967295;
}

const endpointId = (end: unknown): string =>
  typeof end === 'object' && end !== null ? String((end as { id?: string }).id ?? '') : String(end);

/**
 * Place every node on its floor. Deterministic (seeded from the node id), so
 * the same organisation always draws the same building, and positions from
 * the previous refresh are kept so the 45-second live update does not shuffle
 * the map.
 */
export function layoutScene(
  nodes: NetworkTopologyNode[],
  edges: NetworkTopologyEdge[],
  previous: Map<string, Vec3> = new Map(),
): Map<string, Vec3> {
  const ids = nodes.map((n) => n.id);
  const index = new Map(ids.map((id, i) => [id, i]));
  const n = nodes.length;
  const px = new Float64Array(n);
  const pz = new Float64Array(n);
  const vx = new Float64Array(n);
  const vz = new Float64Array(n);
  const tier: NetworkTier[] = nodes.map((node) => nodeTier(node));

  let known = 0;
  nodes.forEach((node, i) => {
    const prev = previous.get(node.id);
    if (prev) {
      px[i] = prev.x;
      pz[i] = prev.z;
      known += 1;
      return;
    }
    const angle = hash(node.id) * Math.PI * 2;
    const ring = TIER_RING[tier[i]] * (0.75 + hash(`${node.id}:r`) * 0.5);
    px[i] = Math.cos(angle) * ring;
    pz[i] = Math.sin(angle) * ring;
  });

  const springs: Array<{ a: number; b: number; length: number; strength: number }> = [];
  edges.forEach((edge) => {
    const a = index.get(endpointId(edge.source));
    const b = index.get(endpointId(edge.target));
    if (a === undefined || b === undefined || a === b) return;
    // "Watches" links fan out from every security tool to everything; letting
    // them pull would collapse the map into one knot.
    const watching = edge.kind === 'monitors';
    springs.push({ a, b, length: SPRING_LENGTH[edge.kind] ?? 82, strength: watching ? 0.006 : 0.07 });
  });

  // A refresh that only adds a device needs a nudge, not a full re-layout.
  const warm = n > 0 && known / n > 0.8;
  const iterations = warm ? 40 : Math.max(120, Math.min(320, Math.round(42000 / Math.max(n, 1))));

  for (let step = 0; step < iterations; step += 1) {
    const alpha = (warm ? 0.25 : 1) * (1 - step / iterations) + 0.02;
    for (let i = 0; i < n; i += 1) {
      for (let j = i + 1; j < n; j += 1) {
        let dx = px[i] - px[j];
        let dz = pz[i] - pz[j];
        let d2 = dx * dx + dz * dz;
        if (d2 < 0.01) {
          dx = hash(ids[i]) - 0.5;
          dz = hash(ids[j]) - 0.5;
          d2 = 0.01;
        }
        if (d2 > 330 * 330) continue;
        // Things on the same floor must not sit on top of each other; things
        // on different floors may overlap in plan view.
        const push = ((tier[i] === tier[j] ? 3400 : 520) / d2) * alpha;
        const d = Math.sqrt(d2);
        const fx = (dx / d) * push;
        const fz = (dz / d) * push;
        vx[i] += fx;
        vz[i] += fz;
        vx[j] -= fx;
        vz[j] -= fz;
      }
    }
    springs.forEach(({ a, b, length, strength }) => {
      const dx = px[b] - px[a];
      const dz = pz[b] - pz[a];
      const d = Math.sqrt(dx * dx + dz * dz) || 0.01;
      const pull = (d - length) * strength * alpha;
      const fx = (dx / d) * pull;
      const fz = (dz / d) * pull;
      vx[a] += fx;
      vz[a] += fz;
      vx[b] -= fx;
      vz[b] -= fz;
    });
    for (let i = 0; i < n; i += 1) {
      const gravity = tier[i] === 'internet' ? 0.12 : 0.009;
      vx[i] -= px[i] * gravity * alpha;
      vz[i] -= pz[i] * gravity * alpha;
      vx[i] *= 0.62;
      vz[i] *= 0.62;
      px[i] += Math.max(-18, Math.min(18, vx[i]));
      pz[i] += Math.max(-18, Math.min(18, vz[i]));
    }
  }

  const out = new Map<string, Vec3>();
  nodes.forEach((node, i) => {
    out.set(node.id, { x: px[i], y: TIER_HEIGHT[tier[i]] + NODE_LIFT, z: pz[i] });
  });
  return out;
}

function withAlpha(color: string, alpha: number): string {
  const hex = color.trim();
  const short = /^#([0-9a-f]{3})$/i.exec(hex);
  const long = /^#([0-9a-f]{6})$/i.exec(hex);
  if (short) {
    const [r, g, b] = short[1].split('').map((c) => parseInt(c + c, 16));
    return `rgba(${r},${g},${b},${alpha})`;
  }
  if (long) {
    const v = parseInt(long[1], 16);
    return `rgba(${(v >> 16) & 255},${(v >> 8) & 255},${v & 255},${alpha})`;
  }
  const rgb = /^rgba?\(([^)]+)\)$/i.exec(hex);
  if (rgb) {
    const [r, g, b] = rgb[1].split(/[\s,/]+/).filter(Boolean);
    return `rgba(${r},${g},${b},${alpha})`;
  }
  return hex;
}

function polygon(ctx: CanvasRenderingContext2D, x: number, y: number, r: number, sides: number, rotation = 0) {
  ctx.beginPath();
  for (let i = 0; i < sides; i += 1) {
    const a = rotation + (i / sides) * Math.PI * 2;
    const px = x + Math.cos(a) * r;
    const py = y + Math.sin(a) * r;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
}

/** One outline per kind of thing, so shape alone tells a server from a VPN. */
function tracePath(ctx: CanvasRenderingContext2D, type: NetworkTopologyNode['type'], x: number, y: number, r: number) {
  switch (type) {
    case 'server':
    case 'database':
      polygon(ctx, x, y, r * 1.15, 4, Math.PI / 4);
      break;
    case 'gateway':
    case 'security_group':
      polygon(ctx, x, y, r * 1.15, 4, 0);
      break;
    case 'network':
    case 'connector':
      polygon(ctx, x, y, r * 1.1, 6, Math.PI / 6);
      break;
    case 'bucket':
      polygon(ctx, x, y, r * 1.15, 3, Math.PI / 2);
      break;
    case 'subnet':
      ctx.beginPath();
      ctx.ellipse(x, y, r * 1.3, r * 0.75, 0, 0, Math.PI * 2);
      break;
    default:
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
  }
}

const prefersReducedMotion = motionReduced;

export const Graph3DLite = forwardRef<GraphHandle, GraphViewProps>(function Graph3DLite(
  { nodes, edges, width, height, theme, selectedId, onSelect, onHover, showMonitoring },
  ref,
) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const positionsRef = useRef<Map<string, Vec3>>(new Map());
  const cameraRef = useRef<Camera>({ yaw: 0.6, pitch: 0.52, dist: 600, target: { x: 0, y: 0, z: 0 } });
  const goalRef = useRef<{ target: Vec3; dist: number } | null>(null);
  const projectedRef = useRef<Projected[]>([]);
  const radiusRef = useRef(200);
  const autoRotateRef = useRef(true);
  const hoverIdRef = useRef<string | null>(null);
  const framedRef = useRef(false);
  const dirtyRef = useRef(true);

  // Latest props for the draw loop, which lives outside React's render cycle.
  const live = useRef({ nodes, edges, theme, selectedId, showMonitoring, width, height, onSelect, onHover });
  live.current = { nodes, edges, theme, selectedId, showMonitoring, width, height, onSelect, onHover };
  dirtyRef.current = true;

  const topologyKey = useMemo(
    () =>
      `${nodes.map((n) => n.id).join('|')}#${edges
        .map((e) => `${endpointId(e.source)}>${endpointId(e.target)}:${e.kind}`)
        .join('|')}`,
    [nodes, edges],
  );

  const neighbours = useMemo(() => {
    const map = new Map<string, Set<string>>();
    edges.forEach((edge) => {
      const a = endpointId(edge.source);
      const b = endpointId(edge.target);
      if (!map.has(a)) map.set(a, new Set());
      if (!map.has(b)) map.set(b, new Set());
      map.get(a)!.add(b);
      map.get(b)!.add(a);
    });
    return map;
  }, [edges]);
  const neighboursRef = useRef(neighbours);
  neighboursRef.current = neighbours;

  const frameAll = (animate: boolean) => {
    const points = Array.from(positionsRef.current.values());
    if (!points.length) return;
    let minY = Infinity;
    let maxY = -Infinity;
    let reach = 60;
    points.forEach((p) => {
      minY = Math.min(minY, p.y);
      maxY = Math.max(maxY, p.y);
      reach = Math.max(reach, Math.hypot(p.x, p.z));
    });
    const centreY = (minY + maxY) / 2;
    const radius = Math.max(reach + 30, (maxY - minY) / 2 + 40);
    radiusRef.current = radius;
    const goal = { target: { x: 0, y: centreY, z: 0 }, dist: radius * 2.1 };
    if (animate) {
      goalRef.current = goal;
    } else {
      cameraRef.current.target = goal.target;
      cameraRef.current.dist = goal.dist;
      goalRef.current = null;
    }
    dirtyRef.current = true;
  };

  useImperativeHandle(ref, () => ({ fit: () => frameAll(true) }));

  // Layout: only when the set of systems or links changes.
  useEffect(() => {
    positionsRef.current = layoutScene(nodes, edges, positionsRef.current);
    if (!framedRef.current && nodes.length) {
      frameAll(false);
      framedRef.current = true;
    } else {
      // Keep the camera where the person left it; only refresh the scene size.
      let reach = 60;
      positionsRef.current.forEach((p) => {
        reach = Math.max(reach, Math.hypot(p.x, p.z));
      });
      radiusRef.current = reach + 30;
    }
    dirtyRef.current = true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topologyKey]);

  // Fly to whatever was opened (from a click, or from the search box).
  useEffect(() => {
    if (!selectedId) return;
    const pos = positionsRef.current.get(selectedId);
    if (!pos) return;
    autoRotateRef.current = false;
    goalRef.current = {
      target: { ...pos },
      dist: Math.min(cameraRef.current.dist, Math.max(radiusRef.current * 1.25, 220)),
    };
    dirtyRef.current = true;
  }, [selectedId]);

  // Draw loop + input. Set up once; reads everything through refs.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    let ctx: CanvasRenderingContext2D | null = null;
    try {
      ctx = canvas.getContext('2d');
    } catch {
      ctx = null;
    }
    const reduced = prefersReducedMotion();
    if (reduced) autoRotateRef.current = false;
    let raf = 0;
    let disposed = false;

    const project = (p: Vec3, cam: Camera, w: number, h: number) => {
      const dx = p.x - cam.target.x;
      const dy = p.y - cam.target.y;
      const dz = p.z - cam.target.z;
      const cy = Math.cos(cam.yaw);
      const sy = Math.sin(cam.yaw);
      const x1 = dx * cy - dz * sy;
      const z1 = dx * sy + dz * cy;
      const cp = Math.cos(cam.pitch);
      const sp = Math.sin(cam.pitch);
      const y2 = dy * cp + z1 * sp;
      const z2 = z1 * cp - dy * sp;
      const depth = cam.dist + z2;
      const scale = (Math.min(w, h) * 0.95) / Math.max(depth, 20);
      return { sx: w / 2 + x1 * scale, sy: h / 2 - y2 * scale, depth, scale };
    };

    const draw = (time: number) => {
      const state = live.current;
      const cam = cameraRef.current;
      const w = state.width;
      const h = state.height;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
        canvas.width = Math.round(w * dpr);
        canvas.height = Math.round(h * dpr);
      }
      if (!ctx) return;
      const { theme: t } = state;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = t.background;
      ctx.fillRect(0, 0, w, h);

      const positions = positionsRef.current;
      const selected = state.selectedId;
      const near = selected ? neighboursRef.current.get(selected) ?? new Set<string>() : null;
      const isLit = (id: string) => !selected || id === selected || !!near?.has(id);

      const floorLabels: Array<[number, number, number, number]> = [];
      // Floors, lowest first so the upper ones sit over them.
      const byTier = new Map<NetworkTier, Vec3[]>();
      state.nodes.forEach((node) => {
        const pos = positions.get(node.id);
        if (!pos) return;
        const tier = nodeTier(node);
        if (!byTier.has(tier)) byTier.set(tier, []);
        byTier.get(tier)!.push(pos);
      });
      [...TIER_ORDER].reverse().forEach((tier) => {
        const points = byTier.get(tier);
        if (!points?.length) return;
        let cx = 0;
        let cz = 0;
        points.forEach((p) => {
          cx += p.x;
          cz += p.z;
        });
        cx /= points.length;
        cz /= points.length;
        let radius = 34;
        points.forEach((p) => {
          radius = Math.max(radius, Math.hypot(p.x - cx, p.z - cz) + 30);
        });
        const y = TIER_HEIGHT[tier];
        let labelX = Infinity;
        let labelY = 0;
        ctx!.beginPath();
        for (let i = 0; i <= 56; i += 1) {
          const a = (i / 56) * Math.PI * 2;
          const p = project({ x: cx + Math.cos(a) * radius, y, z: cz + Math.sin(a) * radius }, cam, w, h);
          if (i === 0) ctx!.moveTo(p.sx, p.sy);
          else ctx!.lineTo(p.sx, p.sy);
          if (p.sx < labelX) {
            labelX = p.sx;
            labelY = p.sy;
          }
        }
        ctx!.closePath();
        ctx!.fillStyle = t.isDark ? 'rgba(255,255,255,0.04)' : 'rgba(15,23,42,0.035)';
        ctx!.fill();
        ctx!.strokeStyle = withAlpha(t.mutedText, 0.28);
        ctx!.lineWidth = 1;
        ctx!.stroke();
        // Floor name sits just outside the left rim, clear of the devices.
        const name = TIER_LABELS[tier].toUpperCase();
        ctx!.font = '700 10px Inter, system-ui, sans-serif';
        ctx!.textBaseline = 'middle';
        const nameWidth = ctx!.measureText(name).width;
        const fitsOutside = labelX - 10 - nameWidth > 8;
        const nameX = fitsOutside ? labelX - 10 - nameWidth : 10;
        ctx!.textAlign = 'left';
        ctx!.fillStyle = withAlpha(t.mutedText, 0.95);
        ctx!.fillText(name, nameX, labelY);
        floorLabels.push([nameX - 2, labelY - 8, nameX + nameWidth + 2, labelY + 8]);
      });

      // Project every node once.
      const nodeById = new Map<string, NetworkTopologyNode>();
      const projected: Projected[] = [];
      const screen = new Map<string, Projected>();
      state.nodes.forEach((node) => {
        const pos = positions.get(node.id);
        if (!pos) return;
        nodeById.set(node.id, node);
        const p = project(pos, cam, w, h);
        if (p.depth < 24) return;
        const item: Projected = {
          node,
          sx: p.sx,
          sy: p.sy,
          depth: p.depth,
          r: Math.max(3.5, Math.min(26, nodeRadius(node) * 1.45 * p.scale)),
        };
        projected.push(item);
        screen.set(node.id, item);
      });

      // Links.
      state.edges.forEach((edge) => {
        const a = endpointId(edge.source);
        const b = endpointId(edge.target);
        const pa = screen.get(a);
        const pb = screen.get(b);
        if (!pa || !pb) return;
        const touchesSelected = !!selected && (a === selected || b === selected);
        if (edge.kind === 'monitors' && !state.showMonitoring && !touchesSelected) return;
        let color = edgeColor(edge, t);
        let dashed = false;
        if (edge.kind === 'vpn_tunnel') {
          const vpn = [nodeById.get(a), nodeById.get(b)].find((nd) => nd?.type === 'vpn');
          if (vpn) {
            color = statusColor(vpn.status, t);
            dashed = vpn.status !== 'healthy';
          }
        }
        const strong = edge.kind === 'vpn_tunnel' || edge.kind === 'exposed_to_internet';
        const alpha = selected ? (touchesSelected ? 0.95 : 0.07) : strong ? 0.85 : edge.kind === 'monitors' ? 0.3 : 0.5;
        ctx!.strokeStyle = withAlpha(color, alpha);
        ctx!.lineWidth = touchesSelected ? 2.2 : strong ? 1.8 : 1;
        ctx!.setLineDash(dashed ? [5, 4] : []);
        ctx!.beginPath();
        ctx!.moveTo(pa.sx, pa.sy);
        ctx!.lineTo(pb.sx, pb.sy);
        ctx!.stroke();
        ctx!.setLineDash([]);
        // A dot travelling along live links: traffic through a tunnel, a route
        // out to the internet, one system talking to another.
        const flows = !dashed && (strong || edge.kind === 'talks_to' || edge.kind === 'routes_to');
        if (flows && !reduced && alpha > 0.2) {
          const phase = (time / 2600 + hash(`${a}>${b}`)) % 1;
          ctx!.fillStyle = withAlpha(color, 0.95);
          ctx!.beginPath();
          ctx!.arc(pa.sx + (pb.sx - pa.sx) * phase, pa.sy + (pb.sy - pa.sy) * phase, 2.1, 0, Math.PI * 2);
          ctx!.fill();
        }
      });

      // Nodes, far to near.
      projected.sort((p, q) => q.depth - p.depth);
      const hoverId = hoverIdRef.current;
      projected.forEach((item) => {
        const { node, sx, sy, r } = item;
        const lit = isLit(node.id);
        const fill = ZONE_COLORS[node.zone] || t.mutedText;
        const ring = statusColor(node.status, t);
        ctx!.globalAlpha = lit ? 1 : 0.2;
        if (node.id === selected || node.id === hoverId) {
          ctx!.beginPath();
          ctx!.arc(sx, sy, r + 6, 0, Math.PI * 2);
          ctx!.fillStyle = t.isDark ? 'rgba(255,255,255,0.16)' : 'rgba(15,23,42,0.1)';
          ctx!.fill();
        }
        const urgent = node.status === 'attention' || node.status === 'error';
        if (urgent && !reduced && lit) {
          const beat = (time / 1400 + hash(node.id)) % 1;
          ctx!.beginPath();
          ctx!.arc(sx, sy, r + 3 + beat * 10, 0, Math.PI * 2);
          ctx!.strokeStyle = withAlpha(ring, 0.55 * (1 - beat));
          ctx!.lineWidth = 1.5;
          ctx!.stroke();
        }
        tracePath(ctx!, node.type, sx, sy, r);
        if (node.type === 'vpn') {
          // A VPN is a ring: a tunnel seen end-on.
          ctx!.lineWidth = Math.max(2.5, r * 0.45);
          ctx!.strokeStyle = ring;
          ctx!.stroke();
        } else {
          ctx!.fillStyle = fill;
          ctx!.fill();
          ctx!.lineWidth = urgent ? 2.4 : 1.5;
          ctx!.strokeStyle = ring;
          ctx!.stroke();
        }
        ctx!.globalAlpha = 1;
      });

      // Labels, nearest first; skip any that would land on one already drawn.
      const showAll = projected.length <= 45;
      const taken: Array<[number, number, number, number]> = [...floorLabels];
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      for (let i = projected.length - 1; i >= 0; i -= 1) {
        const { node, sx, sy, r } = projected[i];
        const important = node.id === selected || node.id === hoverId || (!!selected && !!near?.has(node.id));
        if (!important && (selected || (!showAll && r < 7.5))) continue;
        const size = important ? 12 : Math.max(10, Math.min(12, r + 3));
        ctx.font = `${important ? 700 : 600} ${size}px Inter, system-ui, sans-serif`;
        const text = node.label.length > 26 ? `${node.label.slice(0, 25)}…` : node.label;
        const tw = ctx.measureText(text).width;
        const box: [number, number, number, number] = [sx - tw / 2 - 2, sy + r + 3, sx + tw / 2 + 2, sy + r + 5 + size];
        if (!important && taken.some((o) => box[0] < o[2] && box[2] > o[0] && box[1] < o[3] && box[3] > o[1])) continue;
        taken.push(box);
        ctx.lineWidth = 3;
        ctx.strokeStyle = withAlpha(t.background, 0.9);
        ctx.strokeText(text, sx, sy + r + 4);
        ctx.fillStyle = important ? t.text : withAlpha(t.text, 0.85);
        ctx.fillText(text, sx, sy + r + 4);
      }

      projectedRef.current = projected;
    };

    const tick = (time: number) => {
      if (disposed) return;
      raf = requestAnimationFrame(tick);
      if (typeof document !== 'undefined' && document.hidden) return;
      const cam = cameraRef.current;
      let moving = false;
      if (autoRotateRef.current) {
        cam.yaw += 0.0018;
        moving = true;
      }
      const goal = goalRef.current;
      if (goal) {
        const ease = reduced ? 1 : 0.14;
        cam.target.x += (goal.target.x - cam.target.x) * ease;
        cam.target.y += (goal.target.y - cam.target.y) * ease;
        cam.target.z += (goal.target.z - cam.target.z) * ease;
        cam.dist += (goal.dist - cam.dist) * ease;
        moving = true;
        if (
          Math.abs(goal.dist - cam.dist) < 0.5 &&
          Math.hypot(goal.target.x - cam.target.x, goal.target.y - cam.target.y, goal.target.z - cam.target.z) < 0.5
        ) {
          goalRef.current = null;
        }
      }
      // With reduced motion nothing animates by itself: draw only on change.
      if (reduced && !moving && !dirtyRef.current) return;
      dirtyRef.current = false;
      draw(time);
    };
    raf = requestAnimationFrame(tick);

    // ---- input -----------------------------------------------------------
    const pointers = new Map<number, { x: number; y: number }>();
    let drag: { x: number; y: number; moved: number; pan: boolean } | null = null;
    let pinch = 0;

    const local = (e: { clientX: number; clientY: number }) => {
      const rect = canvas.getBoundingClientRect();
      return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };
    const hit = (x: number, y: number): NetworkTopologyNode | null => {
      const list = projectedRef.current;
      for (let i = list.length - 1; i >= 0; i -= 1) {
        const p = list[i];
        if (Math.hypot(p.sx - x, p.sy - y) <= p.r + 6) return p.node;
      }
      return null;
    };
    const stopAuto = () => {
      autoRotateRef.current = false;
    };
    const zoomBy = (factor: number) => {
      const cam = cameraRef.current;
      const r = radiusRef.current;
      goalRef.current = null;
      cam.dist = Math.max(r * 0.35, Math.min(r * 7, cam.dist * factor));
      dirtyRef.current = true;
    };

    const onDown = (e: PointerEvent) => {
      stopAuto();
      canvas.setPointerCapture?.(e.pointerId);
      const p = local(e);
      pointers.set(e.pointerId, p);
      if (pointers.size === 2) {
        const [a, b] = Array.from(pointers.values());
        pinch = Math.hypot(a.x - b.x, a.y - b.y);
        drag = null;
        return;
      }
      drag = { x: p.x, y: p.y, moved: 0, pan: e.button === 2 || e.shiftKey };
    };
    const onMove = (e: PointerEvent) => {
      const p = local(e);
      if (pointers.has(e.pointerId)) pointers.set(e.pointerId, p);
      if (pointers.size === 2) {
        const [a, b] = Array.from(pointers.values());
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (pinch > 0 && d > 0) zoomBy(pinch / d);
        pinch = d;
        return;
      }
      if (drag) {
        const dx = p.x - drag.x;
        const dy = p.y - drag.y;
        drag.moved += Math.abs(dx) + Math.abs(dy);
        drag.x = p.x;
        drag.y = p.y;
        const cam = cameraRef.current;
        goalRef.current = null;
        if (drag.pan) {
          const k = cam.dist / (Math.min(live.current.width, live.current.height) * 0.95);
          cam.target.x -= (dx * Math.cos(cam.yaw) + dy * Math.sin(cam.yaw)) * k;
          cam.target.z -= (-dx * Math.sin(cam.yaw) + dy * Math.cos(cam.yaw)) * k;
        } else {
          cam.yaw += dx * 0.008;
          cam.pitch = Math.max(PITCH_MIN, Math.min(PITCH_MAX, cam.pitch + dy * 0.006));
        }
        dirtyRef.current = true;
        return;
      }
      const node = hit(p.x, p.y);
      const id = node ? node.id : null;
      if (id !== hoverIdRef.current) {
        hoverIdRef.current = id;
        canvas.style.cursor = node ? 'pointer' : 'grab';
        live.current.onHover?.(node);
        dirtyRef.current = true;
      }
    };
    const onUp = (e: PointerEvent) => {
      const wasDrag = drag;
      pointers.delete(e.pointerId);
      drag = null;
      pinch = 0;
      if (wasDrag && wasDrag.moved < 6) {
        const p = local(e);
        live.current.onSelect(hit(p.x, p.y));
      }
    };
    const onLeave = () => {
      if (hoverIdRef.current) {
        hoverIdRef.current = null;
        live.current.onHover?.(null);
        dirtyRef.current = true;
      }
    };
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      stopAuto();
      zoomBy(Math.exp(e.deltaY * 0.0012));
    };
    const onKey = (e: KeyboardEvent) => {
      const cam = cameraRef.current;
      let handled = true;
      if (e.key === 'ArrowLeft') cam.yaw -= 0.12;
      else if (e.key === 'ArrowRight') cam.yaw += 0.12;
      else if (e.key === 'ArrowUp') cam.pitch = Math.min(PITCH_MAX, cam.pitch + 0.08);
      else if (e.key === 'ArrowDown') cam.pitch = Math.max(PITCH_MIN, cam.pitch - 0.08);
      else if (e.key === '+' || e.key === '=') zoomBy(0.85);
      else if (e.key === '-' || e.key === '_') zoomBy(1.18);
      else handled = false;
      if (handled) {
        e.preventDefault();
        stopAuto();
        goalRef.current = null;
        dirtyRef.current = true;
      }
    };
    const onContext = (e: Event) => e.preventDefault();

    canvas.addEventListener('pointerdown', onDown);
    canvas.addEventListener('pointermove', onMove);
    canvas.addEventListener('pointerup', onUp);
    canvas.addEventListener('pointercancel', onUp);
    canvas.addEventListener('pointerleave', onLeave);
    canvas.addEventListener('wheel', onWheel, { passive: false });
    canvas.addEventListener('keydown', onKey);
    canvas.addEventListener('contextmenu', onContext);

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      canvas.removeEventListener('pointerdown', onDown);
      canvas.removeEventListener('pointermove', onMove);
      canvas.removeEventListener('pointerup', onUp);
      canvas.removeEventListener('pointercancel', onUp);
      canvas.removeEventListener('pointerleave', onLeave);
      canvas.removeEventListener('wheel', onWheel);
      canvas.removeEventListener('keydown', onKey);
      canvas.removeEventListener('contextmenu', onContext);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      data-testid="network-map-3d-lite"
      tabIndex={0}
      role="img"
      aria-label={`3D map of ${nodes.length} systems. Drag to turn, scroll to zoom, arrow keys also turn the view.`}
      style={{ width, height, display: 'block', touchAction: 'none', cursor: 'grab', outline: 'none' }}
    />
  );
});

export default Graph3DLite;
