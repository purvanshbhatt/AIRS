import React, { forwardRef, useCallback, useEffect, useImperativeHandle, useRef } from 'react';
import ForceGraph3D, { type ForceGraph3DInstance } from '3d-force-graph';
import * as THREE from 'three';
import type { NetworkTopologyEdge, NetworkTopologyNode } from '../../../api';
import {
  TIER_HEIGHT,
  TIER_LABELS,
  TIER_ORDER,
  ZONE_COLORS,
  edgeColor,
  isFresh,
  nodeTier,
  statusColor,
  type NetworkTier,
  type ThemeColors,
} from './palette';
import type { GraphHandle, GraphViewProps } from './Graph2D';

/**
 * 3D infrastructure map, driven imperatively through `3d-force-graph`.
 *
 * The scene is a building. Every kind of thing lives on its own floor
 * (internet on the roof, then gateways and VPN, networks, devices and data,
 * people, and the security tools watching it all), so a device hangs directly
 * under the network it sits on and a VPN bridges two networks above them.
 * Height is fixed per floor; the force layout only arranges things sideways.
 *
 * NetworkMap loads this module with React.lazy, so three.js only ships when
 * the 3D view opens. The React wrapper (`react-force-graph-3d`) is avoided on
 * purpose: the Vite manualChunks rule groups every module whose path contains
 * "react" into the eager vendor-react chunk, which would drag three.js into
 * the main download.
 */

type SimNode = NetworkTopologyNode & {
  x?: number;
  y?: number;
  z?: number;
  fy?: number;
  __threeObj?: THREE.Object3D;
};

const MIN_FLOOR_RADIUS = 130;
const LABEL_NODE_LIMIT = 140;
/** Shapes are modelled small; this makes them readable from the whole-building view. */
const NODE_SCALE = 1.3;
const ALWAYS_LABELLED = new Set(['internet', 'network', 'subnet', 'vpn', 'gateway', 'connector']);

function endId(end: unknown): string {
  return end && typeof end === 'object' ? String((end as { id: unknown }).id) : String(end);
}

function prefersReducedMotion(): boolean {
  try {
    return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true;
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// Text labels (canvas sprites). Canvases are cached; jsdom has no 2D context,
// so every failure simply means "no label".
// ---------------------------------------------------------------------------

const labelCanvasCache = new Map<string, HTMLCanvasElement>();

function labelCanvas(text: string, color: string, backdrop: string | null): HTMLCanvasElement | null {
  const key = `${text}|${color}|${backdrop}`;
  const cached = labelCanvasCache.get(key);
  if (cached) return cached;
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx || typeof ctx.measureText !== 'function') return null;
    const fontPx = 40;
    const font = `600 ${fontPx}px ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif`;
    ctx.font = font;
    const padX = 18;
    const width = Math.ceil(ctx.measureText(text).width) + padX * 2;
    const height = fontPx + 22;
    canvas.width = width;
    canvas.height = height;
    if (backdrop) {
      ctx.fillStyle = backdrop;
      const r = 14;
      ctx.beginPath();
      ctx.moveTo(r, 0);
      ctx.arcTo(width, 0, width, height, r);
      ctx.arcTo(width, height, 0, height, r);
      ctx.arcTo(0, height, 0, 0, r);
      ctx.arcTo(0, 0, width, 0, r);
      ctx.closePath();
      ctx.fill();
    }
    ctx.font = font;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = color;
    ctx.fillText(text, width / 2, height / 2 + 2);
    if (labelCanvasCache.size > 600) labelCanvasCache.clear();
    labelCanvasCache.set(key, canvas);
    return canvas;
  } catch {
    return null;
  }
}

function makeLabel(text: string, color: string, backdrop: string | null, worldHeight: number): THREE.Sprite | null {
  const canvas = labelCanvas(text, color, backdrop);
  if (!canvas) return null;
  try {
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set((worldHeight * canvas.width) / canvas.height, worldHeight, 1);
    sprite.userData.baseOpacity = 1;
    return sprite;
  } catch {
    return null;
  }
}

function truncate(text: string, max = 26): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

// ---------------------------------------------------------------------------
// Node shapes
// ---------------------------------------------------------------------------

function solid(color: THREE.ColorRepresentation, opacity = 1): THREE.MeshLambertMaterial {
  const material = new THREE.MeshLambertMaterial({ color, transparent: true, opacity });
  material.userData.baseOpacity = opacity;
  return material;
}

function withEdges(geometry: THREE.BufferGeometry, material: THREE.Material, edgeTint: string): THREE.Object3D {
  const group = new THREE.Group();
  group.add(new THREE.Mesh(geometry, material));
  const lineMaterial = new THREE.LineBasicMaterial({ color: edgeTint, transparent: true, opacity: 0.55 });
  lineMaterial.userData.baseOpacity = 0.55;
  group.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry), lineMaterial));
  return group;
}

/** Returns the shape plus how far it reaches below / sideways from its centre. */
function buildShape(node: SimNode, theme: ThemeColors): { body: THREE.Object3D; halfHeight: number; radius: number } {
  const base = ZONE_COLORS[node.zone] || theme.mutedText;
  const edgeTint = theme.isDark ? '#ffffff' : '#0f172a';

  switch (node.type) {
    case 'internet': {
      const group = new THREE.Group();
      const wire = new THREE.MeshBasicMaterial({ color: base, wireframe: true, transparent: true, opacity: 0.7 });
      wire.userData.baseOpacity = 0.7;
      group.add(new THREE.Mesh(new THREE.SphereGeometry(14, 16, 12), wire));
      group.add(new THREE.Mesh(new THREE.SphereGeometry(6, 20, 16), solid(base, 0.55)));
      return { body: group, halfHeight: 14, radius: 14 };
    }
    case 'gateway':
      return { body: withEdges(new THREE.OctahedronGeometry(8), solid(base), edgeTint), halfHeight: 8, radius: 8 };
    case 'vpn': {
      const tone = statusColor(node.status === 'unknown' ? 'healthy' : node.status, theme);
      const torus = new THREE.Mesh(new THREE.TorusGeometry(6.5, 2.2, 14, 32), solid(tone));
      const core = new THREE.Mesh(new THREE.SphereGeometry(2.4, 16, 12), solid(base));
      const group = new THREE.Group();
      group.add(torus, core);
      return { body: group, halfHeight: 9, radius: 9 };
    }
    case 'network':
      return {
        body: withEdges(new THREE.CylinderGeometry(17, 17, 3, 6), solid(base, 0.9), edgeTint),
        halfHeight: 1.5,
        radius: 17,
      };
    case 'subnet':
      return {
        body: withEdges(new THREE.CylinderGeometry(10.5, 10.5, 2.4, 28), solid(base, 0.75), edgeTint),
        halfHeight: 1.2,
        radius: 10.5,
      };
    case 'security_group':
      return { body: withEdges(new THREE.BoxGeometry(10, 7, 1.4), solid(base), edgeTint), halfHeight: 3.5, radius: 6 };
    case 'server': {
      const group = new THREE.Group();
      group.add(withEdges(new THREE.BoxGeometry(6.5, 11, 6.5), solid(base), edgeTint));
      // Drive bays: three light strips on the front face.
      [-2.6, 0, 2.6].forEach((y) => {
        const strip = new THREE.Mesh(new THREE.BoxGeometry(4.6, 0.7, 0.3), solid(theme.isDark ? '#e2e8f0' : '#ffffff', 0.85));
        strip.position.set(0, y, 3.35);
        group.add(strip);
      });
      return { body: group, halfHeight: 5.5, radius: 5 };
    }
    case 'workstation': {
      const group = new THREE.Group();
      const screen = withEdges(new THREE.BoxGeometry(10, 6.5, 0.8), solid(base), edgeTint);
      screen.position.y = 1.6;
      const stand = new THREE.Mesh(new THREE.BoxGeometry(1.2, 2.6, 1.2), solid(base));
      stand.position.y = -2.8;
      const foot = new THREE.Mesh(new THREE.BoxGeometry(5.5, 0.6, 3.2), solid(base));
      foot.position.y = -4.3;
      group.add(screen, stand, foot);
      return { body: group, halfHeight: 4.8, radius: 5.5 };
    }
    case 'database':
      return { body: withEdges(new THREE.CylinderGeometry(5, 5, 8.5, 24), solid(base), edgeTint), halfHeight: 4.25, radius: 5 };
    case 'bucket':
      return { body: withEdges(new THREE.CylinderGeometry(5.6, 4, 7, 20), solid(base), edgeTint), halfHeight: 3.5, radius: 5.6 };
    case 'identity': {
      const group = new THREE.Group();
      const head = new THREE.Mesh(new THREE.SphereGeometry(2.6, 18, 14), solid(base));
      head.position.y = 3.2;
      const torso = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 3.2, 5, 18), solid(base));
      torso.position.y = -1.6;
      group.add(head, torso);
      return { body: group, halfHeight: 4.2, radius: 3.4 };
    }
    case 'connector':
    default: {
      const material = solid(base);
      material.flatShading = true;
      return { body: new THREE.Mesh(new THREE.IcosahedronGeometry(6, 0), material), halfHeight: 6, radius: 6 };
    }
  }
}

function buildNodeObject(node: SimNode, theme: ThemeColors, showLabel: boolean): THREE.Object3D {
  const group = new THREE.Group();
  const { body, halfHeight, radius } = buildShape(node, theme);
  group.add(body);

  // Status light: a flat ring on the floor under the thing.
  const tone = statusColor(node.status, theme);
  const ringMaterial = new THREE.MeshBasicMaterial({
    color: tone,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: node.status === 'unknown' ? 0.35 : 0.95,
    depthWrite: false,
  });
  ringMaterial.userData.baseOpacity = ringMaterial.opacity;
  const ring = new THREE.Mesh(new THREE.RingGeometry(radius * 1.2, radius * 1.2 + 1.3, 40), ringMaterial);
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = -halfHeight - 0.6;
  group.add(ring);

  // Pulse: things that need attention, and things reported in the last few minutes.
  const needsAttention = node.status === 'attention' || node.status === 'error';
  if (needsAttention || isFresh(node)) {
    const pulseMaterial = new THREE.MeshBasicMaterial({
      color: needsAttention ? theme.red : theme.emerald,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.5,
      depthWrite: false,
    });
    pulseMaterial.userData.baseOpacity = 0.5;
    const pulse = new THREE.Mesh(new THREE.RingGeometry(radius * 1.45, radius * 1.45 + 0.9, 40), pulseMaterial);
    pulse.rotation.x = -Math.PI / 2;
    pulse.position.y = -halfHeight - 0.7;
    pulse.name = 'pulse';
    group.add(pulse);
  }

  // Selection halo, hidden until this node is picked.
  const haloMaterial = new THREE.MeshBasicMaterial({
    color: theme.text,
    transparent: true,
    opacity: 0.16,
    depthWrite: false,
  });
  haloMaterial.userData.baseOpacity = 0.16;
  const halo = new THREE.Mesh(new THREE.SphereGeometry(Math.max(radius, halfHeight) * 1.7, 20, 16), haloMaterial);
  halo.name = 'halo';
  halo.visible = false;
  group.add(halo);

  if (showLabel) {
    const label = makeLabel(
      truncate(node.label),
      theme.text,
      theme.isDark ? 'rgba(6,14,32,0.72)' : 'rgba(255,255,255,0.82)',
      6.6,
    );
    if (label) {
      label.position.y = -halfHeight - 7.5;
      label.name = 'label';
      group.add(label);
    }
  }
  group.scale.setScalar(NODE_SCALE);
  return group;
}

/** Fade or restore every material in a node object. */
function setDim(obj: THREE.Object3D | undefined, dim: boolean, selected: boolean): void {
  if (!obj || typeof obj.traverse !== 'function') return;
  obj.traverse((child: any) => {
    if (child.name === 'halo') {
      child.visible = selected;
      return;
    }
    const material = child.material;
    if (!material) return;
    const baseOpacity = material.userData?.baseOpacity ?? 1;
    material.opacity = dim ? baseOpacity * 0.12 : baseOpacity;
  });
}

// ---------------------------------------------------------------------------
// Sideways gravity: keeps unlinked things from drifting off their floor.
// ---------------------------------------------------------------------------

function gravityXZ(strength: number) {
  let simNodes: any[] = [];
  const force: any = (alpha: number) => {
    for (const n of simNodes) {
      n.vx -= (n.x || 0) * strength * alpha;
      n.vz -= (n.z || 0) * strength * alpha;
    }
  };
  force.initialize = (list: any[]) => {
    simNodes = list;
  };
  return force;
}

const LINK_DISTANCE: Record<string, number> = {
  member_of: 74,
  part_of: 30,
  vpn_tunnel: 80,
  routes_to: 80,
  protects: 76,
  talks_to: 60,
  authenticates: 80,
  backs_up: 140,
  monitors: 150,
  exposed_to_internet: 170,
};

const LINK_STRENGTH: Record<string, number> = {
  member_of: 0.9,
  part_of: 0.9,
  vpn_tunnel: 0.45,
  routes_to: 0.45,
  protects: 0.25,
  talks_to: 0.12,
  authenticates: 0.12,
  backs_up: 0.05,
  monitors: 0.015,
  exposed_to_internet: 0.03,
};

const LINK_WIDTH: Record<string, number> = {
  vpn_tunnel: 2.4,
  exposed_to_internet: 1.4,
  talks_to: 0.9,
  routes_to: 0.9,
  member_of: 0.5,
  part_of: 0.5,
  protects: 0.4,
};

export const Graph3D = forwardRef<GraphHandle, GraphViewProps>(function Graph3D(
  { nodes, edges, width, height, theme, selectedId, onSelect, onHover, showMonitoring = false },
  ref,
) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const graphRef = useRef<ForceGraph3DInstance | null>(null);
  const callbacksRef = useRef({ onSelect, onHover });
  callbacksRef.current = { onSelect, onHover };

  const nodeMapRef = useRef<Map<string, SimNode>>(new Map());
  const edgesRef = useRef<NetworkTopologyEdge[]>(edges);
  const shapeKeyRef = useRef('');
  const themeRef = useRef(theme);
  const selectedRef = useRef<string | null>(selectedId);
  const monitoringRef = useRef(showMonitoring);
  const floorsRef = useRef<THREE.Group | null>(null);
  const floorRadiusRef = useRef(MIN_FLOOR_RADIUS);
  const framedRef = useRef(false);
  themeRef.current = theme;
  selectedRef.current = selectedId;
  monitoringRef.current = showMonitoring;
  edgesRef.current = edges;

  // -- helpers --------------------------------------------------------------

  const neighbourIds = useCallback((id: string | null): Set<string> => {
    const out = new Set<string>();
    if (!id) return out;
    out.add(id);
    for (const e of edgesRef.current) {
      if (e.source === id) out.add(e.target);
      else if (e.target === id) out.add(e.source);
    }
    return out;
  }, []);

  const spreadRadius = useCallback((): number => {
    let max = 0;
    nodeMapRef.current.forEach((n) => {
      const d = Math.hypot(n.x || 0, n.z || 0);
      if (Number.isFinite(d) && d > max) max = d;
    });
    return Math.max(MIN_FLOOR_RADIUS, max + 36);
  }, []);

  /** Elevated three-quarter view of the whole building. */
  const frameAll = useCallback((ms = 900) => {
    const graph = graphRef.current as any;
    if (!graph) return;
    // Look at the middle of the occupied floors, from far enough to see them all.
    let top = -Infinity;
    let bottom = Infinity;
    nodeMapRef.current.forEach((n) => {
      const y = TIER_HEIGHT[nodeTier(n)];
      if (y > top) top = y;
      if (y < bottom) bottom = y;
    });
    if (!Number.isFinite(top)) {
      top = 0;
      bottom = 0;
    }
    const centreY = (top + bottom) / 2 - 12;
    const radius = spreadRadius();
    // 30 degrees above the horizon: every floor shows its surface, none is edge-on.
    const d = Math.max(radius * 2.2, ((top - bottom) * 0.87 + radius) * 1.3, 360);
    graph.cameraPosition({ x: d * 0.4, y: centreY + d * 0.5, z: d * 0.77 }, { x: 0, y: centreY, z: 0 }, ms);
  }, [spreadRadius]);

  const flyTo = useCallback(
    (node: SimNode) => {
      const graph = graphRef.current as any;
      if (!graph) return;
      // Containers: frame the thing together with everything attached to it.
      if (node.type === 'network' || node.type === 'subnet' || node.type === 'vpn' || node.type === 'connector') {
        const ids = neighbourIds(node.id);
        if (ids.size > 1) {
          graph.zoomToFit(800, 70, (n: SimNode) => ids.has(n.id));
          return;
        }
      }
      const x = node.x || 0;
      const y = node.y || 0;
      const z = node.z || 0;
      let dx = x;
      let dz = z;
      try {
        const cam = graph.cameraPosition();
        if (Number.isFinite(cam?.x) && Number.isFinite(cam?.z)) {
          dx = cam.x - x;
          dz = cam.z - z;
        }
      } catch {
        /* camera not readable in this environment */
      }
      const len = Math.hypot(dx, dz) || 1;
      const reach = 150;
      graph.cameraPosition(
        { x: x + (dx / len) * reach, y: y + 70, z: z + (dz / len) * reach },
        { x, y, z },
        900,
      );
    },
    [neighbourIds],
  );

  /** Floors: one translucent disc per level that has something on it. */
  const rebuildFloors = useCallback(() => {
    const graph = graphRef.current as any;
    if (!graph) return;
    try {
      const scene = graph.scene();
      if (floorsRef.current) {
        scene.remove(floorsRef.current);
        floorsRef.current.traverse((child: any) => {
          child.geometry?.dispose?.();
          child.material?.map?.dispose?.();
          child.material?.dispose?.();
        });
      }
      const t = themeRef.current;
      const present = new Set<NetworkTier>();
      nodeMapRef.current.forEach((n) => present.add(nodeTier(n)));
      const group = new THREE.Group();
      const radius = floorRadiusRef.current;
      const tint = t.isDark ? '#ffffff' : '#0f172a';
      TIER_ORDER.filter((tier) => present.has(tier)).forEach((tier) => {
        const y = TIER_HEIGHT[tier] - 14;
        const disc = new THREE.Mesh(
          new THREE.CircleGeometry(1, 72),
          new THREE.MeshBasicMaterial({
            color: tint,
            transparent: true,
            opacity: t.isDark ? 0.035 : 0.04,
            side: THREE.DoubleSide,
            depthWrite: false,
          }),
        );
        disc.rotation.x = -Math.PI / 2;
        disc.position.y = y;
        disc.scale.set(radius, radius, 1);
        disc.name = 'floor';
        const rim = new THREE.Mesh(
          new THREE.RingGeometry(0.992, 1, 96),
          new THREE.MeshBasicMaterial({ color: tint, transparent: true, opacity: 0.22, side: THREE.DoubleSide, depthWrite: false }),
        );
        rim.rotation.x = -Math.PI / 2;
        rim.position.y = y;
        rim.scale.set(radius, radius, 1);
        rim.name = 'floor';
        group.add(disc, rim);
        const label = makeLabel(TIER_LABELS[tier].toUpperCase(), t.mutedText, null, 10);
        if (label) {
          label.position.set(-radius - 4, y + 6, 0);
          label.center.set(1, 0.5);
          label.name = 'floor-label';
          group.add(label);
        }
      });
      scene.add(group);
      floorsRef.current = group;
    } catch {
      /* scene unavailable (test double) */
    }
  }, []);

  const resizeFloors = useCallback(() => {
    const radius = spreadRadius();
    if (Math.abs(radius - floorRadiusRef.current) < 6) return;
    floorRadiusRef.current = radius;
    floorsRef.current?.children.forEach((child: any) => {
      if (child.name === 'floor') child.scale.set(radius, radius, 1);
      else if (child.name === 'floor-label') child.position.x = -radius - 4;
    });
  }, [spreadRadius]);

  /** Push colours, link styles and node shapes into the graph (no layout restart). */
  const applyStyle = useCallback(() => {
    const graph = graphRef.current as any;
    if (!graph) return;
    const t = themeRef.current;
    const sel = selectedRef.current;
    const near = neighbourIds(sel);
    const showLabels = nodeMapRef.current.size <= LABEL_NODE_LIMIT;

    const linkTone = (l: any): string => {
      if (l.kind === 'vpn_tunnel') {
        const a = nodeMapRef.current.get(endId(l.source));
        const b = nodeMapRef.current.get(endId(l.target));
        const vpn = a?.type === 'vpn' ? a : b?.type === 'vpn' ? b : undefined;
        if (vpn?.status === 'attention' || vpn?.status === 'error') return t.red;
        if (vpn?.status === 'warning') return t.amber;
        return t.emerald;
      }
      return edgeColor(l, t);
    };
    const touchesSelection = (l: any) => sel !== null && (endId(l.source) === sel || endId(l.target) === sel);
    const flowing = (l: any): number => {
      if (l.kind === 'vpn_tunnel') return linkTone(l) === t.red ? 0 : 3;
      if (l.kind === 'talks_to' || l.kind === 'exposed_to_internet') return 2;
      if (l.kind === 'routes_to') return 1;
      return 0;
    };

    graph
      .backgroundColor(t.background)
      .nodeThreeObject((n: SimNode) => {
        const obj = buildNodeObject(n, t, showLabels || ALWAYS_LABELLED.has(n.type) || n.id === sel);
        setDim(obj, sel !== null && !near.has(n.id), n.id === sel);
        return obj;
      })
      .linkColor((l: any) => {
        const tone = linkTone(l);
        if (sel === null) return tone;
        return touchesSelection(l) ? tone : t.isDark ? 'rgba(148,163,184,0.10)' : 'rgba(71,85,105,0.10)';
      })
      .linkWidth((l: any) => (touchesSelection(l) ? Math.max(LINK_WIDTH[l.kind] ?? 0.3, 1.1) : LINK_WIDTH[l.kind] ?? 0.3))
      .linkVisibility((l: any) => l.kind !== 'monitors' || monitoringRef.current || touchesSelection(l))
      .linkCurvature((l: any) => (l.kind === 'talks_to' ? 0.3 : 0))
      .linkDirectionalArrowLength((l: any) =>
        l.kind === 'member_of' || l.kind === 'part_of' || l.kind === 'vpn_tunnel' || l.kind === 'monitors' ? 0 : 3.2,
      )
      .linkDirectionalParticles(prefersReducedMotion() ? 0 : flowing)
      .linkDirectionalParticleColor(linkTone);
  }, [neighbourIds]);

  useImperativeHandle(ref, () => ({
    fit: () => frameAll(700),
  }));

  // -- create once, destroy on unmount ---------------------------------------

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const graph = new ForceGraph3D(host, { controlType: 'orbit', rendererConfig: { antialias: true, alpha: false } });
    // A fresh graph knows nothing yet (React StrictMode mounts twice in dev):
    // make the data effect below hand it the data again.
    shapeKeyRef.current = '';
    floorsRef.current = null;
    framedRef.current = false;
    graph
      .showNavInfo(false)
      .nodeLabel(() => '')
      .nodeThreeObjectExtend(false)
      .linkOpacity(0.6)
      .linkDirectionalArrowRelPos(0.92)
      .linkDirectionalParticleWidth(1.9)
      .linkDirectionalParticleSpeed(0.006)
      .enableNodeDrag(true)
      .warmupTicks(90)
      .cooldownTicks(120)
      .cooldownTime(5000)
      .onEngineTick(() => resizeFloors())
      .onEngineStop(() => {
        resizeFloors();
        if (!framedRef.current) {
          framedRef.current = true;
          frameAll(900);
        }
      })
      .onNodeClick((n: any) => callbacksRef.current.onSelect(n))
      .onBackgroundClick(() => callbacksRef.current.onSelect(null))
      .onNodeHover((n: any) => {
        host.style.cursor = n ? 'pointer' : 'grab';
        callbacksRef.current.onHover?.(n);
      });

    // Cap the pixel ratio on small screens: WebGL at DPR 3 on a phone melts batteries.
    try {
      const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
      const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
      graph.renderer()?.setPixelRatio(isMobile ? 1 : Math.min(dpr, 2));
    } catch {
      /* renderer not ready in this environment */
    }

    try {
      const g = graph as any;
      g.d3Force('charge')?.strength?.(-150)?.distanceMax?.(320);
      g.d3Force('link')
        ?.distance?.((l: any) => LINK_DISTANCE[l.kind] ?? 90)
        ?.strength?.((l: any) => LINK_STRENGTH[l.kind] ?? 0.2);
      g.d3Force('gravity', gravityXZ(0.075));
    } catch {
      /* force accessors unavailable (test double) */
    }

    // Slow turntable until the first touch, so the depth reads immediately.
    let stopSpin = () => undefined as void;
    try {
      const controls: any = graph.controls();
      if (controls && !prefersReducedMotion()) {
        controls.autoRotate = true;
        controls.autoRotateSpeed = 0.45;
        stopSpin = () => {
          controls.autoRotate = false;
        };
        host.addEventListener('pointerdown', stopSpin, { once: true });
        host.addEventListener('wheel', stopSpin, { once: true, passive: true });
      }
    } catch {
      /* controls unavailable (test double) */
    }

    // Pulse rings breathe; everything else is static.
    let frame = 0;
    const still = prefersReducedMotion() || typeof requestAnimationFrame !== 'function';
    const tick = (time: number) => {
      const wave = 1 + 0.22 * Math.sin(time / 420);
      nodeMapRef.current.forEach((n) => {
        const pulse = n.__threeObj?.getObjectByName?.('pulse');
        if (pulse) pulse.scale.set(wave, wave, 1);
      });
      frame = requestAnimationFrame(tick);
    };
    if (!still) frame = requestAnimationFrame(tick);

    graphRef.current = graph;
    // Dev builds only: lets the browser console and preview checks read the scene.
    if (import.meta.env.DEV) (window as any).__resilaiNetworkGraph = { graph, nodes: () => Array.from(nodeMapRef.current.values()) };
    return () => {
      if (frame) cancelAnimationFrame(frame);
      host.removeEventListener('pointerdown', stopSpin);
      host.removeEventListener('wheel', stopSpin);
      graph._destructor();
      graphRef.current = null;
    };
    // The graph is created once; callbacks reach current values through refs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // -- data -------------------------------------------------------------------
  // Node objects are reused across refreshes so a live update never throws the
  // layout away: positions persist and only genuinely new things settle in.
  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;
    const previous = nodeMapRef.current;
    const next = new Map<string, SimNode>();
    const simNodes = nodes.map((n) => {
      const existing = previous.get(n.id);
      const sim: SimNode = existing ? Object.assign(existing, n) : { ...n };
      sim.fy = TIER_HEIGHT[nodeTier(n)];
      next.set(n.id, sim);
      return sim;
    });
    nodeMapRef.current = next;

    const shapeKey = `${nodes.map((n) => n.id).sort().join('|')}#${edges
      .map((e) => `${e.source}>${e.target}>${e.kind}`)
      .sort()
      .join('|')}`;
    if (shapeKey !== shapeKeyRef.current) {
      shapeKeyRef.current = shapeKey;
      graph.graphData({ nodes: simNodes, links: edges.map((e) => ({ ...e })) });
      // Start from the three-quarter view straight away; the settled layout re-frames it.
      if (!framedRef.current) frameAll(0);
    }
    applyStyle();
    rebuildFloors();
  }, [nodes, edges, applyStyle, rebuildFloors, frameAll]);

  useEffect(() => {
    graphRef.current?.width(width).height(height);
  }, [width, height]);

  // -- theme, monitoring links -------------------------------------------------
  useEffect(() => {
    applyStyle();
    rebuildFloors();
  }, [theme, showMonitoring, applyStyle, rebuildFloors]);

  // -- selection: dim everything unrelated, then fly there ---------------------
  useEffect(() => {
    applyStyle();
    if (!selectedId) return;
    const node = nodeMapRef.current.get(selectedId);
    if (node) flyTo(node);
  }, [selectedId, applyStyle, flyTo]);

  return <div ref={hostRef} data-testid="network-graph-3d" style={{ width, height, cursor: 'grab' }} />;
});

export default Graph3D;
