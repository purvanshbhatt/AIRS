import React from 'react';
import { Menu, Search, Bell } from 'lucide-react';

interface ReadinessHeaderProps {
  onMenuClick: () => void;
  orgName: string;
}

export function ReadinessHeader({ onMenuClick, orgName }: ReadinessHeaderProps) {
  return (
    <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-4 lg:px-8 z-30 sticky top-0">
      <div className="flex items-center gap-4">
        <button 
          onClick={onMenuClick}
          className="md:hidden p-2 -ml-2 rounded-lg hover:bg-slate-100 text-slate-600"
        >
          <Menu className="w-5 h-5" />
        </button>
        
        <div className="flex items-center gap-2">
          <div className="h-6 w-px bg-slate-200 hidden md:block" />
          <span className="font-medium text-slate-700 hidden md:block">{orgName}</span>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-500 uppercase tracking-wider hidden md:block">
            Production
          </span>
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        <button className="p-2 rounded-full hover:bg-slate-100 text-slate-500 transition-colors">
          <Search className="w-5 h-5" />
        </button>
        <button className="p-2 rounded-full hover:bg-slate-100 text-slate-500 transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2.5 w-2 h-2 rounded-full bg-amber-500 border-2 border-white" />
        </button>
        <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center text-sm font-medium ml-2">
          JD
        </div>
      </div>
    </header>
  );
}
