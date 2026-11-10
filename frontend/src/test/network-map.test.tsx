import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent, within } from '@testing-library/react';
import React from 'react';
import * as api from '../api';
import * as useActiveOrgIdHook from '../hooks/useActiveOrgId';
import { NetworkMap } from '../components/network/NetworkMap';
import { renderWithRouter } from './utils/test-helpers';

// vitest/jsdom cannot drive canvas or WebGL. Replace both graph libraries with a
// tiny DOM stand-in that exposes the data wiring and fires the same callbacks.
vi.mock('react-force-graph-2d', () => ({
  default: React.forwardRef(function FakeGraph2D(props: any, ref: any) {
    React.useImperativeHandle(ref, () => ({ zoomToFit: vi.fn() }));
    return (
      <div data-testid="fake-graph-2d" data-node-count={props.graphData.nodes.length} data-link-count={props.graphData.links.length} data-bg={props.backgroundColor}>
        {props.graphData.nodes.map((n: any) => (
          <button key={n.id} type="button" data-testid={`gnode-${n.id}`} onClick={() => props.onNodeClick(n)} onMouseEnter={() => props.onNodeHover?.(n)}>
            {n.label}
          </button>
        ))}
      </div>
    );
  }),
}));

// 3d-force-graph is imperative: every setter returns the instance. Mirror the
// node count onto the host element so the test can assert the data wiring.
vi.mock('3d-force-graph', () => ({
  default: class FakeForceGraph3D {
    constructor(host: HTMLElement) {
      host.setAttribute('data-testid', 'fake-graph-3d');
      const proxy: any = new Proxy(this, {
        get(_target, prop) {
          if (prop === 'graphData') {
            return (data: any) => {
              host.setAttribute('data-node-count', String(data.nodes.length));
              return proxy;
            };
          }
          if (prop === 'renderer') return () => ({ setPixelRatio: vi.fn() });
          if (prop === '_destructor') return () => undefined;
          return () => proxy;
        },
      });
      return proxy;
    }
  },
}));

vi.mock('../api');
vi.mock('../hooks/useActiveOrgId');

const topology: api.NetworkTopologyResponse = {
  generated_at: new Date().toISOString(),
  org_id: 'org-net-1',
  demo: false,
  nodes: [
    { id: 'connector:aws', type: 'connector', label: 'AWS Security Hub', sublabel: 'Connected system', status: 'healthy', zone: 'security', meta: { issues: [], seen_by: [], last_seen: null, connector_type: 'aws_security_hub' } },
    { id: 'aws:instance:i-1', type: 'server', label: 'clinic-ehr-app-server', sublabel: 'ehr-app-server · t3.micro', status: 'attention', zone: 'servers',
      meta: { issues: [{ title: 'Instance queried a known command and control server', severity: 'high' }], seen_by: ['AWS Security Hub'], last_seen: new Date().toISOString(), instance_type: 't3.micro', internet_exposed: true } },
    { id: 'aws:sg:sg-1', type: 'security_group', label: 'sg-1', sublabel: 'Security group (firewall rules)', status: 'attention', zone: 'cloud', meta: { issues: [{ title: 'Security groups should not allow unrestricted access', severity: 'critical' }], seen_by: ['AWS Security Hub'], last_seen: null, internet_exposed: true } },
    { id: 'ms:device:d-1', type: 'workstation', label: 'FRONT-DESK-PC', sublabel: 'Intune · 10.0.19044', status: 'warning', zone: 'workstations', meta: { issues: [{ title: 'Disk is not encrypted', severity: 'medium' }], seen_by: ['Microsoft 365'], last_seen: null } },
    { id: 'internet', type: 'internet', label: 'Internet', sublabel: 'Anyone, anywhere', status: 'unknown', zone: 'internet', meta: { issues: [], seen_by: [], last_seen: null } },
  ],
  edges: [
    { source: 'connector:aws', target: 'aws:instance:i-1', kind: 'monitors', label: 'monitors' },
    { source: 'connector:aws', target: 'aws:sg:sg-1', kind: 'monitors', label: 'monitors' },
    { source: 'internet', target: 'aws:sg:sg-1', kind: 'exposed_to_internet', label: 'open to the internet' },
  ],
  summary: {
    empty: false,
    node_count: 5,
    edge_count: 3,
    connectors: 1,
    attention: 2,
    internet_exposed: 1,
    by_type: { connector: 1, server: 1, security_group: 1, workstation: 1, internet: 1 },
    by_zone: { security: 1, servers: 1, cloud: 1, workstations: 1, internet: 1 },
    by_status: { healthy: 1, attention: 2, warning: 1, unknown: 1 },
  },
};

const emptyTopology: api.NetworkTopologyResponse = {
  generated_at: new Date().toISOString(),
  nodes: [],
  edges: [],
  summary: { empty: true, hint: 'connect a system', node_count: 0, edge_count: 0, connectors: 0, attention: 0, internet_exposed: 0, by_type: {}, by_zone: {}, by_status: {} },
};

describe('NetworkMap', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(useActiveOrgIdHook, 'useActiveOrgId').mockReturnValue('org-net-1');
  });

  it('fetches the topology for the active org and wires nodes and edges into the graph', async () => {
    vi.mocked(api.getNetworkTopology).mockResolvedValue(topology);
    renderWithRouter(<NetworkMap />);

    expect(screen.getByTestId('network-map-loading')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId('network-map')).toBeInTheDocument());

    expect(api.getNetworkTopology).toHaveBeenCalledWith('org-net-1');
    const graph = screen.getByTestId('fake-graph-2d');
    expect(graph.getAttribute('data-node-count')).toBe('5');
    expect(graph.getAttribute('data-link-count')).toBe('3');
    expect(graph.getAttribute('data-bg')).toBeTruthy();

    // Summary strip reads from summary, not from hardcoded numbers.
    expect(screen.getByText('Systems on the map').nextSibling?.textContent).toBe('5');
    expect(screen.getByText('Reachable from the internet').nextSibling?.textContent).toBe('1');
  });

  it('renders a legend and zone/status filter chips from the data', async () => {
    vi.mocked(api.getNetworkTopology).mockResolvedValue(topology);
    renderWithRouter(<NetworkMap />);
    await waitFor(() => expect(screen.getByTestId('network-map')).toBeInTheDocument());

    const legend = screen.getByTestId('network-map-legend');
    expect(within(legend).getByText('Servers')).toBeInTheDocument();
    expect(within(legend).getByText('Staff computers')).toBeInTheDocument();
    expect(within(legend).queryByText('Backups')).not.toBeInTheDocument(); // zone absent from data
    expect(within(legend).getByText('needs attention')).toBeInTheDocument();

    const zoneGroup = screen.getByRole('group', { name: 'Filter by zone' });
    const serversChip = within(zoneGroup).getByRole('button', { name: /Servers/ });
    fireEvent.click(serversChip);
    expect(serversChip).toHaveAttribute('aria-pressed', 'true');

    // Only the server node is left; edges touching hidden nodes drop out.
    await waitFor(() => expect(screen.getByTestId('fake-graph-2d').getAttribute('data-node-count')).toBe('1'));
    expect(screen.getByTestId('fake-graph-2d').getAttribute('data-link-count')).toBe('0');

    fireEvent.click(serversChip); // back to everything
    await waitFor(() => expect(screen.getByTestId('fake-graph-2d').getAttribute('data-node-count')).toBe('5'));

    const statusGroup = screen.getByRole('group', { name: 'Filter by status' });
    fireEvent.click(within(statusGroup).getByRole('button', { name: /Needs attention/ }));
    await waitFor(() => expect(screen.getByTestId('fake-graph-2d').getAttribute('data-node-count')).toBe('2'));
  });

  it('opens a plain-English side panel when a node is clicked', async () => {
    vi.mocked(api.getNetworkTopology).mockResolvedValue(topology);
    renderWithRouter(<NetworkMap />);
    await waitFor(() => expect(screen.getByTestId('network-map')).toBeInTheDocument());

    expect(screen.queryByTestId('network-node-panel')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('gnode-aws:instance:i-1'));

    const panel = await screen.findByTestId('network-node-panel');
    expect(within(panel).getByRole('heading', { name: 'clinic-ehr-app-server' })).toBeInTheDocument();
    expect(within(panel).getByText(/Server · Servers/)).toBeInTheDocument();
    expect(within(panel).getByText('Needs attention')).toBeInTheDocument();
    expect(within(panel).getByText(/Open issues \(1\)/)).toBeInTheDocument();
    expect(within(panel).getByText('Instance queried a known command and control server')).toBeInTheDocument();
    expect(within(panel).getByText('AWS Security Hub', { selector: 'p' })).toBeInTheDocument(); // seen by
    expect(within(panel).getByText(/Anyone on the internet can reach this/)).toBeInTheDocument();
    expect(within(panel).getByText(/AWS Security Hub watches over this/)).toBeInTheDocument();

    // Jump through a connection, then close.
    fireEvent.click(within(panel).getByRole('button', { name: /AWS Security Hub watches over this/ }));
    await waitFor(() =>
      expect(within(screen.getByTestId('network-node-panel')).getByRole('heading', { name: 'AWS Security Hub' })).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByRole('button', { name: 'Close details' }));
    await waitFor(() => expect(screen.queryByTestId('network-node-panel')).not.toBeInTheDocument());
  });

  it('shows a hover tooltip with the node description', async () => {
    vi.mocked(api.getNetworkTopology).mockResolvedValue(topology);
    renderWithRouter(<NetworkMap />);
    await waitFor(() => expect(screen.getByTestId('network-map')).toBeInTheDocument());

    fireEvent.mouseEnter(screen.getByTestId('gnode-ms:device:d-1'));
    const tooltip = await screen.findByRole('tooltip');
    expect(within(tooltip).getByText('FRONT-DESK-PC')).toBeInTheDocument();
    expect(within(tooltip).getByText(/Worth a look/)).toBeInTheDocument();
  });

  it('falls back to 2D with a notice when WebGL is unavailable, and lazy-loads 3D when it is', async () => {
    vi.mocked(api.getNetworkTopology).mockResolvedValue(topology);
    renderWithRouter(<NetworkMap />);
    await waitFor(() => expect(screen.getByTestId('network-map')).toBeInTheDocument());

    // jsdom has no WebGL: the toggle must degrade gracefully.
    fireEvent.click(screen.getByRole('button', { name: /3D/ }));
    expect(screen.getByText(/3D needs WebGL/)).toBeInTheDocument();
    expect(screen.getByTestId('fake-graph-2d')).toBeInTheDocument();

    // Pretend WebGL exists: the 3D chunk loads via Suspense.
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({}) as any;
    try {
      fireEvent.click(screen.getByRole('button', { name: /3D/ }));
      await waitFor(() => expect(screen.getByTestId('fake-graph-3d')).toBeInTheDocument());
      expect(screen.getByTestId('fake-graph-3d').getAttribute('data-node-count')).toBe('5');
      expect(screen.queryByText(/3D needs WebGL/)).not.toBeInTheDocument();
      fireEvent.click(screen.getByRole('button', { name: /2D/ }));
      await waitFor(() => expect(screen.getByTestId('fake-graph-2d')).toBeInTheDocument());
    } finally {
      HTMLCanvasElement.prototype.getContext = original;
    }
  });

  it('shows the plain-English empty state with a link to connectors when nothing is connected', async () => {
    vi.mocked(api.getNetworkTopology).mockResolvedValue(emptyTopology);
    renderWithRouter(<NetworkMap />);

    await waitFor(() => expect(screen.getByTestId('network-map-empty')).toBeInTheDocument());
    expect(screen.getByText('Nothing is connected yet')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Connect a system' })).toHaveAttribute('href', '/connectors');
    expect(screen.queryByTestId('fake-graph-2d')).not.toBeInTheDocument();
  });

  it('shows a demo notice when the backend flags the org as demo', async () => {
    vi.mocked(api.getNetworkTopology).mockResolvedValue({ ...topology, demo: true });
    renderWithRouter(<NetworkMap orgId="demo-northstar-health" />);
    await waitFor(() => expect(screen.getByTestId('network-map')).toBeInTheDocument());
    expect(api.getNetworkTopology).toHaveBeenCalledWith('demo-northstar-health');
    expect(screen.getByText(/Demo workspace/)).toBeInTheDocument();
  });

  it('shows networks, VPN links and where the data comes from', async () => {
    const withNetworks: api.NetworkTopologyResponse = {
      ...topology,
      nodes: [
        ...topology.nodes,
        { id: 'net:aws:vpc-1', type: 'network', label: 'clinic-vpc', sublabel: '10.20.0.0/16', status: 'healthy', zone: 'network', meta: { issues: [], seen_by: ['Amazon Web Services'], last_seen: null, cidr: '10.20.0.0/16', network_kind: 'vpc' } },
        { id: 'subnet:aws:subnet-1', type: 'subnet', label: 'private-a', sublabel: '10.20.1.0/24', status: 'healthy', zone: 'network', meta: { issues: [], seen_by: [], last_seen: null, cidr: '10.20.1.0/24' } },
        { id: 'vpn:aws:vpn-1', type: 'vpn', label: 'Office to cloud VPN', sublabel: 'Site-to-site VPN', status: 'warning', zone: 'network', meta: { issues: [{ title: 'One VPN tunnel is down', severity: 'medium' }], seen_by: [], last_seen: null, vpn_kind: 'site_to_site', tunnels_up: 1, tunnels_total: 2 } },
        { id: 'gw:aws:igw-1', type: 'gateway', label: 'Internet gateway', sublabel: null, status: 'healthy', zone: 'network', meta: { issues: [], seen_by: [], last_seen: null, gateway_kind: 'internet_gateway' } },
      ],
      edges: [
        ...topology.edges,
        { source: 'aws:instance:i-1', target: 'subnet:aws:subnet-1', kind: 'member_of', label: 'is on' },
        { source: 'subnet:aws:subnet-1', target: 'net:aws:vpc-1', kind: 'part_of', label: 'is part of' },
        { source: 'net:aws:vpc-1', target: 'gw:aws:igw-1', kind: 'routes_to', label: 'routes to' },
        { source: 'gw:aws:igw-1', target: 'internet', kind: 'routes_to', label: 'routes to' },
        { source: 'vpn:aws:vpn-1', target: 'net:aws:vpc-1', kind: 'vpn_tunnel', label: 'VPN tunnel' },
        { source: 'ms:device:d-1', target: 'aws:instance:i-1', kind: 'talks_to', label: 'tcp/443' },
      ],
      summary: { ...topology.summary, node_count: 9, edge_count: 9, networks: 1, vpns: 1, vpn_down: 0 },
      live: {
        mode: 'live',
        latest_event_at: new Date().toISOString(),
        sources: [{ id: 'connector:aws', type: 'aws', label: 'Amazon Web Services', status: 'healthy', last_sync_at: new Date().toISOString(), event_count: 4 }],
      },
    };
    vi.mocked(api.getNetworkTopology).mockResolvedValue(withNetworks);
    renderWithRouter(<NetworkMap />);
    await waitFor(() => expect(screen.getByTestId('network-map')).toBeInTheDocument());

    // Extra stats appear only because the data has networks and a VPN.
    expect(screen.getByText('Networks').nextSibling?.textContent).toBe('1');
    expect(screen.getByText('VPN links').nextSibling?.textContent).toBe('1');

    // The live strip names the feeding system and says the map is live.
    const live = screen.getByTestId('network-map-live');
    expect(within(live).getByText('Live')).toBeInTheDocument();
    expect(within(live).getByText('Amazon Web Services')).toBeInTheDocument();
    expect(within(live).getByText(/refreshes by itself/)).toBeInTheDocument();

    // Search finds a network by its address range and opens it.
    fireEvent.change(screen.getByRole('searchbox', { name: /Find a device or network/ }), { target: { value: '10.20.0' } });
    fireEvent.click(within(screen.getByRole('listbox', { name: 'Matching systems' })).getByText('clinic-vpc'));
    let panel = await screen.findByTestId('network-node-panel');
    expect(within(panel).getByRole('heading', { name: 'clinic-vpc' })).toBeInTheDocument();
    expect(within(panel).getByText('Cloud network')).toBeInTheDocument(); // network_kind in plain words
    expect(within(panel).getByText(/Office to cloud VPN tunnels to this/)).toBeInTheDocument();

    // A device shows its way out: segment, network, gateway, internet.
    fireEvent.click(screen.getByTestId('gnode-aws:instance:i-1'));
    await waitFor(() =>
      expect(within(screen.getByTestId('network-node-panel')).getByRole('heading', { name: 'clinic-ehr-app-server' })).toBeInTheDocument(),
    );
    panel = screen.getByTestId('network-node-panel');
    const route = within(panel).getByTestId('network-node-route');
    expect(within(route).getAllByRole('button').map((b) => b.textContent)).toEqual([
      'private-a', 'clinic-vpc', 'Internet gateway', 'Internet',
    ]);
    expect(within(panel).getByText(/FRONT-DESK-PC talks to this \(tcp\/443\)/)).toBeInTheDocument();
  });

  it('labels a workspace with nothing reporting as waiting, not live', async () => {
    vi.mocked(api.getNetworkTopology).mockResolvedValue({ ...topology, live: { mode: 'live', latest_event_at: null, sources: [] } });
    renderWithRouter(<NetworkMap />);
    await waitFor(() => expect(screen.getByTestId('network-map')).toBeInTheDocument());
    const live = screen.getByTestId('network-map-live');
    expect(within(live).getByText('Waiting for data')).toBeInTheDocument();
    expect(within(live).queryByText('Live')).not.toBeInTheDocument();
  });

  it('surfaces a retry when the request fails', async () => {
    vi.mocked(api.getNetworkTopology).mockRejectedValueOnce(new Error('boom')).mockResolvedValueOnce(topology);
    renderWithRouter(<NetworkMap />);
    await waitFor(() => expect(screen.getByText('We could not load the network map.')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /Try again/ }));
    await waitFor(() => expect(screen.getByTestId('network-map')).toBeInTheDocument());
    expect(api.getNetworkTopology).toHaveBeenCalledTimes(2);
  });
});
