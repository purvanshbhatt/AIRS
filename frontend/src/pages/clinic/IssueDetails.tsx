import React, { useState } from 'react';
import { useLocation, useNavigate, useParams, Link } from 'react-router-dom';

export default function IssueDetails() {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams();
  const moment = location.state?.moment;
  const [fixing, setFixing] = useState(false);

  if (!moment) {
    return <div>Issue not found. <Link to="/clinic">Go back</Link></div>;
  }

  const handleFix = async () => {
    setFixing(true);
    try {
      await fetch(`/api/clinic/problems/${moment.id}/fix`, { method: 'POST' });
      alert("Fix triggered successfully.");
      navigate('/clinic');
    } catch (err) {
      alert("Failed to fix.");
    } finally {
      setFixing(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <Link to="/clinic" className="text-blue-600 hover:underline mb-6 inline-block">← Back to Morning Check</Link>
      
      <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-900 mb-8">{moment.what_happened}</h1>

        <div className="space-y-8">
          <div>
            <h2 className="text-sm uppercase tracking-wider text-gray-500 font-semibold mb-2">Why should I care?</h2>
            <p className="text-gray-900 text-lg">{moment.why_care}</p>
          </div>

          <div>
            <h2 className="text-sm uppercase tracking-wider text-gray-500 font-semibold mb-2">What happens if I ignore it?</h2>
            <p className="text-gray-900 text-lg">{moment.ignore_impact}</p>
          </div>

          <div className="pt-6 border-t border-gray-200 flex items-center justify-between">
            <div>
              <p className="text-gray-600">Estimated time: <strong>{moment.estimated_fix_time_mins} minutes</strong></p>
              {!moment.can_autofix && <p className="text-sm text-gray-500 mt-1">Requires MSP assistance.</p>}
            </div>
            
            <button
              onClick={handleFix}
              disabled={fixing}
              className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 text-lg font-medium disabled:opacity-50"
            >
              {fixing ? "Working..." : moment.fix_action_text}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
