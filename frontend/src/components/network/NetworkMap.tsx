import React, { Suspense, lazy, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Box, Download, Globe, Loader2, Maximize2, PlugZap, RefreshCw, ShieldAlert, Square } from 'lucide-react';
import { Button } from '../ui';
import { useActiveOrgId } from '../../hooks/useActiveOrgId';
import {
  downloadReportById,
  generateReport,
  getNetworkTopology,
  type NetworkNodeStatus,
  type NetworkTopologyNode,
  type NetworkTopologyResponse,
  type NetworkZone,
} from '../../api';
import { Graph2D, type GraphHandle } from './map/Graph2D';
import { NodeDetailPanel } from './map/NodeDetailPanel';
import {
  STATUS_DOT_CLASS,
  STATUS_LABELS,
  STATUS_ORDER,
  ZONE_COLORS,
  ZONE_LABELS,
  ZONE_ORDER,
  describeNode,
  formatRelative,
  readThemeColors,
  type ThemeColors,
} from './map/palette';

// three.js only ships to the browser once someone flips to 3D.
const Graph3D = lazy(() => import('./map/Graph3D'));

type ViewMode = '2d' | '3d';

function webglAvailable(): boolean {
  if (typeof document === 'undefined') return false;
  try {
    const canvas = document.createElement('canvas');
    return Boolean(canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
  } catch {
    return false;
  }
}

function useThemeColors(): ThemeColors {
  const [theme, setTheme] = useState<ThemeColors>(() => readThemeColors());
  useEffect(() => {
    if (typeof MutationObserver === 'undefined') return;
    const observer = new MutationObserver(() => setTheme(readThemeColors()));
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class', 'data-theme'] });
    return () => observer.disconnect();
  }, []);
  return theme;
}

function useElementSize<T extends HTMLElement>(fallbackHeight: number) {
  // Callback ref: the host div mounts only after loading finishes, so a plain
  // ref + effect would measure nothing. Re-measure whenever the element changes.
  const [el, setEl] = useState<T | null>(null);
  const [size, setSize] = useState({ width: 800, height: fallbackHeight });
  useLayoutEffect(() => {
    if (!el) return;
    const measure = () => {
      const rect = el.getBoundingClientRect();
      setSize({ width: Math.max(rect.width || el.clientWidth || 800, 240), height: Math.max(rect.height || fallbackHeight, 240) });
    };
    measure();
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', measure);
      return () => window.removeEventListener('resize', measure);
    }
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, [el, fallbackHeight]);
  return { ref: setEl as (node: T | null) => void, size };
}

export interface NetworkMapProps {
  /** Override the active organisation (tests, embeds). */
  orgId?: string;
}

export function NetworkMap({ orgId: orgIdProp }: NetworkMapProps) {
  const activeOrgId = useActiveOrgId();
  const orgId = orgIdProp || activeOrgId;
  const theme = useThemeColors();

  const [data, setData] = useState<NetworkTopologyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  const [view, setView] = useState<ViewMode>('2d');
  const [webglMissing, setWebglMissing] = useState(false);
  const [zoneFilter, setZoneFilter] = useState<Set<NetworkZone>>(new Set());
  const [statusFilter, setStatusFilter] = useState<Set<NetworkNodeStatus>>(new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hovered, setHovered] = useState<NetworkTopologyNode | null>(null);
  const [pointer, setPointer] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [exporting, setExporting] = useState(false);

  const graphRef = useRef<GraphHandle | null>(null);
  const { ref: canvasHostRef, size } = useElementSize<HTMLDivElement>(560);

  useEffect(() => {
    if (!orgId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    getNetworkTopology(orgId)
      .then((res) => {
        if (cancelled) return;
        setData(res);
        setSelectedId(null);
      })
      .catch((err: any) => {
        if (cancelled) return;
        setError(err?.message || 'Could not load the network map.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [orgId, refreshTick]);

  const nodesById = useMemo(() => {
    const map: Record<string, NetworkTopologyNode> = {};
    (data?.nodes || []).forEach((n) => {
      map[n.id] = n;
    });
    return map;
  }, [data]);

  const visibleNodes = useMemo(() => {
    const nodes = data?.nodes || [];
    return nodes.filter(
      (n) => (zoneFilter.size === 0 || zoneFilter.has(n.zone)) && (statusFilter.size === 0 || statusFilter.has(n.status)),
    );
  }, [data, zoneFilter, statusFilter]);

  const visibleEdges = useMemo(() => {
    const ids = new Set(visibleNodes.map((n) => n.id));
    return (data?.edges || []).filter((e) => ids.has(e.source) && ids.has(e.target));
  }, [data, visibleNodes]);

  const zonesPresent = useMemo(() => ZONE_ORDER.filter((z) => (data?.summary?.by_zone?.[z] || 0) > 0), [data]);
  const statusesPresent = useMemo(() => STATUS_ORDER.filter((s) => (data?.summary?.by_status?.[s] || 0) > 0), [data]);

  const selected = selectedId ? nodesById[selectedId] || null : null;

  const toggleZone = (zone: NetworkZone) =>
    setZoneFilter((prev) => {
      const next = new Set(prev);
      if (next.has(zone)) next.delete(zone);
      else next.add(zone);
      return next;
    });
  const toggleStatus = (status: NetworkNodeStatus) =>
    setStatusFilter((prev) => {
      const next = new Set(prev);
      if (next.has(status)) next.delete(status);
      else next.add(status);
      return next;
    });

  const switchView = (mode: ViewMode) => {
    if (mode === '3d' && !webglAvailable()) {
      setWebglMissing(true);
      setView('2d');
      return;
    }
    setWebglMissing(false);
    setView(mode);
  };

  const handleSelect = useCallback((node: NetworkTopologyNode | null) => {
    setSelectedId(node ? node.id : null);
  }, []);

  const handleExportBossReport = async () => {
    if (!orgId) return;
    setExporting(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const generated = await generateReport({
        organization_id: orgId,
        org_id: orgId,
        report_type: 'boss_report',
        format: 'pdf',
        title: `Monday Morning Boss Report ${today}`,
      } as any);
      const blob = await downloadReportById(generated.id, generated.download_url);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ResilAI_Monday_Boss_Report_${today}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      window.alert(err?.message || 'Could not generate the boss report. Connect a system or try again.');
    } finally {
      setExporting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // States
  // ---------------------------------------------------------------------------

  if (!orgId) {
    return (
      <div className="rounded-2xl border border-outline-variant bg-surface-container-low p-8 text-center text-on-surface-variant">
        Select an organisation to see its network.
      </div>
    );
  }

  if (loading && !data) {
    return (
      <div
        data-testid="network-map-loading"
        className="flex h-[420px] items-center justify-center rounded-2xl border border-outline-variant bg-surface-container-low text-on-surface-variant"
      >
        <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Drawing your network…
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-outline-variant bg-surface-container-low p-8 text-center">
        <p className="font-bold text-on-surface">We could not load the network map.</p>
        <p className="mt-1 text-sm text-on-surface-variant">{error}</p>
        <Button className="mt-4" variant="outline" size="sm" onClick={() => setRefreshTick((t) => t + 1)}>
          <RefreshCw className="mr-1.5 h-4 w-4" /> Try again
        </Button>
      </div>
    );
  }

  if (!data || data.summary.empty || data.nodes.length === 0) {
    return (
      <div
        data-testid="network-map-empty"
        className="rounded-2xl border border-dashed border-outline-variant bg-surface-container-low p-10 text-center"
      >
        <PlugZap className="mx-auto h-10 w-10 text-on-surface-variant" />
        <h3 className="mt-3 text-lg font-extrabold text-on-surface">Nothing is connected yet</h3>
        <p className="mx-auto mt-1 max-w-md text-sm text-on-surface-variant">
          This map only shows systems we can actually see. Connect Microsoft 365, AWS, your backup tool or
          another system and the real picture appears here, with every link between them.
        </p>
        <Link
          to="/connectors"
          className="mt-5 inline-flex items-center rounded-xl bg-on-surface px-4 py-2 text-sm font-bold text-surface-container-lowest hover:opacity-90"
        >
          Connect a system
        </Link>
      </div>
    );
  }

  const summary = data.summary;
  const graphProps = {
    nodes: visibleNodes,
    edges: visibleEdges,
    width: size.width,
    height: size.height,
    theme,
    selectedId,
    onSelect: handleSelect,
    onHover: setHovered,
  };

  return (
    <div data-testid="network-map" className="space-y-4 text-on-surface">
      {/* Summary strip */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Systems on the map" value={summary.node_count} />
        <Stat
          label="Need attention"
          value={summary.attention}
          tone={summary.attention > 0 ? 'red' : 'emerald'}
          icon={<ShieldAlert className="h-4 w-4" />}
        />
        <Stat
          label="Reachable from the internet"
          value={summary.internet_exposed}
          tone={summary.internet_exposed > 0 ? 'red' : 'emerald'}
          icon={<Globe className="h-4 w-4" />}
        />
        <Stat label="Connected systems" value={summary.connectors} icon={<PlugZap className="h-4 w-4" />} />
      </div>

      {data.demo && (
        <p className="rounded-xl border border-outline-variant bg-surface-container px-3 py-2 text-xs text-on-surface-variant">
          Demo workspace: this map is built from telemetry recorded in the demo organisation's real AWS and
          Microsoft accounts, the same way it would be for yours.
        </p>
      )}

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Filter by zone">
          {zonesPresent.map((zone) => {
            const active = zoneFilter.size === 0 || zoneFilter.has(zone);
            return (
              <button
                key={zone}
                type="button"
                onClick={() => toggleZone(zone)}
                aria-pressed={zoneFilter.has(zone)}
                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold transition ${
                  active
                    ? 'border-outline-variant bg-surface-container-high text-on-surface'
                    : 'border-outline-variant bg-transparent text-on-surface-variant opacity-50'
                }`}
              >
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: ZONE_COLORS[zone] }} aria-hidden />
                {ZONE_LABELS[zone]}
                <span className="text-on-surface-variant">{summary.by_zone[zone]}</span>
              </button>
            );
          })}
        </div>
        <span className="hidden h-5 w-px bg-outline-variant md:block" aria-hidden />
        <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Filter by status">
          {statusesPresent.map((status) => {
            const active = statusFilter.size === 0 || statusFilter.has(status);
            return (
              <button
                key={status}
                type="button"
                onClick={() => toggleStatus(status)}
                aria-pressed={statusFilter.has(status)}
                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold transition ${
                  active
                    ? 'border-outline-variant bg-surface-container-high text-on-surface'
                    : 'border-outline-variant bg-transparent text-on-surface-variant opacity-50'
                }`}
              >
                <span className={`h-2 w-2 rounded-full ${STATUS_DOT_CLASS[status]}`} aria-hidden />
                {STATUS_LABELS[status]}
                <span className="text-on-surface-variant">{summary.by_status[status]}</span>
              </button>
            );
          })}
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <div className="inline-flex rounded-lg border border-outline-variant p-0.5" role="group" aria-label="View mode">
            <button
              type="button"
              onClick={() => switchView('2d')}
              aria-pressed={view === '2d'}
              className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-bold ${
                view === '2d' ? 'bg-surface-container-high text-on-surface' : 'text-on-surface-variant'
              }`}
            >
              <Square className="h-3.5 w-3.5" /> 2D
            </button>
            <button
              type="button"
              onClick={() => switchView('3d')}
              aria-pressed={view === '3d'}
              className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-bold ${
                view === '3d' ? 'bg-surface-container-high text-on-surface' : 'text-on-surface-variant'
              }`}
            >
              <Box className="h-3.5 w-3.5" /> 3D
            </button>
          </div>
          <Button variant="outline" size="sm" onClick={() => graphRef.current?.fit()} aria-label="Fit to screen">
            <Maximize2 className="mr-1 h-3.5 w-3.5" /> Fit
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setRefreshTick((t) => t + 1)}
            aria-label="Refresh map"
            disabled={loading}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          <Button variant="primary" size="sm" onClick={handleExportBossReport} loading={exporting}>
            <Download className="mr-1 h-3.5 w-3.5" /> Boss report
          </Button>
        </div>
      </div>

      {webglMissing && (
        <p className="rounded-xl border border-drift-amber/40 bg-drift-amber/10 px-3 py-2 text-xs font-semibold text-drift-amber">
          3D needs WebGL, which this browser or device does not offer. Showing the 2D map instead.
        </p>
      )}

      {/* Canvas + panel */}
      <div className={`grid gap-4 ${selected ? 'md:grid-cols-[minmax(0,1fr)_340px]' : 'md:grid-cols-1'}`}>
        <div
          ref={canvasHostRef}
          data-testid="network-map-canvas"
          className="relative h-[480px] overflow-hidden rounded-2xl border border-outline-variant bg-surface-container-lowest md:h-[600px]"
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            setPointer({ x: e.clientX - rect.left, y: e.clientY - rect.top });
          }}
          onMouseLeave={() => setHovered(null)}
        >
          {view === '3d' ? (
            <Suspense
              fallback={
                <div
                  data-testid="network-map-3d-loading"
                  className="flex h-full items-center justify-center text-sm text-on-surface-variant"
                >
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading the 3D view…
                </div>
              }
            >
              <Graph3D ref={graphRef} {...graphProps} />
            </Suspense>
          ) : (
            <Graph2D ref={graphRef} {...graphProps} />
          )}

          {hovered && !selected && (
            <div
              role="tooltip"
              className="pointer-events-none absolute z-10 max-w-[240px] rounded-lg border border-outline-variant bg-surface-container-low px-2.5 py-1.5 text-xs shadow-lg"
              style={{ left: Math.min(pointer.x + 12, size.width - 250), top: pointer.y + 12 }}
            >
              <p className="font-bold text-on-surface">{hovered.label}</p>
              <p className="text-on-surface-variant">{describeNode(hovered)}</p>
              <p className="mt-0.5 text-on-surface-variant">
                {STATUS_LABELS[hovered.status]}
                {hovered.meta?.issues?.length ? ` · ${hovered.meta.issues.length} open` : ''}
              </p>
            </div>
          )}

          {/* Legend */}
          <div
            data-testid="network-map-legend"
            className="absolute bottom-3 left-3 hidden max-w-[260px] rounded-xl border border-outline-variant bg-surface-container-low/90 p-2.5 text-[11px] backdrop-blur sm:block"
          >
            <p className="mb-1 font-bold uppercase tracking-wide text-on-surface-variant">Legend</p>
            <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
              {zonesPresent.map((zone) => (
                <div key={zone} className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: ZONE_COLORS[zone] }} aria-hidden />
                  <span className="text-on-surface-variant">{ZONE_LABELS[zone]}</span>
                </div>
              ))}
            </div>
            <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 border-t border-outline-variant pt-1.5">
              <span className="flex items-center gap-1 text-on-surface-variant">
                <span className="h-2 w-2 rounded-full border-2 border-ready-emerald" aria-hidden /> fine
              </span>
              <span className="flex items-center gap-1 text-on-surface-variant">
                <span className="h-2 w-2 rounded-full border-2 border-drift-amber" aria-hidden /> worth a look
              </span>
              <span className="flex items-center gap-1 text-on-surface-variant">
                <span className="h-2 w-2 rounded-full border-2 border-red-500" aria-hidden /> needs attention
              </span>
              <span className="flex items-center gap-1 text-on-surface-variant">
                <span className="inline-block h-0 w-4 border-t-2 border-dashed border-red-500" aria-hidden /> open to internet
              </span>
            </div>
          </div>

          <p className="absolute right-3 top-3 rounded-md bg-surface-container-low/80 px-2 py-0.5 text-[10px] text-on-surface-variant">
            Updated {formatRelative(data.generated_at)} · {visibleNodes.length}/{summary.node_count} shown
          </p>
        </div>

        {selected && (
          <div
            className="fixed inset-x-0 bottom-0 z-40 max-h-[70vh] overflow-hidden rounded-t-2xl border border-outline-variant shadow-2xl md:static md:z-auto md:max-h-none md:h-[600px] md:rounded-2xl md:shadow-none"
          >
            <NodeDetailPanel
              node={selected}
              edges={data.edges}
              nodesById={nodesById}
              onClose={() => setSelectedId(null)}
              onJump={(id) => setSelectedId(id)}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
  icon,
}: {
  label: string;
  value: number;
  tone?: 'red' | 'emerald';
  icon?: React.ReactNode;
}) {
  const toneClass = tone === 'red' ? 'text-red-500' : tone === 'emerald' ? 'text-ready-emerald' : 'text-on-surface';
  return (
    <div className="rounded-xl border border-outline-variant bg-surface-container-low p-3">
      <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide text-on-surface-variant">
        {icon} {label}
      </p>
      <p className={`mt-1 text-2xl font-extrabold ${toneClass}`}>{value}</p>
    </div>
  );
}

export default NetworkMap;
