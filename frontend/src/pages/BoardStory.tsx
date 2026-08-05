import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Brain, Download, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button, Badge } from '../components/ui';
import { getOrganizations, getBoardStory, ApiRequestError, BoardStory as BoardStoryType, getBoardStoryPdfUrl } from '../api';
import type { Organization } from '../types';

/** UUID v4 guard — prevents API calls with garbage org IDs crafted in the URL */
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const isValidOrgId = (id: string) => UUID_RE.test(id);

export function BoardStory() {
  const [searchParams] = useSearchParams();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState(searchParams.get('org') || '');
  const [story, setStory] = useState<BoardStoryType | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<string>('');

  // Fixed list of 10 standard sections expected by the board narrative
  const standardSections = [
    { id: 'sec-1', defaultTitle: 'Executive Summary', icon: '1' },
    { id: 'sec-2', defaultTitle: 'Overall Posture Analysis', icon: '2' },
    { id: 'sec-3', defaultTitle: 'Telemetry Health Check Status', icon: '3' },
    { id: 'sec-4', defaultTitle: 'Critical Vulnerabilities (KEVs)', icon: '4' },
    { id: 'sec-5', defaultTitle: 'Software Lifecycle & EOL Risks', icon: '5' },
    { id: 'sec-6', defaultTitle: 'Compliance Alignment Details', icon: '6' },
    { id: 'sec-7', defaultTitle: 'Remediation Progress & Backlog', icon: '7' },
    { id: 'sec-8', defaultTitle: 'SLA Breaches & Response Velocity', icon: '8' },
    { id: 'sec-9', defaultTitle: 'AI Governance (Shadow AI)', icon: '9' },
    { id: 'sec-10', defaultTitle: 'Actionable Mitigation Roadmap', icon: '10' },
  ];

  useEffect(() => {
    getOrganizations()
      .then((orgs) => {
        setOrganizations(orgs);
        if (!selectedOrgId && orgs.length > 0) {
          setSelectedOrgId(orgs[0].id);
        }
      })
      .catch(() => {});
  }, []);

  const loadStory = async () => {
    if (!selectedOrgId) return;
    // Guard: prevent API calls with crafted non-UUID org IDs (F-009 / T-H01)
    if (!isValidOrgId(selectedOrgId)) {
      setError('Invalid organization ID in URL. Please select a valid organization.');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getBoardStory(selectedOrgId);
      setStory(data);
      if (data.sections && data.sections.length > 0) {
        setActiveSection(data.sections[0].section_id);
      } else {
        setActiveSection(standardSections[0].id);
      }
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.toDisplayMessage()
          : 'Failed to synthesize board story narrative.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStory();
  }, [selectedOrgId]);

  const scrollToSection = (sectionId: string) => {
    setActiveSection(sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  /**
   * S1.8-AUDIT-FIX-A01: PDF download is now server-side.
   * The backend endpoint sources all numbers from the scoring snapshot via reportlab.
   * No PDF bytes are ever constructed in the browser.
   */
  const pdfDownloadUrl = selectedOrgId && isValidOrgId(selectedOrgId)
    ? getBoardStoryPdfUrl(selectedOrgId)
    : null;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-3">
        <svg className="animate-spin h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-semibold animate-pulse">Generating Board Story Briefing...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center px-4 space-y-4">
        <div className="p-3 bg-danger-500/10 rounded-full">
          <AlertTriangle className="h-8 w-8 text-danger-500" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Failed to load Board Story</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{error}</p>
        </div>
        <button onClick={loadStory} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-bold rounded-lg transition-colors">
          Retry Generation
        </button>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="max-w-7xl mx-auto space-y-6 text-left pb-12"
    >
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-50/15 dark:bg-indigo-950/20 border border-indigo-200 dark:border-indigo-800/40 rounded-2xl flex items-center justify-center">
            <Brain className="w-5 h-5 text-indigo-650 dark:text-indigo-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Boardroom Briefing Interpreter
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-semibold">
              What is our security posture story for the board?
            </p>
          </div>
        </div>
        <div className="flex gap-3 items-center">
          <select
            aria-label="Select Organization"
            className="rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 min-w-[220px] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-bold"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>{org.name}</option>
            ))}
          </select>
          {pdfDownloadUrl ? (
            <a
              href={pdfDownloadUrl}
              download
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl font-bold text-sm bg-[#00C853] hover:bg-[#00C853]/90 text-white transition-colors"
            >
              <Download className="w-4 h-4" /> Download PDF Story
            </a>
          ) : (
            <button
              disabled
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl font-bold text-sm bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
            >
              <Download className="w-4 h-4" /> Download PDF Story
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Navigation Sidebar */}
        <div className="lg:col-span-1 space-y-2">
          <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest pl-3 mb-3">Briefing Sections</h3>
          <div className="space-y-1">
            {standardSections.map((sec) => {
              const matched = story?.sections.find(s => s.section_id === sec.id);
              const isActive = activeSection === sec.id;
              
              return (
                <button
                  key={sec.id}
                  onClick={() => scrollToSection(sec.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold text-left transition-all ${
                    isActive
                      ? 'bg-indigo-50/80 dark:bg-indigo-950/20 text-indigo-650 dark:text-indigo-400 shadow-sm border border-indigo-100 dark:border-indigo-900/50'
                      : 'hover:bg-slate-50 dark:hover:bg-slate-900/40 text-slate-600 dark:text-slate-400 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className={`w-5 h-5 flex items-center justify-center rounded-lg text-[10px] font-bold border ${
                      isActive 
                        ? 'bg-indigo-600 text-white border-indigo-600' 
                        : 'bg-slate-100 dark:bg-slate-900 border-slate-205 dark:border-slate-800'
                    }`}>
                      {sec.icon}
                    </span>
                    <span className="truncate max-w-[130px]">{matched ? matched.title : sec.defaultTitle}</span>
                  </div>
                  {matched && <CheckCircle2 className="w-3.5 h-3.5 text-[#00C853] shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Story Content View */}
        <div className="lg:col-span-3 space-y-6 h-[calc(100vh-230px)] overflow-y-auto pr-2 scrollbar-thin">
          {standardSections.map((sec) => {
            const matchedSection = story?.sections.find((s) => s.section_id === sec.id);
            const isMissing = !matchedSection;

            return (
              <Card 
                key={sec.id} 
                id={sec.id} 
                className={`rounded-3xl border transition-all duration-300 ${
                  activeSection === sec.id 
                    ? 'border-indigo-400 dark:border-indigo-850 shadow-md ring-1 ring-indigo-500/20' 
                    : 'border-slate-205 dark:border-slate-800 bg-white/60 dark:bg-slate-950/20'
                }`}
              >
                <CardHeader className="pb-3 flex flex-row items-center justify-between border-b border-slate-100 dark:border-slate-900">
                  <CardTitle className="text-sm font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                    <span className="w-6 h-6 flex items-center justify-center rounded-lg text-xs font-bold bg-indigo-500/10 text-indigo-500">
                      {sec.icon}
                    </span>
                    {matchedSection ? matchedSection.title : sec.defaultTitle}
                  </CardTitle>
                  {isMissing ? (
                    <Badge variant="warning" className="text-[9px] font-bold uppercase">Fallback Mode</Badge>
                  ) : (
                    <Badge variant="success" className="text-[9px] font-bold uppercase">Verified Narrative</Badge>
                  )}
                </CardHeader>
                <CardContent className="pt-4">
                  {isMissing ? (
                    <div className="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-800 dark:text-amber-400 leading-relaxed font-semibold">
                      <p className="font-extrabold flex items-center gap-1.5 uppercase tracking-wide">
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                        Section Incomplete
                      </p>
                      <p className="mt-1.5">
                        This section requires additional telemetry integrations (Splunk/Wazuh) to synthesize custom posture details. Connecting more data sources will replace this placeholder with mathematical evidence narratives.
                      </p>
                    </div>
                  ) : (
                    <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap font-sans font-semibold">
                      {matchedSection.content}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}

export default BoardStory;
