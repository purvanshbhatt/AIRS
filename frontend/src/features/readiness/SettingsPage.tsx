import React from 'react';
import { Settings, Plug, Users, Bell } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      <div className="flex items-center gap-4 border-b border-slate-200 pb-6">
        <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-600 flex items-center justify-center">
          <Settings className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
          <p className="text-slate-500 mt-1">
            Manage your organization, integrations, and preferences.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Integrations */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
          <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center mb-4">
            <Plug className="w-5 h-5 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Data Connectors</h3>
          <p className="text-slate-600 text-sm mb-4">
            Connect Microsoft 365, Google Workspace, and Backup providers to enable continuous verification.
          </p>
          <div className="flex items-center gap-2 text-sm font-medium text-blue-600">
            3 Active Connectors
          </div>
        </div>

        {/* Team Members */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
          <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center mb-4">
            <Users className="w-5 h-5 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Team & Access</h3>
          <p className="text-slate-600 text-sm mb-4">
            Manage who has access to the readiness dashboard and assign roles.
          </p>
          <div className="flex items-center gap-2 text-sm font-medium text-blue-600">
            4 Members
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
          <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center mb-4">
            <Bell className="w-5 h-5 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Notifications</h3>
          <p className="text-slate-600 text-sm mb-4">
            Configure morning briefs, critical alerts, and weekly summary emails.
          </p>
          <div className="flex items-center gap-2 text-sm font-medium text-blue-600">
            Morning Brief enabled
          </div>
        </div>

      </div>

    </div>
  );
}
