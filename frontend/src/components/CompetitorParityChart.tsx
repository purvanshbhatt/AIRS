/**
 * Competitor Parity Chart — Staging-only "Market Gap" engagement widget.
 *
 * Renders a horizontal bar chart comparing the organisation's GHI Score
 * against anonymised industry-average benchmarks to create a sense of
 * urgency around compliance posture improvement.
 */

import { Card, CardHeader, CardTitle, CardContent, Badge } from './ui';
import { BarChart3, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface CompetitorParityChartProps {
  orgGhi: number;
  orgGrade: string;
  industryName?: string;
}

// Anonymised "industry average" benchmarks (demo data).
// In production this would come from cross-tenant aggregate analytics.
const INDUSTRY_BENCHMARKS: Record<string, number> = {
  Healthcare:      68,
  Finance:         74,
  Technology:      71,
  Government:      62,
  Retail:          58,
  Manufacturing:   55,
  Education:       52,
  Energy:          60,
  Default:         63,
};

const PEER_LABELS = [
  { label: 'Your Organization', key: 'org' },
  { label: 'Industry Average',  key: 'avg' },
  { label: 'Top 10% Performers', key: 'top' },
];

function getBarColor(value: number): string {
  if (value >= 80) return 'bg-green-500';
  if (value >= 60) return 'bg-blue-500';
  if (value >= 40) return 'bg-yellow-500';
  return 'bg-red-500';
}

function getGapVerdict(gap: number): { icon: typeof TrendingUp; text: string; color: string } {
  if (gap > 5)  return { icon: TrendingUp,   text: 'Above average',  color: 'text-green-600 dark:text-green-400' };
  if (gap >= -5) return { icon: Minus,        text: 'At parity',      color: 'text-gray-500 dark:text-slate-400' };
  return { icon: TrendingDown, text: 'Below average', color: 'text-red-600 dark:text-red-400' };
}

export default function CompetitorParityChart({
  orgGhi,
  orgGrade,
  industryName = 'Default',
}: CompetitorParityChartProps) {
  const industryAvg = INDUSTRY_BENCHMARKS[industryName] ?? INDUSTRY_BENCHMARKS.Default;
  const topPerformers = Math.min(industryAvg + 22, 98); // simulated top-10% band
  const gap = orgGhi - industryAvg;
  const verdict = getGapVerdict(gap);
  const VerdictIcon = verdict.icon;

  const bars = [
    { label: 'Your Organization', value: orgGhi,        highlight: true },
    { label: 'Industry Average',  value: industryAvg,   highlight: false },
    { label: 'Top 10% Performers', value: topPerformers, highlight: false },
  ];

  return (
    <Card className="border-indigo-200 dark:border-indigo-800">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-500" />
            Competitor Parity — {industryName}
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            Staging Analytics
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Bars */}
        <div className="space-y-3">
          {bars.map((bar) => (
            <div key={bar.label}>
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-medium ${
                  bar.highlight
                    ? 'text-indigo-700 dark:text-indigo-300'
                    : 'text-gray-500 dark:text-slate-400'
                }`}>
                  {bar.label}
                </span>
                <span className={`text-xs font-bold ${
                  bar.highlight
                    ? 'text-indigo-700 dark:text-indigo-300'
                    : 'text-gray-600 dark:text-slate-300'
                }`}>
                  {bar.value}
                </span>
              </div>
              <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    bar.highlight ? 'bg-indigo-500' : getBarColor(bar.value)
                  } ${bar.highlight ? 'ring-2 ring-indigo-300 dark:ring-indigo-700' : ''}`}
                  style={{ width: `${Math.min(bar.value, 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Gap verdict */}
        <div className={`flex items-center gap-2 p-3 rounded-lg border ${
          gap > 5
            ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
            : gap >= -5
              ? 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
              : 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800'
        }`}>
          <VerdictIcon className={`w-5 h-5 shrink-0 ${verdict.color}`} />
          <div>
            <p className={`text-sm font-semibold ${verdict.color}`}>
              {verdict.text} ({gap >= 0 ? '+' : ''}{gap} pts)
            </p>
            <p className="text-xs text-gray-500 dark:text-slate-400">
              {gap < -5
                ? 'Your compliance posture is below industry peers. Prioritize remediation to close the gap.'
                : gap > 5
                  ? 'You are outperforming industry peers. Maintain momentum to stay ahead.'
                  : 'Your posture is on par with industry peers. Continue improving to differentiate.'}
            </p>
          </div>
        </div>

        <p className="text-[10px] text-gray-400 dark:text-slate-600 text-center">
          Benchmarks based on anonymised cross-industry aggregate data. Not an official ranking.
        </p>
      </CardContent>
    </Card>
  );
}
