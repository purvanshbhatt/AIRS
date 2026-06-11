import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Activity } from 'lucide-react';
import { ApiRequestError, getOrganizations, getOrgRemediations, patchRemediation } from '../api';
import type { TrackerItem } from '../types';


export default function RemediationLedger() {
  const [search, setSearch] = useState('');
  const [orgId, setOrgId] = useState<string>('');
  const [orgs, setOrgs] = useState<Array<{ id: string; name: string }>>([]);
  const [tasks, setTasks] = useState<TrackerItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const resolvedCount = tasks.filter((task) => task.status === 'completed' || task.status === 'done').length;

  return (
    
      <motion.div 
        initial={{ opacity: 0 }} 
        animate={{ opacity: 1 }} 
        transition={{ duration: 0.2 }}
        className="p-6 space-y-6 max-w-[1200px] mx-auto"
      >
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-8">
          <div>
            <h1 className="text-xl font-medium tracking-tight mb-2">Remediation Ledger</h1>
            <p className="text-xs text-white/50">Action tracker with live remediation status across assessments.</p>
          </div>
          <div className="surface px-4 py-2 rounded-lg text-xs flex items-center gap-3">
            <span className="text-white/40 font-mono">Progress:</span>
            <div className="text-primary-400 font-mono">{resolvedCount} resolved / {tasks.length} total</div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-white/50 uppercase tracking-widest">Organization</label>
          <select
            value={orgId}
            onChange={(event) => setOrgId(event.target.value)}
            className="bg-white/5 border border-white/10 rounded-md py-1.5 px-3 text-[13px]"
            aria-label="Organization"
          >
            {orgs.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name}
              </option>
            ))}
          </select>
        </div>

        <div className="surface rounded-xl overflow-hidden">
          <div className="p-4 border-b border-white/5 flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
              <input 
                type="text" 
                placeholder="Search ledger..." 
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-md py-1.5 pl-9 pr-3 text-[13px] outline-none focus:border-primary-500/50 transition-colors placeholder:text-white/30"
              />
            </div>
            {error ? <span className="text-[12px] text-red-400">{error}</span> : null}
          </div>

          <div className="w-full">
            <div className="grid grid-cols-12 text-[11px] font-medium text-white/40 uppercase tracking-widest px-4 py-3 border-b border-white/5 bg-white/[0.02]">
              <div className="col-span-2">Task ID</div>
              <div className="col-span-4">Finding</div>
              <div className="col-span-2">Domain</div>
              <div className="col-span-2">Priority</div>
              <div className="col-span-2 text-right">Status</div>
            </div>
            <div className="divide-y divide-white/5">
              {loading ? (
                <div className="py-12 text-center text-[13px] text-white/40">Loading remediations...</div>
              ) : filtered.map(task => (
                <div key={task.id} className="grid grid-cols-12 items-center text-[13px] px-4 py-3 hover:bg-white/5 transition-colors group">
                  <div className="col-span-2 font-mono text-white/60">{task.id.slice(0, 8)}</div>
                  <div className="col-span-4 pr-4 truncate">{task.title}</div>
                  <div className="col-span-2">
                    <span className="px-2 py-0.5 rounded bg-white/5 text-[11px] text-white/70">Assessment</span>
                  </div>
                  <div className="col-span-2 flex items-center gap-2 tabular-nums">
                    <Activity size={12} className={task.priority === 'critical' ? 'text-rose-400' : 'text-primary-400'} />
                    <span className="capitalize">{task.priority}</span>
                  </div>
                  <div className="col-span-2 flex items-center justify-end gap-3">
                    <select
                      value={normalizeStatus(task.status)}
                      onChange={(event) =>
                        handleStatusChange(task.id, event.target.value as 'open' | 'in_progress' | 'resolved')
                      }
                      className="text-[11px] text-white/80 bg-white/5 border border-white/10 rounded px-2 py-1"
                      aria-label={`Status for ${task.title}`}
                    >
                      <option value="open">Open</option>
                      <option value="in_progress">In Progress</option>
                      <option value="resolved">Resolved</option>
                    </select>
                  </div>
                </div>
              ))}
              {filtered.length === 0 && (
                <div className="py-12 text-center text-[13px] text-white/40">No records found matching your criteria.</div>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    
  );
}
