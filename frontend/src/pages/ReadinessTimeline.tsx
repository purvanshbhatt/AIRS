import { useState } from 'react';
import { motion } from 'framer-motion';
import { ShieldAlert, FileSearch, Activity, ShieldCheck, Box, FileKey2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Badge } from '../components/ui';

export default function ReadinessTimeline() {
  const [selectedOrgId] = useState('org_default');

  const timelineEvents = [
    {
      id: 1,
      date: 'July 20',
      delta: 2,
      reason: 'CrowdStrike Falcon host verified via Wazuh',
      icon: ShieldCheck,
      category: 'telemetry',
    },
    {
      id: 2,
      date: 'July 21',
      delta: -4,
      reason: 'Python 3.8 reached End of Life (EOL) across 3 production services',
      icon: Box,
      category: 'lifecycle',
    },
    {
      id: 3,
      date: 'July 22',
      delta: -3,
      reason: 'Critical KEV (CVE-2024-9143) published for OpenSSL',
      icon: ShieldAlert,
      category: 'threat',
    },
    {
      id: 4,
      date: 'July 23',
      delta: 1,
      reason: 'MFA explicitly verified across critical GitHub repositories',
      icon: FileKey2,
      category: 'governance',
    }
  ];

  let currentScore = 79;
  const eventsWithScores = [...timelineEvents].reverse().map(event => {
    const scoreBefore = currentScore - event.delta;
    const current = currentScore;
    currentScore = scoreBefore;
    return { ...event, currentScore: current, previousScore: scoreBefore };
  }).reverse();

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-display text-slate-900 dark:text-slate-100 flex items-center gap-3">
            <Activity className="w-8 h-8 text-primary-500" />
            Readiness Timeline
          </h1>
          <p className="text-body text-slate-600 dark:text-slate-400 mt-2">
            Historical trace of all deterministic events impacting your incident readiness score.
          </p>
        </div>
      </div>

      <div className="max-w-4xl">
        <div className="relative border-l-2 border-slate-200 dark:border-slate-800 ml-6 pl-8 py-4 space-y-12">
          {eventsWithScores.map((event, index) => {
            const Icon = event.icon;
            const isPositive = event.delta > 0;
            return (
              <motion.div 
                key={event.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative"
              >
                {/* Timeline Node */}
                <div className={`absolute -left-[41px] p-1.5 rounded-full border-4 border-white dark:border-slate-900 ${
                  isPositive ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'
                }`}>
                  <Icon className="w-4 h-4" />
                </div>

                <Card className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                          {event.date}
                        </span>
                        <Badge variant={isPositive ? 'success' : 'danger'} className="font-mono text-xs">
                          {isPositive ? '+' : ''}{event.delta}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 font-mono">
                        <span className="text-slate-400">{event.previousScore}</span>
                        <span className="text-slate-300">→</span>
                        <span className={`font-bold ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
                          {event.currentScore}
                        </span>
                      </div>
                    </div>
                    <p className="text-lg font-medium text-slate-900 dark:text-slate-100">
                      {event.reason}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
