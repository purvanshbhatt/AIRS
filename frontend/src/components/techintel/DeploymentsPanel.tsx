import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Cloud, Plug, ArrowRight } from 'lucide-react';
import type { TechDeployment } from '../../api';
import { Chip, IssueList, SourceChips, plural, severityRank, timeAgo, titleCase } from './shared';

/** Plain names for the cloud resource types the collector reports. Unknown types are shown as sent. */
const TYPE_COPY: Record<string, { plain: string; technical?: string }> = {
  ec2: { plain: 'Virtual servers', technical: 'EC2' },
  ec2_instance: { plain: 'Virtual servers', technical: 'EC2' },
  instance: { plain: 'Virtual servers' },
  vm: { plain: 'Virtual servers' },
  lambda: { plain: 'Small programs that run on demand', technical: 'Lambda' },
  function: { plain: 'Small programs that run on demand', technical: 'Functions' },
  rds: { plain: 'Databases', technical: 'RDS' },
  database: { plain: 'Databases' },
  dynamodb: { plain: 'Databases', technical: 'DynamoDB' },
  s3: { plain: 'File storage', technical: 'S3' },
  bucket: { plain: 'File storage' },
  storage: { plain: 'File storage' },
  ecs: { plain: 'Containers', technical: 'ECS' },
  eks: { plain: 'Containers', technical: 'EKS (Kubernetes)' },
  container: { plain: 'Containers' },
  load_balancer: { plain: 'Traffic entry points', technical: 'Load balancers' },
  elb: { plain: 'Traffic entry points', technical: 'Load balancers' },
  alb: { plain: 'Traffic entry points', technical: 'Load balancers' },
  cloudfront: { plain: 'Content delivery', technical: 'CloudFront' },
  api_gateway: { plain: 'APIs', technical: 'API Gateway' },
  apigateway: { plain: 'APIs', technical: 'API Gateway' },
  app_service: { plain: 'Hosted web apps', technical: 'App Service' },
  cloud_run: { plain: 'Hosted web apps', technical: 'Cloud Run' },
  elasticbeanstalk: { plain: 'Hosted web apps', technical: 'Elastic Beanstalk' },
};

function typeCopy(type: string): { plain: string; technical?: string } {
  const key = String(type || '').toLowerCase().replace(/[\s-]+/g, '_');
  return TYPE_COPY[key] || { plain: titleCase(String(type || 'Other services')) };
}

function DeploymentCard({ deployment }: { deployment: TechDeployment }) {
  const issues = deployment.issues || [];
  const worst = issues.reduce((w, i) => Math.min(w, severityRank(i.severity)), 4);
  const runtime = [deployment.runtime, deployment.version].filter(Boolean).join(' ');
  return (
    <li
      className={`rounded-xl border bg-surface-container-low p-4 space-y-3 ${
        worst === 0 ? 'border-critical-red/40' : issues.length > 0 ? 'border-drift-amber/40' : 'border-outline-variant'
      }`}
      data-testid="deployment-card"
    >
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-bold text-on-surface break-words">{deployment.name}</p>
          <p className="text-[11px] font-mono text-on-surface-variant">
            {[deployment.provider, deployment.region].filter(Boolean).join(' · ') || 'Location not reported'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-1.5 shrink-0">
          {deployment.public === true && (
            <Chip tone="warning" testId="deployment-public" title="Reachable from the public internet">
              Open to the internet
            </Chip>
          )}
          {deployment.public === false && (
            <Chip tone="ready" testId="deployment-private">
              Private
            </Chip>
          )}
          {deployment.public == null && <Chip testId="deployment-exposure-unknown">Exposure not known</Chip>}
        </div>
      </div>
      <p className="text-sm text-on-surface-variant">
        Runs on:{' '}
        {runtime ? (
          <span className="font-mono font-semibold text-on-surface">{runtime}</span>
        ) : (
          <span>not reported for this service</span>
        )}
      </p>
      {issues.length > 0 ? (
        <IssueList issues={issues} testId="deployment-issues" />
      ) : (
        <p className="text-xs text-on-surface-variant">No problems found on this service.</p>
      )}
    </li>
  );
}

interface DeploymentsPanelProps {
  deployments: TechDeployment[];
  sources?: Record<string, string> | null;
  collectedAt?: string | null;
}

/** Cloud services, grouped by what they are, with exposure and issues in plain words. */
export function DeploymentsPanel({ deployments, sources, collectedAt }: DeploymentsPanelProps) {
  const list = deployments || [];
  const groups = useMemo(() => {
    const map = new Map<string, TechDeployment[]>();
    list.forEach(d => {
      const key = String(d.type || 'other');
      map.set(key, [...(map.get(key) || []), d]);
    });
    return Array.from(map.entries());
  }, [list]);
  const collected = timeAgo(collectedAt);
  const publicCount = list.filter(d => d.public === true).length;
  const issueCount = list.reduce((sum, d) => sum + (d.issues || []).length, 0);

  if (list.length === 0) {
    return (
      <div className="space-y-4" data-testid="deployments-panel">
        <SourceChips sources={sources} label="Cloud accounts" testId="deployment-sources" />
        <div
          className="p-8 rounded-xl bg-surface-container-low border border-dashed border-outline-variant flex flex-col items-center text-center"
          data-testid="deployments-empty"
        >
          <div className="w-12 h-12 rounded-2xl bg-drift-amber/10 border border-drift-amber/30 flex items-center justify-center text-drift-amber mb-3">
            <Cloud className="w-6 h-6" aria-hidden="true" />
          </div>
          <h3 className="text-base font-semibold text-on-surface">Connect AWS to list what is running</h3>
          <p className="text-sm text-on-surface-variant max-w-md mt-1 leading-relaxed">
            Once your cloud account is connected we list every server, database and app in it, which ones are open to
            the internet, and what to fix. It takes one read-only login from your IT provider.
          </p>
          <Link
            to="/connectors"
            className="mt-4 inline-flex items-center gap-2 px-6 py-3 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 text-sm font-bold rounded-xl transition-all active:scale-[0.98]"
            data-testid="deployments-connect-link"
          >
            <Plug className="w-4 h-4" aria-hidden="true" />
            <span>Connect AWS</span>
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="deployments-panel">
      <div className="space-y-3">
        <p className="text-sm text-on-surface-variant" data-testid="deployments-summary">
          {plural(list.length, 'cloud service', 'cloud services')} running.{' '}
          {publicCount > 0
            ? `${publicCount} ${publicCount === 1 ? 'is' : 'are'} open to the internet.`
            : 'None are reported as open to the internet.'}{' '}
          {issueCount > 0 ? `${plural(issueCount, 'thing', 'things')} to fix.` : 'Nothing to fix.'}
          {collected ? ` Collected ${collected}.` : ''}
        </p>
        <SourceChips sources={sources} label="Cloud accounts" testId="deployment-sources" />
      </div>

      {groups.map(([type, items]) => {
        const copy = typeCopy(type);
        return (
          <section key={type} className="space-y-3" data-testid="deployment-group" aria-label={copy.plain}>
            <h3 className="flex flex-wrap items-baseline gap-2 text-sm font-bold text-on-surface">
              {copy.plain}
              {copy.technical && <span className="text-[10px] font-mono font-normal text-on-surface-variant">{copy.technical}</span>}
              <span className="text-xs font-mono font-normal text-on-surface-variant">{items.length}</span>
            </h3>
            <ul className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {items.map(d => (
                <DeploymentCard key={d.id} deployment={d} />
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}

export default DeploymentsPanel;
