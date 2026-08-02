import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

interface ActionCard {
  action_id: string;
  title: string;
  description: string;
  expected_result: string;
  rollback_description: string;
  estimated_minutes: number;
  approval_needed: boolean;
  required_permissions: string[];
  success_message: string;
  reversible: boolean;
  can_automate: boolean;
  category: string;
}

interface TrustContext {
  confidence_pct: number;
  evidence_source: string;
  evidence_age_mins: number;
  provider_name: string;
  reasons: string[];
}

interface ReadinessCheck {
  status: string;
  label: string;
  detail?: string;
  trust?: TrustContext;
  action?: ActionCard;
}

interface UnknownItem {
  label: string;
  impact: string;
  source: string;
}

interface ConnectorReadiness {
  connector_type: string;
  display_name: string;
  status: string;
  last_sync_age_mins: number;
  verifies: string[];
}

interface CoverageSummary {
  coverage_pct: number;
  covered_systems: string[];
  uncovered_systems: string[];
}

interface DailyReadinessReport {
  report_id: string;
  report_date: string;
  generated_at: string;
  status: string;
  clinic_health_pct: number;
  connector_health_pct: number;
  greeting: string;
  summary: string;
  passed_checks: ReadinessCheck[];
  failed_checks: ReadinessCheck[];
  warnings: ReadinessCheck[];
  unknowns: UnknownItem[];
  immediate_actions: ActionCard[];
  coverage: CoverageSummary;
  connectors: ConnectorReadiness[];
  trust: TrustContext;
  checks_performed: number;
  devices_checked: number;
  accounts_checked: number;
  backups_verified: number;
}

export default function Home() {
  const [report, setReport] = useState<DailyReadinessReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // using "default-org" for demo
    fetch('/api/clinic/readiness/default-org')
      .then(res => res.json())
      .then(d => {
        setReport(d);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return (
    <div className="flex h-screen items-center justify-center">
      <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
    </div>
  );
  if (!report) return <div className="text-center mt-10">Failed to load readiness report.</div>;

  const isSafe = report.status === 'safe_to_open';
  const isWarning = report.status === 'action_needed';
  const isUnknown = report.status === 'unknown';

  return (
    <div className="max-w-4xl mx-auto py-10 font-sans">
      <h1 className="text-4xl font-semibold text-gray-900 tracking-tight mb-2">{report.greeting}</h1>
      
      {isSafe && (
        <div className="bg-emerald-50 rounded-2xl p-8 mb-8 border border-emerald-100 mt-6 shadow-sm">
          <div className="flex items-start">
             <div className="w-12 h-12 bg-emerald-500 text-white rounded-full flex items-center justify-center mr-6 shrink-0 shadow-sm">
               <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
             </div>
             <div>
                <h2 className="text-2xl font-semibold text-emerald-950 mb-2">Your clinic is safe to open today.</h2>
                <p className="text-emerald-800 text-lg leading-relaxed">{report.summary}</p>
             </div>
          </div>
        </div>
      )}

      {isWarning && (
        <div className="bg-amber-50 rounded-2xl p-8 mb-8 border border-amber-100 mt-6 shadow-sm">
          <div className="flex items-start">
             <div className="w-12 h-12 bg-amber-500 text-white rounded-full flex items-center justify-center mr-6 shrink-0 shadow-sm">
               <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
             </div>
             <div>
                <h2 className="text-2xl font-semibold text-amber-950 mb-2">Your clinic needs attention.</h2>
                <p className="text-amber-800 text-lg leading-relaxed">{report.summary}</p>
             </div>
          </div>
        </div>
      )}

      {!isSafe && !isWarning && !isUnknown && (
        <div className="bg-red-50 rounded-2xl p-8 mb-8 border border-red-100 mt-6 shadow-sm">
          <div className="flex items-start">
             <div className="w-12 h-12 bg-red-600 text-white rounded-full flex items-center justify-center mr-6 shrink-0 shadow-sm">
               <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
             </div>
             <div>
                <h2 className="text-2xl font-semibold text-red-950 mb-2">Critical Risk Detected.</h2>
                <p className="text-red-800 text-lg leading-relaxed">{report.summary}</p>
             </div>
          </div>
        </div>
      )}

      {isUnknown && (
        <div className="bg-slate-50 rounded-2xl p-8 mb-8 border border-slate-200 mt-6 shadow-sm">
          <div className="flex items-start">
             <div className="w-12 h-12 bg-slate-500 text-white rounded-full flex items-center justify-center mr-6 shrink-0 shadow-sm">
               <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
             </div>
             <div>
                <h2 className="text-2xl font-semibold text-slate-900 mb-2">We cannot determine readiness.</h2>
                <p className="text-slate-700 text-lg leading-relaxed">{report.summary}</p>
             </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-8 mb-12">
        <div>
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">We Checked</h3>
          <ul className="space-y-3">
            {report.accounts_checked > 0 && (
              <li className="flex items-center text-gray-700">
                <span className="text-emerald-500 mr-3">✓</span>
                {report.accounts_checked} employee accounts
              </li>
            )}
            {report.devices_checked > 0 && (
              <li className="flex items-center text-gray-700">
                <span className="text-emerald-500 mr-3">✓</span>
                {report.devices_checked} computers
              </li>
            )}
            {report.backups_verified > 0 && (
              <li className="flex items-center text-gray-700">
                <span className="text-emerald-500 mr-3">✓</span>
                {report.backups_verified} backups verified
              </li>
            )}
            <li className="flex items-center text-gray-700">
              <span className="text-emerald-500 mr-3">✓</span>
              Email security
            </li>
            <li className="flex items-center text-gray-700">
              <span className="text-emerald-500 mr-3">✓</span>
              Microsoft 365
            </li>
          </ul>
        </div>
        
        <div>
          <div className="bg-gray-50 rounded-xl p-6 border border-gray-100 h-full flex flex-col justify-center space-y-4">
             <div className="flex justify-between items-center">
               <span className="text-gray-500 text-sm">Confidence</span>
               <span className="text-2xl font-semibold text-gray-900">{report.trust?.confidence_pct || 0}%</span>
             </div>
             <div className="flex justify-between items-center">
               <span className="text-gray-500 text-sm">Last verified</span>
               <span className="text-sm font-medium text-gray-900">
                  {report.generated_at ? Math.floor((new Date().getTime() - new Date(report.generated_at).getTime()) / 60000) : 0} minutes ago
               </span>
             </div>
             <div className="flex justify-between items-center">
               <span className="text-gray-500 text-sm">Coverage</span>
               <span className="text-sm font-medium text-gray-900">{report.coverage?.coverage_pct || 0}%</span>
             </div>
          </div>
        </div>
      </div>

      {report.failed_checks.length > 0 && (
        <div className="mb-12">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">Critical Actions Needed</h3>
          <div className="space-y-6">
            {report.failed_checks.map((check, idx) => (
              <div key={idx} className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow">
                 <div className="flex justify-between items-start">
                    <div className="max-w-xl">
                      <h4 className="text-lg font-bold text-gray-900 mb-2">{check.label}</h4>
                      {check.action && (
                        <>
                          <p className="text-gray-600 mb-4">{check.action.description}</p>
                          <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                             <div>
                               <span className="block text-gray-400 font-semibold uppercase tracking-wider text-xs mb-1">Expected Result</span>
                               <span className="text-gray-800">{check.action.expected_result}</span>
                             </div>
                             <div>
                               <span className="block text-gray-400 font-semibold uppercase tracking-wider text-xs mb-1">Estimated Fix</span>
                               <span className="text-gray-800">{check.action.estimated_minutes} minutes</span>
                             </div>
                          </div>
                        </>
                      )}
                    </div>
                    {check.action?.can_automate && (
                       <Link to={`/clinic/issue/${check.action.action_id}`} state={{ check }} className="bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700 font-medium text-sm transition-colors text-center">
                         Review & Fix
                       </Link>
                    )}
                 </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {report.warnings.length > 0 && (
        <div className="mb-12">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">Warnings</h3>
          <div className="space-y-6">
            {report.warnings.map((check, idx) => (
              <div key={idx} className="bg-white border border-yellow-200 rounded-xl p-6 shadow-sm">
                 <h4 className="text-lg font-bold text-gray-900">{check.label}</h4>
                 <p className="text-gray-600 mt-2">{check.detail}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {report.coverage?.uncovered_systems?.length > 0 && (
        <div className="mt-12 border-t border-gray-200 pt-8">
           <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">We cannot currently verify</h3>
           <ul className="space-y-3">
             {report.coverage.uncovered_systems.map((sys, idx) => (
               <li key={idx} className="flex items-center text-gray-500">
                 <span className="text-gray-400 mr-3">✗</span>
                 {sys}
               </li>
             ))}
           </ul>
        </div>
      )}
    </div>
  );
}
