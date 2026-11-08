import React from 'react';
import { X, ShieldAlert, Eye, Clock, Link2 } from 'lucide-react';
import type { NetworkTopologyEdge, NetworkTopologyNode } from '../../../api';
import {
  EDGE_LABELS,
  STATUS_DOT_CLASS,
  STATUS_LABELS,
  STATUS_TEXT_CLASS,
  TYPE_LABELS,
  ZONE_COLORS,
  ZONE_LABELS,
  describeNode,
  formatRelative,
} from './palette';

export interface NodeDetailPanelProps {
  node: NetworkTopologyNode;
  edges: NetworkTopologyEdge[];
  nodesById: Record<string, NetworkTopologyNode>;
  onClose: () => void;
  onJump: (nodeId: string) => void;
}

/** Fields worth showing a business owner, in plain words. */
const META_LABELS: Record<string, string> = {
  instance_type: 'Size',
  platform: 'Platform',
  state: 'State',
  role: 'Role',
  department: 'Department',
  private_ip: 'Private address',
  public_ip: 'Public address',
  ip_address: 'Address',
  operating_system: 'Operating system',
  os_version: 'OS version',
  cloud_provider: 'Cloud',
  compliance_state: 'Compliance',
  bitlocker_status: 'Disk encryption',
  mfa_enforced: 'Multi-factor sign-in',
  account_enabled: 'Account enabled',
  last_sign_in: 'Last sign-in',
  access_key_active: 'Access key active',
  last_successful_backup: 'Last good backup',
  backup_type: 'Backup type',
  ssm_managed: 'Remotely managed',
  imdsv2: 'Instance metadata',
  ebs_encrypted: 'Disk encrypted',
  connector_type: 'Connector',
  error_message: 'Last error',
};

function formatValue(key: string, value: unknown): string {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (key === 'last_sign_in' || key === 'last_successful_backup') return formatRelative(String(value));
  return String(value);
}

export function NodeDetailPanel({ node, edges, nodesById, onClose, onJump }: NodeDetailPanelProps) {
  const issues = node.meta?.issues || [];
  const seenBy = node.meta?.seen_by || [];
  const related = edges.filter((e) => e.source === node.id || e.target === node.id);
  const metaEntries = Object.entries(node.meta || {}).filter(
    ([key, value]) => META_LABELS[key] && value !== null && value !== undefined && value !== '',
  );

  return (
    <aside
      data-testid="network-node-panel"
      aria-label={`Details for ${node.label}`}
      className="flex h-full flex-col bg-surface-container-low text-on-surface"
    >
      <header className="flex items-start gap-3 border-b border-outline-variant p-4">
        <span
          className="mt-1 h-3.5 w-3.5 shrink-0 rounded-full ring-2 ring-offset-2 ring-offset-surface-container-low"
          style={{ backgroundColor: ZONE_COLORS[node.zone], ['--tw-ring-color' as any]: 'transparent' }}
          aria-hidden
        />
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-bold uppercase tracking-wide text-on-surface-variant">
            {TYPE_LABELS[node.type] || node.type} · {ZONE_LABELS[node.zone] || node.zone}
          </p>
          <h3 className="truncate text-base font-extrabold leading-tight" title={node.label}>
            {node.label}
          </h3>
          {node.sublabel && <p className="truncate text-xs text-on-surface-variant">{node.sublabel}</p>}
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close details"
          className="rounded-lg p-1.5 text-on-surface-variant hover:bg-surface-container-high"
        >
          <X className="h-4 w-4" />
        </button>
      </header>

      <div className="flex-1 space-y-5 overflow-y-auto p-4 text-sm">
        <section>
          <div className={`flex items-center gap-2 font-bold ${STATUS_TEXT_CLASS[node.status]}`}>
            <span className={`h-2 w-2 rounded-full ${STATUS_DOT_CLASS[node.status]}`} aria-hidden />
            {STATUS_LABELS[node.status]}
          </div>
          <p className="mt-1 text-on-surface-variant">{describeNode(node)}</p>
          {node.meta?.internet_exposed && (
            <p className="mt-2 rounded-lg border border-red-500/30 bg-red-500/10 p-2 text-xs font-semibold text-red-500">
              Anyone on the internet can reach this. That is the first thing to fix.
            </p>
          )}
        </section>

        <section>
          <h4 className="mb-1.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-on-surface-variant">
            <ShieldAlert className="h-3.5 w-3.5" /> Open issues ({issues.length})
          </h4>
          {issues.length === 0 ? (
            <p className="text-on-surface-variant">Nothing open right now.</p>
          ) : (
            <ul className="space-y-1.5">
              {issues.map((issue, idx) => (
                <li key={idx} className="flex gap-2 rounded-lg bg-surface-container p-2">
                  <span
                    className={`mt-0.5 shrink-0 rounded px-1.5 text-[10px] font-bold uppercase ${
                      issue.severity === 'critical' || issue.severity === 'high'
                        ? 'bg-red-500/15 text-red-500'
                        : 'bg-drift-amber/15 text-drift-amber'
                    }`}
                  >
                    {issue.severity}
                  </span>
                  <span className="leading-snug">{issue.title}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-surface-container p-2.5">
            <p className="flex items-center gap-1 text-[11px] font-bold uppercase text-on-surface-variant">
              <Eye className="h-3 w-3" /> Seen by
            </p>
            <p className="mt-0.5 font-semibold">{seenBy.length ? seenBy.join(', ') : 'Connector registry'}</p>
          </div>
          <div className="rounded-lg bg-surface-container p-2.5">
            <p className="flex items-center gap-1 text-[11px] font-bold uppercase text-on-surface-variant">
              <Clock className="h-3 w-3" /> Last seen
            </p>
            <p className="mt-0.5 font-semibold">{formatRelative(node.meta?.last_seen)}</p>
          </div>
        </section>

        {metaEntries.length > 0 && (
          <section>
            <h4 className="mb-1.5 text-xs font-bold uppercase tracking-wide text-on-surface-variant">Details</h4>
            <dl className="divide-y divide-outline-variant rounded-lg border border-outline-variant">
              {metaEntries.map(([key, value]) => (
                <div key={key} className="flex items-start justify-between gap-3 px-2.5 py-1.5">
                  <dt className="text-on-surface-variant">{META_LABELS[key]}</dt>
                  <dd className="max-w-[60%] truncate text-right font-semibold" title={String(value)}>
                    {formatValue(key, value)}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        )}

        <section>
          <h4 className="mb-1.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-on-surface-variant">
            <Link2 className="h-3.5 w-3.5" /> Connections ({related.length})
          </h4>
          {related.length === 0 ? (
            <p className="text-on-surface-variant">Not linked to anything else yet.</p>
          ) : (
            <ul className="space-y-1">
              {related.map((edge, idx) => {
                const otherId = edge.source === node.id ? edge.target : edge.source;
                const other = nodesById[otherId];
                const verb = EDGE_LABELS[edge.kind] || edge.kind;
                const sentence =
                  edge.source === node.id
                    ? `${verb} ${other?.label || otherId}`
                    : `${other?.label || otherId} ${verb} this`;
                return (
                  <li key={idx}>
                    <button
                      type="button"
                      onClick={() => onJump(otherId)}
                      className="w-full truncate rounded-lg px-2 py-1.5 text-left hover:bg-surface-container-high"
                      title={sentence}
                    >
                      <span
                        className={`mr-2 inline-block h-2 w-2 rounded-full ${
                          edge.kind === 'exposed_to_internet' ? 'bg-red-500' : 'bg-on-surface-variant/50'
                        }`}
                        aria-hidden
                      />
                      {sentence}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>
    </aside>
  );
}

export default NodeDetailPanel;
