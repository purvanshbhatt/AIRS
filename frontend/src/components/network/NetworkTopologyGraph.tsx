import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Network,
  ShieldCheck,
  ShieldAlert,
  Server,
  Laptop,
  Cloud,
  Lock,
  Unlock,
  Wifi,
  Database,
  AlertTriangle,
  Plus,
  Play,
  RotateCcw,
  CheckCircle2,
  Layers,
  Radio,
  ArrowRight,
  Sliders,
  X,
  Info,
  ExternalLink,
  ChevronRight,
  HardDrive
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button, Badge } from '../ui';
import { useVertical } from '../../contexts/VerticalContext';

export interface NetworkNode {
  id: string;
  name: string;
  type: 'gateway' | 'firewall' | 'vlan' | 'server' | 'endpoint' | 'cloud' | 'iot';
  cidrOrIp: string;
  zone: 'perimeter' | 'security' | 'core' | 'workstations' | 'guest' | 'cloud';
  status: 'healthy' | 'warning' | 'critical';
  isolated: boolean;
  parentIds: string[];
  description: string;
  soWhat: string;
  activeControls: string[];
  lateralRisk?: string;
  verticalLabels?: {
    healthcare?: { name: string; description: string };
    legal?: { name: string; description: string };
  };
}

const DEFAULT_NODES: NetworkNode[] = [
  // Perimeter
  {
    id: 'node-wan',
    name: 'Internet / WAN Gateway',
    type: 'gateway',
    cidrOrIp: '0.0.0.0/0 (Fiber Primary)',
    zone: 'perimeter',
    status: 'healthy',
    isolated: false,
    parentIds: [],
    description: 'Redundant SD-WAN fiber uplink with BGP failover.',
    soWhat: 'All incoming public traffic terminates at the perimeter firewall with zero direct inward ports open.',
    activeControls: ['DDoS Shield', 'BGP Route Filter', 'Geo-IP Ingress Block'],
  },
  {
    id: 'node-cloud-vpc',
    name: 'AWS Cloud Production VPC',
    type: 'cloud',
    cidrOrIp: '172.31.0.0/16 (us-east-1)',
    zone: 'cloud',
    status: 'warning',
    isolated: true,
    parentIds: ['node-wan'],
    description: 'Cloud workloads hosting databases and encrypted document storage.',
    soWhat: 'Directly monitored via AWS Security Hub connector. S3 client vault public access check flagged.',
    activeControls: ['AWS Security Hub', 'GuardDuty Intelligent Detection', 'VPC Flow Logs'],
    lateralRisk: 'Cloud-to-prem IPsec tunnel restricted to port 443 only.',
    verticalLabels: {
      healthcare: {
        name: 'AWS Health Cloud VPC',
        description: 'HIPAA-compliant cloud storage hosting encrypted EHR backups.',
      },
      legal: {
        name: 'AWS Legal Vault VPC',
        description: 'SOC2-compliant repository hosting confidential client matter archives.',
      },
    },
  },
  // Security Layer
  {
    id: 'node-firewall',
    name: 'Edge Next-Gen Firewall Cluster',
    type: 'firewall',
    cidrOrIp: '10.0.0.1 (HA Pair Active/Passive)',
    zone: 'security',
    status: 'healthy',
    isolated: false,
    parentIds: ['node-wan', 'node-cloud-vpc'],
    description: 'Hardware firewall running deep packet inspection & microsegmentation.',
    soWhat: 'The single brain enforcing zero-trust boundaries between office laptops, backups, and guest networks.',
    activeControls: ['Zero-Trust Microsegmentation', 'TLS 1.3 Inspection', 'Intrusion Prevention (IPS)'],
  },
  // Subnets / VLANs
  {
    id: 'vlan-core',
    name: 'VLAN 10: Management & Core Servers',
    type: 'vlan',
    cidrOrIp: '10.0.10.0/24',
    zone: 'core',
    status: 'healthy',
    isolated: true,
    parentIds: ['node-firewall'],
    description: 'Protected zone for Domain Controllers, Identity Services, and Line-of-Business apps.',
    soWhat: 'Workstations cannot directly reach administration ports. RDP and SSH strictly gated via MFA bastion.',
    activeControls: ['MFA Access Enforcement', '802.1X Port Authentication', 'Admin Bastion Gating'],
  },
  {
    id: 'vlan-backup',
    name: 'VLAN 20: Air-Gapped Backups & Storage',
    type: 'vlan',
    cidrOrIp: '10.0.20.0/24',
    zone: 'core',
    status: 'healthy',
    isolated: true,
    parentIds: ['node-firewall'],
    description: 'Immutable backup storage repository running hardened Linux repository.',
    soWhat: 'Completely air-gapped from user workstations. Ransomware on staff laptops physically cannot touch this VLAN.',
    activeControls: ['Microsegmentation Rule #14', 'Immutable Object Lock', 'No Inbound SMB Traffic'],
  },
  {
    id: 'vlan-staff',
    name: 'VLAN 30: Staff & Partner Workstations',
    type: 'vlan',
    cidrOrIp: '10.0.30.0/24',
    zone: 'workstations',
    status: 'healthy',
    isolated: false,
    parentIds: ['node-firewall'],
    description: 'Primary corporate network for staff laptops, desktop PCs, and docking stations.',
    soWhat: 'Protected by endpoint detection and response (EDR). Lateral host-to-host traffic blocked by switch ACLs.',
    activeControls: ['EDR Active Sensor', 'Client-to-Client Isolation', 'DNS Filtering'],
  },
  {
    id: 'vlan-guest',
    name: 'VLAN 50: Quarantined Guest & IoT',
    type: 'vlan',
    cidrOrIp: '10.0.50.0/24',
    zone: 'guest',
    status: 'healthy',
    isolated: true,
    parentIds: ['node-firewall'],
    description: 'Visitor Wi-Fi, waiting room smart displays, and network printers.',
    soWhat: 'Internet-only egress. Strict firewall drop rules prevent any access to corporate or backup networks.',
    activeControls: ['Strict Intra-BSS Quarantine', 'Zero Internal Routing', 'Bandwidth Capping'],
  },
  // Connected Assets
  {
    id: 'asset-dc',
    name: 'Primary Domain Controller',
    type: 'server',
    cidrOrIp: '10.0.10.5',
    zone: 'core',
    status: 'healthy',
    isolated: true,
    parentIds: ['vlan-core'],
    description: 'Active Directory & DNS Server handling corporate authentication.',
    soWhat: 'Enforces password hygiene, BitLocker recovery keys, and centralized Kerberos tickets.',
    activeControls: ['SMB Signing Required', 'Audit Logging Enabled', 'Tier 0 Administrative Boundary'],
  },
  {
    id: 'asset-backup',
    name: 'Immutable Veeam Backup Appliance',
    type: 'server',
    cidrOrIp: '10.0.20.10',
    zone: 'core',
    status: 'healthy',
    isolated: true,
    parentIds: ['vlan-backup'],
    description: 'Hardened Linux repository with 30-day immutable snapshot retention.',
    soWhat: 'Your disaster recovery safety net. Verified clean recovery point taken 2 hours ago.',
    activeControls: ['Hardened Immutable Repository', 'Write-Once-Read-Many (WORM)', 'MFA Console Access'],
  },
  {
    id: 'asset-laptop',
    name: 'Staff & Executive Laptops (x38)',
    type: 'endpoint',
    cidrOrIp: '10.0.30.15 - 10.0.30.55',
    zone: 'workstations',
    status: 'healthy',
    isolated: false,
    parentIds: ['vlan-staff'],
    description: 'Company-managed MacBooks and ThinkPads protected by MDM & Defender/Crowdstrike.',
    soWhat: 'All full-disk encrypted with BitLocker/FileVault. Automated daily compliance posture checks.',
    activeControls: ['BitLocker / FileVault Enforced', 'EDR Sensor 100% Active', 'MFA Required for Login'],
    verticalLabels: {
      healthcare: {
        name: 'Clinical Laptops & Nursing Tablets (x42)',
        description: 'Clinician mobile devices accessing EHR with smartcard / MFA tap.',
      },
      legal: {
        name: 'Partner Laptops & Legal Assistants (x35)',
        description: 'Partner laptops with encrypted document checkouts and matter vaults.',
      },
    },
  },
  {
    id: 'asset-s3',
    name: 'Cloud Data Vault (AWS S3)',
    type: 'cloud',
    cidrOrIp: 's3://resilai-vault-505467908065',
    zone: 'cloud',
    status: 'warning',
    isolated: true,
    parentIds: ['node-cloud-vpc'],
    description: 'Offsite replica bucket in AWS us-east-1.',
    soWhat: 'Needs attention: AWS Security Hub detected Block Public Access setting was toggled off on one sub-folder.',
    activeControls: ['AWS KMS Server-Side Encryption', 'Object Versioning', 'Bucket Policy Enforced'],
    verticalLabels: {
      healthcare: {
        name: 'Patient Health Records Vault (AWS S3)',
        description: 'Offsite encrypted HIPAA archive for diagnostic images and chart exports.',
      },
      legal: {
        name: 'Client Matter Vault (AWS S3)',
        description: 'Confidential litigation hold repository and deposition video archives.',
      },
    },
  },
];

export function NetworkTopologyGraph() {
  const { currentVertical } = useVertical();
  const [nodes, setNodes] = useState<NetworkNode[]>(DEFAULT_NODES);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>('node-firewall');
  const [isSimulationActive, setIsSimulationActive] = useState(false);
  const [simulatedCompromiseId, setSimulatedCompromiseId] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [filterZone, setFilterZone] = useState<string>('all');

  // Form for Adding New Subnet/Node
  const [formData, setFormData] = useState({
    name: '',
    cidrOrIp: '',
    zone: 'workstations' as NetworkNode['zone'],
    type: 'vlan' as NetworkNode['type'],
    isolated: true,
    description: '',
  });

  // Selected Node Details
  const selectedNode = useMemo(() => {
    return nodes.find((n) => n.id === selectedNodeId) || nodes[0];
  }, [nodes, selectedNodeId]);

  // Dynamic Vertical Label resolution
  const getNodeName = (node: NetworkNode) => {
    if (currentVertical === 'legal' && node.verticalLabels?.legal?.name) {
      return node.verticalLabels.legal.name;
    }
    if (currentVertical === 'healthcare' && node.verticalLabels?.healthcare?.name) {
      return node.verticalLabels.healthcare.name;
    }
    return node.name;
  };

  const getNodeDescription = (node: NetworkNode) => {
    if (currentVertical === 'legal' && node.verticalLabels?.legal?.description) {
      return node.verticalLabels.legal.description;
    }
    if (currentVertical === 'healthcare' && node.verticalLabels?.healthcare?.description) {
      return node.verticalLabels.healthcare.description;
    }
    return node.description;
  };

  // Simulation Logic: If a node is compromised, determine blast radius
  const simulationState = useMemo(() => {
    if (!isSimulationActive || !simulatedCompromiseId) {
      return { compromised: new Set<string>(), blocked: new Set<string>(), protected: new Set<string>() };
    }

    const compromised = new Set<string>([simulatedCompromiseId]);
    const blocked = new Set<string>();
    const protectedNodes = new Set<string>();

    nodes.forEach((n) => {
      if (n.id === simulatedCompromiseId) return;

      // If simulated node is on guest or workstations, zero-trust isolates core and backups!
      if (simulatedCompromiseId === 'vlan-guest' || simulatedCompromiseId === 'asset-laptop') {
        if (n.zone === 'core') {
          blocked.add('node-firewall');
          protectedNodes.add(n.id);
        } else if (n.id === 'vlan-staff' && simulatedCompromiseId === 'vlan-guest') {
          blocked.add('node-firewall');
          protectedNodes.add(n.id);
        } else if (n.zone === 'cloud') {
          protectedNodes.add(n.id);
        }
      } else {
        // General isolation check
        if (n.isolated) {
          protectedNodes.add(n.id);
        }
      }
    });

    return { compromised, blocked, protected: protectedNodes };
  }, [isSimulationActive, simulatedCompromiseId, nodes]);

  // Handle Add Network Node
  const handleAddNode = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.cidrOrIp) return;

    const newNode: NetworkNode = {
      id: `custom-${Date.now()}`,
      name: formData.name,
      type: formData.type,
      cidrOrIp: formData.cidrOrIp,
      zone: formData.zone,
      status: 'healthy',
      isolated: formData.isolated,
      parentIds: ['node-firewall'],
      description: formData.description || 'Custom organizational subnet added by IT administration.',
      soWhat: formData.isolated
        ? 'Microsegmented: Traffic to critical core servers is blocked by default policy.'
        : 'Standard corporate routing: Monitored for lateral protocol anomalies.',
      activeControls: ['Custom IT Network Policy', 'Subnet Egress Guard'],
    };

    setNodes((prev) => [...prev, newNode]);
    setSelectedNodeId(newNode.id);
    setIsAddModalOpen(false);
    setFormData({
      name: '',
      cidrOrIp: '',
      zone: 'workstations',
      type: 'vlan',
      isolated: true,
      description: '',
    });
  };

  // Icon selector
  const getNodeIcon = (type: NetworkNode['type']) => {
    switch (type) {
      case 'gateway':
        return Radio;
      case 'cloud':
        return Cloud;
      case 'firewall':
        return ShieldCheck;
      case 'vlan':
        return Layers;
      case 'server':
        return Server;
      case 'endpoint':
        return Laptop;
      case 'iot':
        return Wifi;
      default:
        return Network;
    }
  };

  // Filtered nodes
  const filteredNodes = useMemo(() => {
    if (filterZone === 'all') return nodes;
    return nodes.filter((n) => n.zone === filterZone);
  }, [nodes, filterZone]);

  // Tiers for visual grouping
  const tiers = useMemo(() => {
    return [
      {
        title: 'Tier 1: Cloud & External Perimeter',
        subtitle: 'Internet gateways, cloud VPCs, and external boundary',
        nodes: filteredNodes.filter((n) => n.zone === 'perimeter' || n.zone === 'cloud'),
      },
      {
        title: 'Tier 2: Security & Zero-Trust Enforcement',
        subtitle: 'Hardware firewalls and microsegmentation policy engine',
        nodes: filteredNodes.filter((n) => n.zone === 'security'),
      },
      {
        title: 'Tier 3: Network Segments (VLANs & Subnets)',
        subtitle: 'Isolated broadcast domains separating staff, backups, and guests',
        nodes: filteredNodes.filter((n) => n.type === 'vlan'),
      },
      {
        title: 'Tier 4: Critical Assets & Endpoints',
        subtitle: 'Core databases, backup appliances, and user workstations',
        nodes: filteredNodes.filter((n) => n.type === 'server' || n.type === 'endpoint' || n.type === 'iot'),
      },
    ].filter((t) => t.nodes.length > 0);
  }, [filteredNodes]);

  return (
    <div className="space-y-6">
      {/* Top Banner / Explainer for Solo IT Teams */}
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 text-white shadow-xl border border-indigo-500/20">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl text-left">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-500/30 text-indigo-300 border border-indigo-400/30">
                1-Person IT Cockpit
              </span>
              <span className="text-xs text-slate-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Zero SOC Alert Fatigue
              </span>
            </div>
            <h2 className="text-2xl font-black tracking-tight text-white">
              Visual Network Architecture & Blast Radius Map
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              No endless SIEM logs or confusing SOC labs. See how your entire infrastructure branches out, verify that backups are truly air-gapped, and test ransomware containment in one click.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Lateral Movement Simulator Button */}
            <Button
              onClick={() => {
                if (isSimulationActive) {
                  setIsSimulationActive(false);
                  setSimulatedCompromiseId(null);
                } else {
                  setIsSimulationActive(true);
                  setSimulatedCompromiseId('asset-laptop'); // Default simulate staff laptop
                }
              }}
              variant={isSimulationActive ? 'danger' : 'secondary'}
              className="font-bold flex items-center gap-2 shadow-sm"
            >
              {isSimulationActive ? (
                <>
                  <RotateCcw className="w-4 h-4" /> Reset Simulation
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 text-rose-500" /> Simulate Threat Containment
                </>
              )}
            </Button>

            {/* Add Network Node Button */}
            <Button
              onClick={() => setIsAddModalOpen(true)}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold flex items-center gap-2 shadow-md"
            >
              <Plus className="w-4 h-4" /> Add Subnet / Network
            </Button>
          </div>
        </div>

        {/* Simulation Banner Active Notice */}
        <AnimatePresence>
          {isSimulationActive && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 pt-4 border-t border-indigo-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs bg-rose-950/40 p-3 rounded-xl border border-rose-500/30"
            >
              <div className="flex items-center gap-2 text-rose-300 font-medium">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>
                  <strong>Simulation Active:</strong> Simulating a ransomware breach on{' '}
                  <span className="text-white underline font-bold">
                    {nodes.find((n) => n.id === simulatedCompromiseId)?.name || 'Selected Node'}
                  </span>
                  . Green nodes indicate verified zero-trust containment.
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-emerald-400 font-bold flex items-center gap-1">
                  <ShieldCheck className="w-4 h-4" /> Containment: 100%
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Filter and Quick Stats Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 text-left">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-bold text-slate-500 uppercase mr-1">Zone Filter:</span>
          {[
            { id: 'all', label: 'All Zones' },
            { id: 'cloud', label: 'AWS / Cloud' },
            { id: 'core', label: 'Core & Backups' },
            { id: 'workstations', label: 'Workstations' },
            { id: 'guest', label: 'Guest / IoT' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterZone(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                filterZone === tab.id
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-4 text-xs font-medium text-slate-500">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>
            <span>Zero-Trust Isolated: <strong>5 Subnets</strong></span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span>
            <span>Needs Attention: <strong>1 Cloud Asset</strong></span>
          </div>
        </div>
      </div>

      {/* Main Layout: Interactive Graph Canvas + Inspector Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Graph Canvas (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          <div className="space-y-6">
            {tiers.map((tier, tierIdx) => (
              <div
                key={tierIdx}
                className="bg-slate-50/70 dark:bg-slate-900/60 p-5 rounded-2xl border border-slate-200 dark:border-slate-800/80 text-left relative overflow-hidden"
              >
                <div className="mb-4 flex items-center justify-between border-b border-slate-200/60 dark:border-slate-800 pb-2">
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      {tier.title}
                    </h3>
                    <p className="text-[11px] text-slate-400">{tier.subtitle}</p>
                  </div>
                  <Badge variant="outline" className="text-[10px] font-mono">
                    {tier.nodes.length} {tier.nodes.length === 1 ? 'Node' : 'Nodes'}
                  </Badge>
                </div>

                {/* Nodes Grid within Tier */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  {tier.nodes.map((node) => {
                    const Icon = getNodeIcon(node.type);
                    const isSelected = selectedNodeId === node.id;
                    const isCompromised = simulationState.compromised.has(node.id);
                    const isProtected = simulationState.protected.has(node.id);
                    const isBlocked = simulationState.blocked.has(node.id);

                    // Dynamic Styling based on state & simulation
                    let borderClass = 'border-slate-200 dark:border-slate-800';
                    let bgClass = 'bg-white dark:bg-slate-900';
                    let statusBadge = (
                      <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                    );

                    if (node.status === 'warning') {
                      statusBadge = <span className="w-2 h-2 rounded-full bg-amber-500"></span>;
                    } else if (node.status === 'critical') {
                      statusBadge = <span className="w-2 h-2 rounded-full bg-rose-500"></span>;
                    }

                    if (isSelected) {
                      borderClass = 'border-indigo-600 ring-2 ring-indigo-500/30';
                    }

                    if (isSimulationActive) {
                      if (isCompromised) {
                        borderClass = 'border-rose-600 ring-4 ring-rose-500/40 animate-pulse';
                        bgClass = 'bg-rose-50 dark:bg-rose-950/40';
                      } else if (isProtected) {
                        borderClass = 'border-emerald-500 ring-2 ring-emerald-500/20';
                        bgClass = 'bg-emerald-50/40 dark:bg-emerald-950/20';
                      }
                    }

                    return (
                      <motion.div
                        key={node.id}
                        whileHover={{ scale: 1.015 }}
                        whileTap={{ scale: 0.99 }}
                        onClick={() => {
                          setSelectedNodeId(node.id);
                          if (isSimulationActive) {
                            setSimulatedCompromiseId(node.id);
                          }
                        }}
                        className={`cursor-pointer p-4 rounded-xl border transition-all text-left shadow-sm ${bgClass} ${borderClass}`}
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2.5">
                            <div
                              className={`p-2 rounded-lg ${
                                isCompromised
                                  ? 'bg-rose-500 text-white'
                                  : isProtected
                                  ? 'bg-emerald-500 text-white'
                                  : node.type === 'firewall'
                                  ? 'bg-indigo-600 text-white'
                                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                              }`}
                            >
                              <Icon className="w-4 h-4" />
                            </div>
                            <div>
                              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 leading-tight">
                                {getNodeName(node)}
                              </h4>
                              <p className="text-[11px] font-mono text-slate-500">{node.cidrOrIp}</p>
                            </div>
                          </div>

                          <div className="flex items-center gap-1.5">
                            {statusBadge}
                            {node.isolated ? (
                              <span title="Zero-Trust Isolated">
                                <Lock className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                              </span>
                            ) : (
                              <span title="Routed">
                                <Unlock className="w-3.5 h-3.5 text-slate-400" />
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Brief Summary */}
                        <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 mt-1">
                          {getNodeDescription(node)}
                        </p>

                        {/* Badges */}
                        <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px]">
                          <span className="text-slate-400 capitalize">{node.zone} zone</span>
                          {isSimulationActive ? (
                            isCompromised ? (
                              <span className="text-rose-600 font-bold flex items-center gap-1">
                                <AlertTriangle className="w-3 h-3" /> Compromised
                              </span>
                            ) : (
                              <span className="text-emerald-600 font-bold flex items-center gap-1">
                                <ShieldCheck className="w-3 h-3" /> Safe (Isolated)
                              </span>
                            )
                          ) : (
                            <span className="text-indigo-600 dark:text-indigo-400 font-semibold flex items-center gap-0.5">
                              Inspect <ChevronRight className="w-3 h-3" />
                            </span>
                          )}
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Drawer: Asset & Isolation Inspector (4 cols) */}
        <div className="lg:col-span-4 sticky top-6">
          <Card className="border-indigo-100 dark:border-slate-800 shadow-xl overflow-hidden text-left">
            <CardHeader className="bg-slate-50 dark:bg-slate-900/80 p-5 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
                  Node Inspector
                </span>
                {selectedNode.status === 'warning' ? (
                  <Badge variant="warning" className="text-xs">Needs Attention</Badge>
                ) : (
                  <Badge variant="ready" className="text-xs">Healthy & Enforced</Badge>
                )}
              </div>
              <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                {getNodeName(selectedNode)}
              </CardTitle>
              <p className="text-xs font-mono text-slate-500">{selectedNode.cidrOrIp}</p>
            </CardHeader>

            <CardContent className="p-5 space-y-5">
              {/* Solo IT "So What?" Card */}
              <div className="p-3.5 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/30 space-y-1">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-indigo-700 dark:text-indigo-300">
                  What This Means For Solo IT
                </span>
                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                  {selectedNode.soWhat}
                </p>
              </div>

              {/* Isolation & Blast Radius Metric */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Blast Radius & Containment
                </h4>
                <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 bg-slate-50/50 dark:bg-slate-900/50">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-600 dark:text-slate-400">Zero-Trust Isolation:</span>
                    <span className="font-bold text-emerald-600 flex items-center gap-1">
                      {selectedNode.isolated ? (
                        <>
                          <Lock className="w-3.5 h-3.5" /> Enforced (Blocked)
                        </>
                      ) : (
                        <>
                          <Unlock className="w-3.5 h-3.5 text-amber-500" /> Standard Routing
                        </>
                      )}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-600 dark:text-slate-400">Lateral Route to Backups:</span>
                    <span className="font-mono font-bold text-emerald-600">0 Permitted Paths</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-600 dark:text-slate-400">Zone Classification:</span>
                    <span className="font-bold text-slate-900 dark:text-white capitalize">
                      {selectedNode.zone}
                    </span>
                  </div>
                </div>
              </div>

              {/* Active Verified Controls */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Active Verified Defenses
                </h4>
                <div className="space-y-1.5">
                  {selectedNode.activeControls.map((ctrl, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 p-2 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 text-xs font-medium text-emerald-800 dark:text-emerald-300"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span>{ctrl}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action / Remediation if node has issue */}
              {selectedNode.status === 'warning' && (
                <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/40 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-amber-800 dark:text-amber-300">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    <span>Action Required (1 Click)</span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    Enable S3 Block Public Access across all bucket policies in account 505467908065.
                  </p>
                  <Button size="sm" className="w-full bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs">
                    Apply Recommended Cloud Fix
                  </Button>
                </div>
              )}

              {/* Quick Actions */}
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs font-semibold"
                  onClick={() => {
                    setIsSimulationActive(true);
                    setSimulatedCompromiseId(selectedNode.id);
                  }}
                >
                  <Play className="w-3 h-3 text-rose-500 mr-1" /> Test Isolation
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Modal: Add Subnet / Network Node */}
      <AnimatePresence>
        {isAddModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden text-left"
            >
              <div className="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
                <div className="flex items-center gap-2">
                  <Plus className="w-5 h-5 text-indigo-600" />
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    Add Network Subnet or Node
                  </h3>
                </div>
                <button
                  onClick={() => setIsAddModalOpen(false)}
                  className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleAddNode} className="p-6 space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-slate-600 dark:text-slate-400 mb-1">
                    Subnet or Node Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Branch Office Laptops or Legal Deposition VLAN"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase text-slate-600 dark:text-slate-400 mb-1">
                      CIDR / IP Range *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. 10.0.60.0/24"
                      value={formData.cidrOrIp}
                      onChange={(e) => setFormData({ ...formData, cidrOrIp: e.target.value })}
                      className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold uppercase text-slate-600 dark:text-slate-400 mb-1">
                      Zone Classification
                    </label>
                    <select
                      value={formData.zone}
                      onChange={(e) => setFormData({ ...formData, zone: e.target.value as any })}
                      className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="workstations">Workstations & Laptops</option>
                      <option value="core">Core & Management</option>
                      <option value="cloud">AWS / Cloud VPC</option>
                      <option value="guest">Guest / IoT</option>
                      <option value="perimeter">Perimeter WAN</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase text-slate-600 dark:text-slate-400 mb-1">
                    Zero-Trust Isolation Policy
                  </label>
                  <div className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                    <input
                      type="checkbox"
                      id="isolated-toggle"
                      checked={formData.isolated}
                      onChange={(e) => setFormData({ ...formData, isolated: e.target.checked })}
                      className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
                    />
                    <label htmlFor="isolated-toggle" className="text-xs text-slate-700 dark:text-slate-300">
                      <strong>Enforce Microsegmentation:</strong> Block all inbound lateral connections from other subnets except through authenticated bastions.
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase text-slate-600 dark:text-slate-400 mb-1">
                    Description / Purpose (Optional)
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Brief note on what devices live on this subnet..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsAddModalOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold"
                  >
                    Add to Network Map
                  </Button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default NetworkTopologyGraph;
