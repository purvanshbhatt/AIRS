import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

interface ClinicMoment {
  id: string;
  type_id: string;
  what_happened: string;
  why_care: string;
  fix_action_text: string;
  ignore_impact: string;
  can_autofix: boolean;
  estimated_fix_time_mins: number;
  severity: string;
}

interface MorningCheck {
  id: string;
  date: string;
  status: string;
  moments: ClinicMoment[];
  generated_at: string;
}

export default function Home() {
  const [data, setData] = useState<MorningCheck | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/clinic/morning-summary')
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!data) return <div>Failed to load Morning Check.</div>;

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Morning Check</h1>
      <p className="text-gray-500 mb-8">{new Date(data.date).toLocaleDateString()}</p>

      {data.status === 'SAFE' ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 flex items-center">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mr-4">
            <span className="text-green-600 text-2xl">✓</span>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-green-900">Your clinic is safe.</h2>
            <p className="text-green-700">Have a great day seeing patients.</p>
          </div>
        </div>
      ) : (
        <div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 flex items-center mb-6">
            <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mr-4">
              <span className="text-yellow-600 text-2xl">⚠</span>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-yellow-900">{data.moments.length} Issues Need Attention</h2>
              <p className="text-yellow-700">Please review before seeing patients today.</p>
            </div>
          </div>
          <div className="space-y-4">
            {data.moments.map(moment => (
              <div key={moment.id} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm flex justify-between items-center">
                <div>
                  <h3 className="text-md font-bold text-gray-900">{moment.what_happened}</h3>
                  <p className="text-sm text-gray-500 mt-1">{moment.estimated_fix_time_mins} minute fix</p>
                </div>
                <Link to={`/clinic/issue/${moment.id}`} state={{ moment }} className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm font-medium">
                  Fix It
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
