import React, { useState } from 'react';
import { Terminal } from 'lucide-react';

export function DiagnosticsFooter() {
  const [isOpen, setIsOpen] = useState(false);
  const buildInfo = (window as any).__RESILAI_BUILD__ || {};

  if (Object.keys(buildInfo).length === 0) return null;

  return (
    <div className="fixed bottom-0 right-0 z-50 p-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-gray-800 text-gray-400 hover:text-white rounded px-2 py-1 text-xs flex items-center gap-2 opacity-50 hover:opacity-100 transition-opacity"
        title="Build Diagnostics"
      >
        <Terminal size={12} />
        {buildInfo.commit || 'unknown'}
      </button>

      {isOpen && (
        <div className="absolute bottom-10 right-2 w-64 bg-gray-900 text-green-400 text-xs p-4 rounded shadow-lg border border-gray-700 font-mono">
          <div className="flex justify-between items-center mb-2 pb-2 border-b border-gray-700">
            <span className="font-bold text-white">System Diagnostics</span>
            <button onClick={() => setIsOpen(false)} className="text-gray-500 hover:text-white">&times;</button>
          </div>
          <div className="space-y-1 overflow-hidden">
            <p className="truncate" title={buildInfo.commit}><span className="text-gray-500">Commit:</span> {buildInfo.commit}</p>
            <p className="truncate" title={buildInfo.environment}><span className="text-gray-500">Env:</span> {buildInfo.environment}</p>
            <p className="truncate" title={buildInfo.buildTime}><span className="text-gray-500">Built:</span> {buildInfo.buildTime ? new Date(buildInfo.buildTime).toLocaleString() : 'unknown'}</p>
            <p className="truncate" title={buildInfo.api}><span className="text-gray-500">API:</span> {buildInfo.api}</p>
            <p className="truncate" title={buildInfo.version}><span className="text-gray-500">Ver:</span> {buildInfo.version}</p>
          </div>
        </div>
      )}
    </div>
  );
}
