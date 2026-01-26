import { useMemo } from 'react';
import type { ScoreTrendPoint } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from './ui';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface ScoreTrendChartProps {
    data: ScoreTrendPoint[];
    height?: number;
}

export function ScoreTrendChart({ data, height = 200 }: ScoreTrendChartProps) {
    const sortedData = useMemo(() => {
        return [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    }, [data]);

    if (sortedData.length < 2) {
        return (
            <Card className="h-full flex items-center justify-center p-6 text-gray-500 text-sm">
                Not enough data for trend analysis
            </Card>
        );
    }

    // Calculate scales
    const minScore = 0; // Always show full context
    const maxScore = 100;

    // Create path
    const points = sortedData.map((d, i) => {
        const x = (i / (sortedData.length - 1)) * 100;
        const y = 100 - ((d.score - minScore) / (maxScore - minScore)) * 100;
        return `${x},${y}`;
    }).join(' ');

    const currentScore = sortedData[sortedData.length - 1].score;
    const previousScore = sortedData[sortedData.length - 2].score;
    const trend = currentScore - previousScore;

    return (
        <Card className="h-full">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-gray-500" />
                        Readiness Trend
                    </CardTitle>
                    <div className={`flex items-center gap-1 text-sm font-medium ${trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-600'
                        }`}>
                        {trend > 0 ? <TrendingUp className="w-4 h-4" /> : trend < 0 ? <TrendingDown className="w-4 h-4" /> : null}
                        {trend > 0 ? '+' : ''}{Math.round(trend)} points
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="relative w-full" style={{ height: `${height}px` }}>
                    <svg
                        viewBox="0 0 100 100"
                        className="w-full h-full overflow-visible"
                        preserveAspectRatio="none"
                    >
                        {/* Grid lines */}
                        <line x1="0" y1="0" x2="100" y2="0" stroke="#e5e7eb" strokeWidth="0.5" strokeDasharray="2" />
                        <line x1="0" y1="50" x2="100" y2="50" stroke="#e5e7eb" strokeWidth="0.5" strokeDasharray="2" />
                        <line x1="0" y1="100" x2="100" y2="100" stroke="#e5e7eb" strokeWidth="0.5" strokeDasharray="2" />

                        {/* Area fill */}
                        <path
                            d={`M0,100 L${points} L100,100 Z`}
                            fill="url(#trendGradient)"
                            opacity="0.2"
                        />
                        <defs>
                            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="var(--primary-color, #3b82f6)" />
                                <stop offset="100%" stopColor="white" stopOpacity="0" />
                            </linearGradient>
                        </defs>

                        {/* Line */}
                        <polyline
                            fill="none"
                            stroke="var(--primary-color, #3b82f6)"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            points={points}
                            vectorEffect="non-scaling-stroke"
                        />

                        {/* Dots */}
                        {sortedData.map((d, i) => {
                            const x = (i / (sortedData.length - 1)) * 100;
                            const y = 100 - ((d.score - minScore) / (maxScore - minScore)) * 100;
                            return (
                                <circle
                                    key={i}
                                    cx={x}
                                    cy={y}
                                    r="1.5"
                                    className="fill-white stroke-primary-600"
                                    strokeWidth="0.5"
                                    vectorEffect="non-scaling-stroke"
                                >
                                    <title>{d.name}: {Math.round(d.score)} ({new Date(d.date).toLocaleDateString()})</title>
                                </circle>
                            );
                        })}
                    </svg>
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-2">
                    <span>{new Date(sortedData[0].date).toLocaleDateString()}</span>
                    <span>{new Date(sortedData[sortedData.length - 1].date).toLocaleDateString()}</span>
                </div>
            </CardContent>
        </Card>
    );
}
