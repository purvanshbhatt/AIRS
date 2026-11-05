import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui';
import { getEvidenceLineage } from '../api';
import { Network, Database, FileText, CheckCircle, Award, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';

interface EvidenceGraphProps {
  hash?: string;
}

export default function EvidenceGraph({ hash = 'default' }: EvidenceGraphProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hash) return;
    setLoading(true);
    getEvidenceLineage(hash)
      .then((res) => {
        setData(res);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch evidence lineage');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [hash]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Evidence Confidence</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse h-32 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5" /> Evidence Lineage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-rose-500 bg-rose-50 dark:bg-rose-950/30 p-4 rounded-xl">
            <ShieldAlert className="w-5 h-5" />
            <p className="text-sm font-medium">{error || 'Data unavailable'}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const conf = data.confidence || { freshness: 0, completeness: 0, integrity: 0, availability: 0, overall: 0 };
  const nodes = data.nodes || { connector: 'N/A', event: 'N/A', registry: 'N/A', rule: 'N/A', score: 0 };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Network className="w-5 h-5 text-indigo-500" />
          Evidence Lineage & Confidence
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Confidence Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="col-span-2 md:col-span-1 text-center p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/30">
            <p className="text-xs font-semibold text-indigo-500 uppercase">Overall</p>
            <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">{conf.overall}/100</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 flex flex-col justify-center">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Freshness</p>
            <p className="text-xl font-bold">{conf.freshness}%</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 flex flex-col justify-center">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Complete</p>
            <p className="text-xl font-bold">{conf.completeness}%</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 flex flex-col justify-center">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Integrity</p>
            <p className="text-xl font-bold">{conf.integrity}%</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 flex flex-col justify-center">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Availability</p>
            <p className="text-xl font-bold">{conf.availability}%</p>
          </div>
        </div>

        {/* Lineage Graph */}
        <div className="p-6 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-800 overflow-x-auto">
          <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-8 uppercase tracking-wider text-center">
            Lineage Path
          </h4>
          
          <div className="flex items-center justify-between relative min-w-[500px] px-4 pb-4">
            <div className="absolute top-1/2 left-8 right-8 h-1 bg-slate-200 dark:bg-slate-700 -translate-y-1/2 z-0"></div>
            
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="z-10 flex flex-col items-center gap-2 bg-white dark:bg-slate-950 p-3 rounded-xl border-2 border-blue-500/20 shadow-sm w-24">
              <Database className="w-6 h-6 text-blue-500" />
              <span className="text-[10px] font-bold uppercase text-center break-words w-full truncate" title={nodes.connector}>{nodes.connector}</span>
            </motion.div>
            
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="z-10 flex flex-col items-center gap-2 bg-white dark:bg-slate-950 p-3 rounded-xl border-2 border-emerald-500/20 shadow-sm w-24">
              <FileText className="w-6 h-6 text-emerald-500" />
              <span className="text-[10px] font-bold uppercase text-center break-words w-full truncate" title={nodes.event}>{nodes.event}</span>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="z-10 flex flex-col items-center gap-2 bg-white dark:bg-slate-950 p-3 rounded-xl border-2 border-purple-500/20 shadow-sm w-24">
              <Database className="w-6 h-6 text-purple-500" />
              <span className="text-[10px] font-bold uppercase text-center break-words w-full truncate" title={nodes.registry}>{nodes.registry}</span>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="z-10 flex flex-col items-center gap-2 bg-white dark:bg-slate-950 p-3 rounded-xl border-2 border-orange-500/20 shadow-sm w-24">
              <CheckCircle className="w-6 h-6 text-orange-500" />
              <span className="text-[10px] font-bold uppercase text-center break-words w-full truncate" title={nodes.rule}>{nodes.rule}</span>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="z-10 flex flex-col items-center gap-2 bg-indigo-500 p-3 rounded-xl border-2 border-indigo-600 shadow-sm text-white w-24">
              <Award className="w-6 h-6" />
              <span className="text-[11px] font-bold uppercase text-center">Score: {nodes.score}</span>
            </motion.div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
