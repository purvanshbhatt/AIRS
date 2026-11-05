import React from 'react';
import { Shield, Activity, Search, AlertCircle } from 'lucide-react';

interface ExecutiveQuestionsGridProps {
  canOperate: boolean;
  canRecover: boolean;
  itemsNeedingAttention: number;
  confidencePct: number;
}

export function ExecutiveQuestionsGrid({
  canOperate,
  canRecover,
  itemsNeedingAttention,
  confidencePct
}: ExecutiveQuestionsGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Question 1 */}
      <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
        <div className="flex items-center gap-3 mb-4 text-slate-500">
          <Activity className="w-5 h-5" />
          <h3 className="font-medium text-sm">Can we operate today?</h3>
        </div>
        <div>
          <span className={`text-2xl font-bold ${canOperate ? 'text-emerald-600' : 'text-red-600'}`}>
            {canOperate ? 'YES' : 'NO'}
          </span>
        </div>
      </div>

      {/* Question 2 */}
      <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
        <div className="flex items-center gap-3 mb-4 text-slate-500">
          <Shield className="w-5 h-5" />
          <h3 className="font-medium text-sm">Can we recover today?</h3>
        </div>
        <div>
          <span className={`text-2xl font-bold ${canRecover ? 'text-emerald-600' : 'text-red-600'}`}>
            {canRecover ? 'YES' : 'NO'}
          </span>
        </div>
      </div>

      {/* Question 3 */}
      <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
        <div className="flex items-center gap-3 mb-4 text-slate-500">
          <AlertCircle className="w-5 h-5" />
          <h3 className="font-medium text-sm">Anything needs attention?</h3>
        </div>
        <div>
          <span className={`text-2xl font-bold ${itemsNeedingAttention === 0 ? 'text-emerald-600' : 'text-amber-600'}`}>
            {itemsNeedingAttention} items
          </span>
        </div>
      </div>

      {/* Question 4 */}
      <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
        <div className="flex items-center gap-3 mb-4 text-slate-500">
          <Search className="w-5 h-5" />
          <h3 className="font-medium text-sm">How confident are we?</h3>
        </div>
        <div>
          <span className="text-2xl font-bold text-slate-700">
            {confidencePct}%
          </span>
        </div>
      </div>
    </div>
  );
}
