import React, { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { ForceGraphMethods } from 'react-force-graph-2d';
import type { NetworkTopologyEdge, NetworkTopologyNode } from '../../../api';
import { ZONE_COLORS, edgeColor, nodeRadius, statusColor, type ThemeColors } from './palette';

export interface GraphHandle {
  fit: () => void;
}

export interface GraphViewProps {
  nodes: NetworkTopologyNode[];
  edges: NetworkTopologyEdge[];
  width: number;
  height: number;
  theme: ThemeColors;
  selectedId: string | null;
  onSelect: (node: NetworkTopologyNode | null) => void;
  onHover?: (node: NetworkTopologyNode | null) => void;
}

type GNode = NetworkTopologyNode & { x?: number; y?: number };
type GLink = NetworkTopologyEdge & { source: any; target: any };

/**
 * 2D force-directed canvas. Pan/zoom/drag come from the library; node glyphs
 * are drawn by hand so zone (fill), status (ring) and label all read at a glance.
 */
export const Graph2D = forwardRef<GraphHandle, GraphViewProps>(function Graph2D(
  { nodes, edges, width, height, theme, selectedId, onSelect, onHover },
  ref,
) {
  const fgRef = useRef<ForceGraphMethods<any, any> | undefined>(undefined);

  // The library mutates node objects (x, y, vx...). Copy so the API payload stays pristine.
  const graphData = useMemo(
    () => ({
      nodes: nodes.map((n) => ({ ...n })) as GNode[],
      links: edges.map((e) => ({ ...e })) as GLink[],
    }),
    [nodes, edges],
  );

  useImperativeHandle(ref, () => ({
    fit: () => fgRef.current?.zoomToFit(500, 48),
  }));

  // Spread the layout: the d3 defaults pack two dozen nodes into a tight blob,
  // which makes every glyph look huge once zoomToFit runs.
  useEffect(() => {
    const fg = fgRef.current as any;
    if (!fg?.d3Force) return;
    fg.d3Force('charge')?.strength?.(-220)?.distanceMax?.(260);
    fg.d3Force('link')?.distance?.((l: GLink) => (l.kind === 'monitors' ? 55 : 40));
    fg.d3ReheatSimulation?.();
  }, [graphData]);

  const paintNode = useCallback(
    (node: GNode, ctx: CanvasRenderingContext2D, scale: number) => {
      const r = nodeRadius(node);
      const x = node.x ?? 0;
      const y = node.y ?? 0;
      const fill = ZONE_COLORS[node.zone] || theme.mutedText;
      const ring = statusColor(node.status, theme);
      const isSelected = node.id === selectedId;

      if (isSelected) {
        ctx.beginPath();
        ctx.arc(x, y, r + 4, 0, 2 * Math.PI);
        ctx.fillStyle = theme.isDark ? 'rgba(255,255,255,0.18)' : 'rgba(15,23,42,0.12)';
        ctx.fill();
      }

      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.fillStyle = fill;
      ctx.fill();
      ctx.lineWidth = node.status === 'attention' || node.status === 'error' ? 2.2 : 1.4;
      ctx.strokeStyle = ring;
      ctx.stroke();

      if (node.type === 'internet') {
        // Hollow globe-ish ring so the internet reads as "outside".
        ctx.beginPath();
        ctx.arc(x, y, r * 0.55, 0, 2 * Math.PI);
        ctx.strokeStyle = theme.background;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }

      // Labels only once zoomed in enough to be legible, or when selected.
      if (scale > 0.9 || isSelected) {
        const fontSize = Math.max(10 / scale, 2.2);
        ctx.font = `${isSelected ? 600 : 500} ${fontSize}px ui-sans-serif, system-ui, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillStyle = theme.text;
        const label = node.label.length > 28 ? `${node.label.slice(0, 26)}…` : node.label;
        ctx.fillText(label, x, y + r + 2 / scale);
      }
    },
    [selectedId, theme],
  );

  const paintPointerArea = useCallback((node: GNode, color: string, ctx: CanvasRenderingContext2D) => {
    ctx.beginPath();
    ctx.arc(node.x ?? 0, node.y ?? 0, nodeRadius(node) + 4, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
  }, []);

  return (
    <ForceGraph2D
      ref={fgRef as any}
      width={width}
      height={height}
      graphData={graphData}
      backgroundColor={theme.background}
      nodeRelSize={1}
      nodeVal={(n: GNode) => nodeRadius(n) ** 2}
      nodeLabel={() => ''}
      nodeCanvasObject={paintNode as any}
      nodePointerAreaPaint={paintPointerArea as any}
      linkColor={(l: GLink) => edgeColor(l, theme)}
      linkWidth={(l: GLink) => (l.kind === 'exposed_to_internet' ? 2 : 1)}
      linkLineDash={(l: GLink) => (l.kind === 'exposed_to_internet' ? [4, 3] : null)}
      linkDirectionalArrowLength={4}
      linkDirectionalArrowRelPos={0.9}
      linkDirectionalParticles={(l: GLink) => (l.kind === 'exposed_to_internet' ? 2 : 0)}
      linkDirectionalParticleWidth={2.5}
      linkDirectionalParticleColor={() => theme.red}
      d3VelocityDecay={0.35}
      cooldownTicks={120}
      onEngineStop={() => fgRef.current?.zoomToFit(400, 48)}
      onNodeClick={(n: GNode) => onSelect(n)}
      onBackgroundClick={() => onSelect(null)}
      onNodeHover={(n: GNode | null) => onHover?.(n)}
      enableNodeDrag
    />
  );
});

export default Graph2D;
