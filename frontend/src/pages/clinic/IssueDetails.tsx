import React, { useState } from 'react';
import { useLocation, useNavigate, useParams, Link } from 'react-router-dom';

export default function IssueDetails() {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams();
  const check = location.state?.check;
  const [fixing, setFixing] = useState(false);
  const [fixResult, setFixResult] = useState<string | null>(null);

  if (!check || !check.action) {
    return <div className="p-10 text-center">Issue details not found. <Link to="/clinic" className="text-blue-600 underline">Go back</Link></div>;
  }

  const handleFix = async () => {
    setFixing(true);
    try {
      const res = await fetch(`/api/clinic/problems/${check.action.action_id}/fix`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
         setFixResult('success');
         setTimeout(() => navigate('/clinic'), 2000);
      } else {
         setFixResult(data.message || 'Failed to fix.');
      }
    } catch (err) {
      setFixResult('An error occurred while communicating with the server.');
    } finally {
      setFixing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-10 font-sans">
      <Link to="/clinic" className="text-blue-600 hover:underline mb-6 inline-flex items-center text-sm font-medium">
        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
        Back to Morning Check
      </Link>
      
      <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm mb-8">
        <div className="flex items-start mb-8 border-b border-gray-100 pb-8">
           <div className="w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center mr-6 shrink-0 mt-1">
             <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
           </div>
           <div>
             <h1 className="text-3xl font-bold text-gray-900 mb-2">{check.label}</h1>
             <p className="text-gray-600 text-lg leading-relaxed">{check.action.description}</p>
           </div>
        </div>

        <div className="grid grid-cols-2 gap-12 mb-8">
          <div>
            <h2 className="text-xs uppercase tracking-wider text-gray-400 font-bold mb-3">Expected Result</h2>
            <p className="text-gray-800 text-md leading-relaxed">{check.action.expected_result}</p>
          </div>

          <div>
            <h2 className="text-xs uppercase tracking-wider text-gray-400 font-bold mb-3">Rollback</h2>
            <p className="text-gray-800 text-md leading-relaxed bg-gray-50 p-4 rounded-lg border border-gray-100">{check.action.rollback_description}</p>
          </div>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 flex items-center justify-between">
          <div>
            <p className="text-gray-900 font-semibold mb-1">Estimated Fix Time: {check.action.estimated_minutes} minutes</p>
            <p className="text-sm text-gray-500">
               {check.action.can_automate ? "ResilAI can automatically fix this issue for you." : `Requires ${check.action.required_permissions.join(', ')} privileges.`}
            </p>
          </div>
          
          {check.action.can_automate && (
            <button
              onClick={handleFix}
              disabled={fixing || fixResult === 'success'}
              className="bg-blue-600 text-white px-8 py-3 rounded-xl hover:bg-blue-700 text-md font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            >
              {fixing ? "Applying Fix..." : fixResult === 'success' ? "Fix Applied ✓" : check.action.title || "Fix Now"}
            </button>
          )}
        </div>
        
        {fixResult && fixResult !== 'success' && (
           <div className="mt-4 text-red-600 font-medium text-center">{fixResult}</div>
        )}
      </div>

      {/* Evidence Explorer */}
      {check.trust && (
        <div>
           <h3 className="text-lg font-bold text-gray-900 mb-4">Evidence Explorer</h3>
           <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
              <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                 <div>
                    <span className="text-xs uppercase tracking-wider text-gray-500 font-bold block mb-1">Source</span>
                    <span className="text-gray-900 font-medium">{check.trust.provider_name} ({check.trust.evidence_source})</span>
                 </div>
                 <div className="text-right">
                    <span className="text-xs uppercase tracking-wider text-gray-500 font-bold block mb-1">Verified</span>
                    <span className="text-gray-900 font-medium">{check.trust.evidence_age_mins} minutes ago</span>
                 </div>
                 <div className="text-right">
                    <span className="text-xs uppercase tracking-wider text-gray-500 font-bold block mb-1">Confidence</span>
                    <span className="text-emerald-600 font-bold">{check.trust.confidence_pct}%</span>
                 </div>
              </div>
              <div className="p-6">
                 <h4 className="text-sm font-semibold text-gray-900 mb-3">Verification Details</h4>
                 <ul className="space-y-2">
                    {check.trust.reasons.map((reason, idx) => (
                       <li key={idx} className="flex items-start text-sm text-gray-700">
                          <span className="text-emerald-500 mr-2 mt-0.5">✓</span>
                          {reason}
                       </li>
                    ))}
                 </ul>
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
