import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Activity, ChevronDown, ChevronUp, Terminal, ShieldAlert, CheckCircle2, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ApiRequestError, getOrganizations, getOrgRemediations, patchRemediation, getGovernanceHealthIndex } from '../api';
import type { TrackerItem } from '../types';
import { Button, Badge } from '../components/ui';

const springTransition = { type: 'spring' as const, stiffness: 80, damping: 15, mass: 1 };

function getStackAwareEngineeringTasks(task: TrackerItem) {
  const title = task.title.toLowerCase();
  
  if (title.includes('mfa') || title.includes('auth') || title.includes('credential') || title.includes('identity')) {
    return {
      vendor: "Okta / IAM Platform",
      status: "Configuration Required",
      verificationMethod: "OAuth2 Token Validation & MFA Policy Attestation",
      instructions: "Update Okta global enrollment policy to enforce phishing-resistant MFA (WebAuthn/FIDO2) for all administrative and developer profiles.",
      snippet: `// Okta API - Create MFA Policy Rule Enforcing FIDO2 WebAuthn
curl -X POST \\
  https://\${OKTA_SUBDOMAIN}.okta.com/api/v1/policies/\${MFA_POLICY_ID}/rules \\
  -H 'Authorization: SSWS \${OKTA_API_TOKEN}' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "type": "SIGN_IN",
    "name": "Enforce WebAuthn FIDO2",
    "status": "ACTIVE",
    "actions": {
      "signon": {
        "access": "ALLOW",
        "requireFactor": true,
        "factorPromptMode": "ALWAYS",
        "rememberDeviceByDefault": false,
        "factorConstraints": {
          "supportedFactors": [
            { "factorType": "webauthn", "provider": "FIDO" }
          ]
        }
      }
    }
  }'`
    };
  } else if (title.includes('endpoint') || title.includes('edr') || title.includes('agent') || title.includes('threat') || title.includes('wazuh') || title.includes('splunk') || title.includes('monitoring') || title.includes('siem')) {
    return {
      vendor: "CrowdStrike Falcon / Wazuh EDR",
      status: "Sensor Telemetry Active",
      verificationMethod: "Wazuh Agent API Heartbeat & Falcon Control Policy",
      instructions: "Deploy the Wazuh agent v4.7.2 with CIS Benchmarks auditing configured, and update CrowdStrike Falcon prevention policy parameters to trigger critical alert detections.",
      snippet: `# Wazuh Agent local configuration block (ossec.conf) for CIS Auditing
cat <<EOF >> /var/ossec/etc/ossec.conf
<cis-cat>
  <enabled>yes</enabled>
  <scan_on_start>yes</scan_on_start>
  <interval>1d</interval>
  <ciscat_path>/var/ossec/wodles/ciscat</ciscat_path>
  <java_path>/usr/bin/java</java_path>
</cis-cat>

<localfile>
  <log_format>syslog</log_format>
  <location>/var/log/secure</location>
</localfile>
EOF

# Restart EDR Service to reload configurations
systemctl restart wazuh-agent
systemctl status wazuh-agent --no-pager`
    };
  } else if (title.includes('backup') || title.includes('dr') || title.includes('recovery') || title.includes('restore') || title.includes('bcdr')) {
    return {
      vendor: "AWS Backup / BCDR Engine",
      status: "Verification Pending",
      verificationMethod: "AWS Backup Vault Lock Verification",
      instructions: "Configure AWS Backup Vault Lock in compliance mode with a minimum lock duration to prevent malicious ransomware deletions of system recovery points.",
      snippet: `# Enable AWS Backup Vault Lock in Compliance Mode
aws backup put-backup-vault-lock-configuration \\
  --backup-vault-name ResilAI-Production-Vault \\
  --min-retention-days 30 \\
  --max-retention-days 365 \\
  --changeable-for-days 3 \\
  --region us-east-1

# Verify Vault Lock is active
aws backup describe-backup-vault \\
  --backup-vault-name ResilAI-Production-Vault \\
  --query '[BackupVaultName, Locked, MinRetentionDays]' \\
  --output table`
    };
  } else if (title.includes('vuln') || title.includes('patch') || title.includes('version') || title.includes('eol') || title.includes('legacy') || title.includes('update')) {
    return {
      vendor: "Tenable / AWS Systems Manager (SSM)",
      status: "Scan Completed - Actions Pending",
      verificationMethod: "AWS SSM Patch Manager Compliance Report",
      instructions: "Initiate immediate AWS Systems Manager patch baseline execution to resolve critical vulnerabilities (CVEs) across all active EC2/K8s nodes.",
      snippet: `# AWS Systems Manager - Run Patch Baseline on Production Targets
aws ssm send-command \\
  --document-name "AWS-RunPatchBaseline" \\
  --targets "Key=tag:Environment,Values=Production" \\
  --parameters "Operation=Install" \\
  --comment "Urgent security patches for critical CVE compliance" \\
  --region us-east-1

# Query command execution status
aws ssm list-command-invocations \\
  --command-id "\${COMMAND_ID}" \\
  --details`
    };
  } else {
    return {
      vendor: "Enterprise Security Control Manager",
      status: "Control Under Assessment",
      verificationMethod: "Manual Compliance Verification Check",
      instructions: "Align the control to the corresponding organization governance standard, validating the enforcement footprint through the administration console.",
      snippet: `# Audit command helper to review active security parameters
resilai-cli audit verify-control \\
  --control-id "${task.id}" \\
  --org-id "\${ORG_ID}" \\
  --verbose`
    };
  }
}

export default function RemediationLedger() {
  const [search, setSearch] = useState('');
  const [orgId, setOrgId] = useState<string>('');
  const [orgs, setOrgs] = useState<Array<{ id: string; name: string }>>([]);
  const [tasks, setTasks] = useState<TrackerItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Accordions open/close state (30, 60, 90 urgency cycles)
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    '30': true,
    '60': true,
    '90': false,
  });

  // Selected task state for configuration side drawer
  const [selectedTask, setSelectedTask] = useState<TrackerItem | null>(null);

  const toggleGroup = (group: string) => {
    setExpandedGroups(prev => ({
      ...prev,
      [group]: !prev[group],
    }));
  };

  const normalizeStatus = (status: TrackerItem['status']): 'open' | 'in_progress' | 'resolved' => {
    if (status === 'in_progress') return 'in_progress';
    if (status === 'completed' || status === 'done') return 'resolved';
    return 'open';
  };

  useEffect(() => {
    async function loadOrgs() {
      try {
        const data = await getOrganizations();
        setOrgs(data.map((o) => ({ id: o.id, name: o.name })));
        if (data.length > 0) {
          setOrgId(data[0].id);
        }
      } catch (err) {
        setError(err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to load organizations');
      }
    }
    void loadOrgs();
  }, []);

  useEffect(() => {
    async function loadTasks() {
      if (!orgId) return;
      setLoading(true);
      setError(null);
      try {
        const response = await getOrgRemediations(orgId);
        setTasks(response.items || []);
      } catch (err) {
        setError(err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to load remediations');
      } finally {
        setLoading(false);
      }
    }

    void loadTasks();
  }, [orgId]);

  const handleStatusChange = async (itemId: string, status: 'open' | 'in_progress' | 'resolved') => {
    try {
      const updated = await patchRemediation(itemId, { status });
      setTasks((prev) => prev.map((task) => (task.id === itemId ? { ...task, status: updated.status } : task)));
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to update remediation');
    }
  };

  const filtered = useMemo(
    () =>
      tasks.filter(
        (task) =>
          task.title.toLowerCase().includes(search.toLowerCase()) ||
          task.id.toLowerCase().includes(search.toLowerCase())
      ),
    [search, tasks]
  );

  // Group remediations by urgency window (30 / 60 / 90 days)
  const groupedTasks = useMemo(() => {
    const immediate: TrackerItem[] = [];
    const nearTerm: TrackerItem[] = [];
    const strategic: TrackerItem[] = [];

    filtered.forEach((task) => {
      if (task.phase === '30' || task.priority === 'critical') {
        immediate.push(task);
      } else if (task.phase === '60' || task.priority === 'high') {
        nearTerm.push(task);
      } else {
        strategic.push(task);
      }
    });

    return { '30': immediate, '60': nearTerm, '90': strategic };
  }, [filtered]);

  const resolvedCount = tasks.filter((task) => task.status === 'completed' || task.status === 'done').length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={springTransition}
      className="p-4 sm:p-6 lg:p-8 space-y-8 max-w-[1200px] mx-auto text-slate-100 min-h-screen"
    >
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link to="/dashboard" className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              <ArrowLeft className="w-3 h-3" /> Back to Dashboard
            </Link>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Priority Remediation Ledger</h1>
          <p className="text-slate-400 text-xs mt-0.5">
            Operational roadmap sorted by response urgency windows.
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-2xl text-xs flex items-center gap-3">
          <span className="text-slate-500 font-mono">Progress:</span>
          <div className="text-emerald-400 font-mono font-bold">
            {resolvedCount} resolved / {tasks.length} total
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <label className="text-xs text-slate-400 uppercase tracking-widest shrink-0">Org Context</label>
          <select
            value={orgId}
            onChange={(event) => setOrgId(event.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-xs font-semibold text-slate-300 focus:border-indigo-500/50 w-full sm:w-56"
            aria-label="Organization selector"
          >
            {orgs.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name}
              </option>
            ))}
          </select>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search tasks..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 pl-9 pr-3 text-xs outline-none focus:border-indigo-500/50 transition-colors placeholder:text-slate-500 text-slate-200"
          />
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-900/30 text-rose-400 text-xs">
          {error}
        </div>
      )}

      {/* Accordion groups */}
      <div className="space-y-4">
        {loading ? (
          <div className="py-12 text-center text-xs text-slate-500 italic">
            Retrieving remediation tasks...
          </div>
        ) : (
          ([
            { key: '30', label: 'Immediate Mitigation (30 Days)', color: 'border-rose-500/30 text-rose-400 bg-rose-500/5' },
            { key: '60', label: 'Near-Term Resolution (60 Days)', color: 'border-amber-500/30 text-amber-400 bg-amber-500/5' },
            { key: '90', label: 'Strategic Alignment (90 Days)', color: 'border-indigo-500/30 text-indigo-400 bg-indigo-500/5' }
          ] as const).map((group) => {
            const items = groupedTasks[group.key] || [];
            const isOpen = expandedGroups[group.key];
            return (
              <div key={group.key} className="rounded-3xl border border-slate-900 overflow-hidden bg-slate-950/20 shadow-lg">
                <button
                  onClick={() => toggleGroup(group.key)}
                  className="w-full p-5 flex items-center justify-between text-left hover:bg-slate-900/20 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`px-2.5 py-1 rounded-xl text-[10px] font-bold border ${group.color}`}>
                      {group.key}d
                    </div>
                    <span className="text-xs font-semibold text-slate-200">{group.label}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-900 border border-slate-800 text-slate-400">
                      {items.length} controls
                    </span>
                  </div>
                  {isOpen ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                </button>

                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: 'auto' }}
                      exit={{ height: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="p-5 pt-0 border-t border-slate-900 divide-y divide-slate-900">
                        {items.length === 0 ? (
                          <p className="text-xs text-slate-500 italic py-6 text-center">
                            No active tasks matching search filters.
                          </p>
                        ) : (
                          items.map((item) => {
                            const boostValue =
                              item.priority === 'critical' ? '+6.5' :
                              item.priority === 'high' ? '+4.5' :
                              item.priority === 'medium' ? '+2.5' : '+1.0';

                            return (
                              <div
                                key={item.id}
                                onClick={() => setSelectedTask(item)}
                                className="py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer hover:bg-slate-900/10 transition-all rounded-xl px-2.5 group"
                              >
                                <div className="flex items-start gap-3 min-w-0 flex-1">
                                  <span className="px-2.5 py-1 rounded-xl bg-emerald-500/10 text-emerald-400 font-mono font-bold text-xs border border-emerald-500/20 shrink-0 self-center">
                                    {boostValue} GHI
                                  </span>
                                  <div className="min-w-0">
                                    <div className="flex items-center gap-2">
                                      <span className="text-[10px] font-mono text-slate-500">{item.id.slice(0, 8)}</span>
                                      <span className="text-[10px] px-2 py-0.2 bg-slate-900 rounded text-slate-400 capitalize">
                                        {item.priority}
                                      </span>
                                    </div>
                                    <p className="text-xs font-semibold text-slate-200 mt-1 truncate group-hover:text-indigo-400 transition-colors">
                                      {item.title}
                                    </p>
                                  </div>
                                </div>

                                <div className="flex items-center gap-4 shrink-0" onClick={e => e.stopPropagation()}>
                                  <select
                                    aria-label={`Status selector for task ${item.id}`}
                                    value={normalizeStatus(item.status)}
                                    onChange={(event) =>
                                      handleStatusChange(item.id, event.target.value as 'open' | 'in_progress' | 'resolved')
                                    }
                                    className="text-[11px] font-semibold text-slate-300 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 focus:border-indigo-500"
                                  >
                                    <option value="open">Open</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="resolved">Resolved</option>
                                  </select>
                                </div>
                              </div>
                            );
                          })
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })
        )}
      </div>

      {/* Stack-Aware side drawer */}
      <AnimatePresence>
        {selectedTask && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedTask(null)}
              className="fixed inset-0 z-40 bg-black cursor-pointer"
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 22, stiffness: 120 }}
              className="fixed inset-y-0 right-0 z-50 w-full sm:w-[500px] bg-slate-950 border-l border-slate-900 shadow-2xl p-6 flex flex-col justify-between overflow-y-auto"
            >
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-slate-900 pb-4">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-5 h-5 text-indigo-400" />
                    <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                      Engineering Remediation Guide
                    </h3>
                  </div>
                  <button
                    onClick={() => setSelectedTask(null)}
                    className="p-1 rounded-lg hover:bg-slate-900 text-slate-400 hover:text-white transition-colors cursor-pointer"
                  >
                    Close
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                      Task ID: {selectedTask.id}
                    </span>
                    <h4 className="text-sm font-bold text-white mt-1">
                      {selectedTask.title}
                    </h4>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 bg-slate-900/50 rounded-2xl border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Vendor Integration</span>
                      <span className="font-semibold text-slate-300 mt-1 block">
                        {getStackAwareEngineeringTasks(selectedTask).vendor}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-900/50 rounded-2xl border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Verification Method</span>
                      <span className="font-semibold text-indigo-400 mt-1 block">
                        {getStackAwareEngineeringTasks(selectedTask).verificationMethod}
                      </span>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-slate-900/30 border border-slate-800 space-y-2">
                    <span className="text-[10px] text-slate-500 tracking-wider font-semibold block">
                      Instructions
                    </span>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {getStackAwareEngineeringTasks(selectedTask).instructions}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <span className="text-[10px] text-slate-500 tracking-wider font-semibold block">
                      Vendor Shell Configuration
                    </span>
                    <pre className="font-mono text-[10px] bg-slate-950 p-4 rounded-2xl border border-slate-900 text-slate-200 overflow-x-auto whitespace-pre leading-relaxed select-all">
                      {getStackAwareEngineeringTasks(selectedTask).snippet}
                    </pre>
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-900 pt-4 mt-6 flex gap-2">
                <Button
                  className="flex-1 text-xs py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold shadow-lg shadow-indigo-600/10"
                  onClick={() => setSelectedTask(null)}
                >
                  Accept Instructions
                </Button>
                <Button
                  className="text-xs py-2 bg-slate-900 hover:bg-slate-800 text-slate-400 rounded-xl"
                  onClick={() => setSelectedTask(null)}
                >
                  Close
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
