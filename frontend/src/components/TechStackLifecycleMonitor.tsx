import { Card, CardHeader, CardTitle, CardDescription, CardContent, Badge } from './ui';
import { Cpu, CheckCircle2, AlertTriangle, XCircle, ShieldAlert } from 'lucide-react';

interface TechStackItem {
  id: string;
  component_name: string;
  version: string;
  category: string;
  lts_status: 'lts' | 'active' | 'deprecated' | 'eol';
  major_versions_behind: number;
}

interface TechStackLifecycleMonitorProps {
  items: TechStackItem[];
}

const mapCategory = (cat: string) => {
  if (cat === 'Language Runtime') return 'Runtime';
  if (cat === 'Framework') return 'Framework';
  if (cat === 'Database') return 'Database';
  if (cat === 'Library') return 'Library';
  return cat;
};

export default function TechStackLifecycleMonitor({ items }: TechStackLifecycleMonitorProps) {
  // Filter only relevant items (Runtime, Framework, Database, Library)
  const targetCategories = ['Language Runtime', 'Framework', 'Database', 'Library'];
  const filteredItems = items.filter((item) => targetCategories.includes(item.category));

  const getRiskBadge = (item: TechStackItem) => {
    if (item.lts_status === 'eol' || item.major_versions_behind >= 2) {
      return (
        <Badge variant="critical" className="rounded-full px-2.5 py-0.5 font-bold flex items-center w-fit gap-1 bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400 border border-red-200 dark:border-red-900/30">
          <XCircle className="w-3.5 h-3.5" />
          Critical Drift
        </Badge>
      );
    }
    if (item.lts_status === 'deprecated' || item.major_versions_behind === 1) {
      return (
        <Badge variant="drift" className="rounded-full px-2.5 py-0.5 font-bold flex items-center w-fit gap-1 bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-200 dark:border-amber-900/30">
          <AlertTriangle className="w-3.5 h-3.5" />
          Minor Drift
        </Badge>
      );
    }
    return (
      <Badge className="rounded-full px-2.5 py-0.5 font-bold flex items-center w-fit gap-1 bg-emerald-100 text-[#00C853] dark:bg-emerald-950/40 dark:text-[#00C853] border border-emerald-200 dark:border-emerald-900/30">
        <CheckCircle2 className="w-3.5 h-3.5" />
        Secure
      </Badge>
    );
  };

  return (
    <Card className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20 backdrop-blur-md shadow-sm hover:shadow-md transition-all duration-300">
      <CardHeader>
        <CardTitle className="text-lg font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-indigo-500" />
          Tech Stack Lifecycle Monitor
        </CardTitle>
        <CardDescription className="text-xs font-semibold">
          Component governance tracking version drift against production baselines.
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-2">
        {filteredItems.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500 dark:text-slate-400 italic">
            No runtime, framework, database, or library components configured in registry.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-900/20 text-slate-500 dark:text-slate-450">
                  <th className="py-2.5 px-4 font-bold uppercase tracking-wider">Component</th>
                  <th className="py-2.5 px-4 font-bold uppercase tracking-wider">Type</th>
                  <th className="py-2.5 px-4 font-bold uppercase tracking-wider">Version</th>
                  <th className="py-2.5 px-4 font-bold uppercase tracking-wider">Drift</th>
                  <th className="py-2.5 px-4 font-bold uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={item.id} className="border-b border-slate-100 dark:border-slate-900 hover:bg-slate-50/50 dark:hover:bg-slate-900/10 transition-colors">
                    <td className="py-3 px-4 font-extrabold text-slate-900 dark:text-slate-100">{item.component_name}</td>
                    <td className="py-3 px-4 text-slate-550 dark:text-slate-400 font-semibold">{mapCategory(item.category)}</td>
                    <td className="py-3 px-4 font-mono text-slate-700 dark:text-slate-350">{item.version}</td>
                    <td className="py-3 px-4 font-semibold text-slate-600 dark:text-slate-400">
                      {item.major_versions_behind === 0 
                        ? 'Current' 
                        : `${item.major_versions_behind} major version${item.major_versions_behind > 1 ? 's' : ''} behind`
                      }
                    </td>
                    <td className="py-3 px-4">{getRiskBadge(item)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
