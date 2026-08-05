import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { AppSidebar } from './AppSidebar';
import { ReadinessHeader } from '../../components/readiness/ReadinessHeader';

export default function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen bg-slate-50 font-sans overflow-hidden">
      {/* Sidebar (desktop) */}
      <AppSidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <ReadinessHeader 
          orgName="Acme Healthcare" 
          onMenuClick={() => setMobileMenuOpen(true)} 
        />
        
        <main className="flex-1 overflow-y-auto p-4 md:p-8 lg:p-12 relative">
          <div className="max-w-6xl mx-auto pb-24">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)} />
          <div className="relative w-4/5 max-w-sm bg-white h-full flex flex-col">
            <AppSidebar />
          </div>
        </div>
      )}
    </div>
  );
}
