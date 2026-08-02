import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui';
import { getMondayMorning } from '../api';
import { ArrowUp, Activity } from 'lucide-react';

interface ActionableItem {
  id: string;
  title: string;
  impact: number;
}

interface MondayMorningData {
  current_readiness_score: number;
  projected_readiness_score: number;
  actionable_items: ActionableItem[];
}

export default function ExecutiveMondayMorning() {
  const [data, setData] = useState<MondayMorningData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMondayMorning()
      .then((res: any) => {
        setData(res);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch Monday Morning data');
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Executive Monday Morning</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/4"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Executive Monday Morning</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-500 text-sm">{error || 'No data available'}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-emerald-500/20 bg-emerald-50/10 dark:bg-emerald-950/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
          <Activity className="w-5 h-5" />
          Executive Monday Morning
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between p-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div>
            <p className="text-sm text-slate-500 font-semibold mb-1">Current Score</p>
            <p className="text-3xl font-bold">{data.current_readiness_score}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-slate-500 font-semibold mb-1">Projected Readiness</p>
            <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
              <p className="text-3xl font-bold">{data.projected_readiness_score}</p>
              <ArrowUp className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div>
          <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3 uppercase tracking-wider">
            Top Priority Actions
          </h4>
          <div className="space-y-3">
            {data.actionable_items?.map((item) => (
              <div 
                key={item.id} 
                className="flex items-center justify-between p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50"
              >
                <span className="font-medium text-slate-800 dark:text-slate-200">{item.title}</span>
                <span className="inline-flex items-center justify-center px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400">
                  +{item.impact}
                </span>
              </div>
            ))}
            {(!data.actionable_items || data.actionable_items.length === 0) && (
              <p className="text-sm text-slate-500">No actions required.</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
