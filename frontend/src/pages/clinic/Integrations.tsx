import React from 'react';

export default function Integrations() {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Connected Systems</h1>
      <p className="text-gray-500 mb-8">The systems ResilAI checks every morning.</p>

      <div className="space-y-4">
        <div className="bg-white border border-gray-200 rounded-lg p-6 flex justify-between items-center">
          <div>
            <h3 className="font-bold text-gray-900">Microsoft 365 / Google Workspace</h3>
            <p className="text-sm text-gray-500">Connected</p>
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6 flex justify-between items-center">
          <div>
            <h3 className="font-bold text-gray-900">Clinic PCs (Wazuh)</h3>
            <p className="text-sm text-gray-500">Connected (5 devices)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
