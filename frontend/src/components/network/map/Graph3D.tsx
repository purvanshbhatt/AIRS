import React, { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import ForceGraph3D, { type ForceGraph3DInstance } from '3d-force-graph';
import { ZONE_COLORS, edgeColor, nodeRadius, statusColor } from './palette';
import type { GraphHandle, GraphViewProps } from './Graph2D';

/**
 * 3D view, driven imperatively through `3d-force-graph`.
 *
 * NetworkMap loads this module with React.lazy, so three.js only ships when a
 * user flips the toggle. The React wrapper (`react-force-graph-3d`) is avoided
 * on purpose: the Vite manualChunks rule groups every module whose path
 * contains "react" into the eager vendor-react chunk, which would drag
 * three.js into the main download.
 */
export const Graph3D = forwardRef<GraphHandle, GraphViewProps>(function Graph3D(
  { nodes, edges, width, height, theme, selectedId, onSelect, onHover },
  ref,
) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const graphRef = useRef<ForceGraph3DInstance | null>(null);
  const callbacksRef = useRef({ onSelect, onHover });
  callbacksRef.current = { onSelect, onHover };

  useImperativeHandle(ref, () => ({
    fit: () => graphRef.current?.zoomToFit(600, 60),
  }));

  // Create once, destroy on unmount.
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const graph = new ForceGraph3D(host, { controlType: 'orbit', rendererConfig: { antialias: true, alpha: false } });
    graph
      .showNavInfo(false)
      .nodeRelSize(3)
      .nodeOpacity(0.95)
      .nodeResolution(12)
      .nodeVal((n: any) => nodeRadius(n) ** 2)
      .nodeLabel((n: any) => `${n.label}`)
      .linkOpacity(0.55)
      .linkWidth((l: any) => (l.kind === 'exposed_to_internet' ? 1.2 : 0.4))
      .linkDirectionalArrowLength(3)
      .linkDirectionalArrowRelPos(0.9)
      .linkDirectionalParticles((l: any) => (l.kind === 'exposed_to_internet' ? 2 : 0))
      .linkDirectionalParticleWidth(1.6)
      .enableNodeDrag(true)
      .onEngineStop(() => graph.zoomToFit(500, 60))
      .onNodeClick((n: any) => callbacksRef.current.onSelect(n))
      .onBackgroundClick(() => callbacksRef.current.onSelect(null))
      .onNodeHover((n: any) => callbacksRef.current.onHover?.(n));

    // Cap the pixel ratio on small screens: WebGL at DPR 3 on a phone melts batteries.
    try {
      const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
      const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
      graph.renderer()?.setPixelRatio(isMobile ? 1 : Math.min(dpr, 2));
    } catch {
      /* renderer not ready in this environment */
    }

    // Same spread as the 2D view so the two layouts feel like one map.
    try {
      (graph as any).d3Force('charge')?.strength?.(-160)?.distanceMax?.(300);
      (graph as any).d3Force('link')?.distance?.((l: any) => (l.kind === 'monitors' ? 60 : 45));
    } catch {
      /* force accessors unavailable (test double) */
    }

    graphRef.current = graph;
    return () => {
      graph._destructor();
      graphRef.current = null;
    };
  }, []);

  // Data: copy so the library's mutations (x, y, z, vx...) never leak into the API payload.
  useEffect(() => {
    graphRef.current?.graphData({
      nodes: nodes.map((n) => ({ ...n })),
      links: edges.map((e) => ({ ...e })),
    });
  }, [nodes, edges]);

  useEffect(() => {
    graphRef.current?.width(width).height(height);
  }, [width, height]);

  // Theme and selection colours.
  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;
    graph
      .backgroundColor(theme.background)
      .nodeColor((n: any) =>
        n.id === selectedId
          ? theme.text
          : n.status === 'attention' || n.status === 'error'
            ? statusColor(n.status, theme)
            : ZONE_COLORS[n.zone as keyof typeof ZONE_COLORS] || theme.mutedText,
      )
      .linkColor((l: any) => edgeColor(l, theme));
  }, [theme, selectedId]);

  return <div ref={hostRef} data-testid="network-graph-3d" style={{ width, height }} />;
});

export default Graph3D;
