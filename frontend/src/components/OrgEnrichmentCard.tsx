import { useState } from 'react';
import {
    Globe,
    Sparkles,
    RefreshCw,
    AlertCircle,
    CheckCircle,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, Button } from './ui';
import { enrichOrganization } from '../api';
import type { OrganizationWithEnrichment, EnrichmentResult } from '../types';

interface OrgEnrichmentCardProps {
    organization: OrganizationWithEnrichment;
    onEnrichmentComplete: (result: EnrichmentResult) => void;
}

export function OrgEnrichmentCard({ organization, onEnrichmentComplete }: OrgEnrichmentCardProps) {
    const [url, setUrl] = useState(organization.website_url || '');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<EnrichmentResult | null>(
        organization.org_profile ? JSON.parse(organization.org_profile) : null
    );

    const handleEnrich = async () => {
        if (!url) {
            setError('Please enter a website URL');
            return;
        }

        // Basic URL validation
        if (!url.startsWith('http')) {
            setError('URL must start with http:// or https://');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const enrichmentResult = await enrichOrganization(organization.id, url);
            setResult(enrichmentResult);
            onEnrichmentComplete(enrichmentResult);
        } catch (err: any) {
            setError(err.message || 'Failed to enrich organization profile');
        } finally {
            setLoading(false);
        }
    };

    const getConfidenceColor = (score: number) => {
        if (score >= 0.8) return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30';
        if (score >= 0.5) return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30';
        return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
    };

    const getConfidenceLabel = (score: number) => {
        if (score >= 0.8) return 'High Confidence';
        if (score >= 0.5) return 'Medium Confidence';
        return 'Low Confidence';
    };

    return (
        <Card className="h-full">
            <CardHeader>
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                        <Sparkles className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                    </div>
                    <div>
                        <CardTitle className="text-lg">Profile Enrichment</CardTitle>
                        <CardDescription>Automatically infer profile from website</CardDescription>
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* URL Input */}
                <div className="flex gap-2">
                    <div className="relative flex-1">
                        <Globe className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
                        <input
                            type="url"
                            placeholder="https://example.com"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        />
                    </div>
                    <Button
                        onClick={handleEnrich}
                        disabled={loading || !url}
                        className="shrink-0"
                    >
                        {loading ? (
                            <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                        ) : (
                            <Sparkles className="w-4 h-4 mr-2" />
                        )}
                        {loading ? 'Analyzing...' : 'Enrich'}
                    </Button>
                </div>

                {error && (
                    <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-lg flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                        {error}
                    </div>
                )}

                {/* Results Display */}
                {result && (
                    <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 animate-in fade-in slide-in-from-top-2 duration-300">
                        <div className="flex items-start justify-between mb-3">
                            <div>
                                <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                                    {result.title || 'Unknown Title'}
                                </h4>
                                <a
                                    href={result.source_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-gray-500 dark:text-gray-400 hover:underline truncate block max-w-[200px]"
                                >
                                    {result.source_url}
                                </a>
                            </div>
                            <span className={`text-xs px-2 py-1 rounded-full font-medium ${getConfidenceColor(result.confidence)}`}>
                                {getConfidenceLabel(result.confidence)}
                            </span>
                        </div>

                        {result.description && (
                            <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-3">
                                {result.description}
                            </p>
                        )}

                        {result.keywords && result.keywords.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-3">
                                {result.keywords.slice(0, 5).map((kw: string, i: number) => (
                                    <span
                                        key={i}
                                        className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
                                    >
                                        {kw}
                                    </span>
                                ))}
                                {result.keywords.length > 5 && (
                                    <span className="text-xs px-2 py-0.5 text-gray-500">
                                        +{result.keywords.length - 5}
                                    </span>
                                )}
                            </div>
                        )}

                        {result.baseline_suggestion && (
                            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                        Suggested Profile:
                                    </span>
                                    <span className="text-sm font-bold text-primary-600 dark:text-primary-400 capitalize">
                                        {result.baseline_suggestion.replace('_', ' ')}
                                    </span>
                                </div>
                                <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                                    <CheckCircle className="w-3 h-3 text-green-500" />
                                    Apply this baseline in Results page
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
