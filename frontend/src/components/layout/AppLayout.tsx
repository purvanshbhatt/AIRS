import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { AppSidebar } from './AppSidebar';
import { ReadinessHeader } from '../readiness/ReadinessHeader';
import { useDemoMode } from '../../contexts/DemoModeContext';
import { useToast } from '../ui';
import { Sparkles, ArrowUp, Calendar, AlertTriangle, RotateCcw, Layers } from 'lucide-react';

export default function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const { isMspTenant } = useDemoMode();
  const { addToast } = useToast();

  const handleSearchSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) return;
    
    addToast({ title: 'Search Query Logged', message: 'Telemetry query recorded in audit history.', type: "info" });
    setSearchQuery('');
  };

  return (
    <div className="min-h-screen bg-background text-on-background antialiased flex font-sans selection:bg-ready-emerald/30 selection:text-ready-emerald">
      {/* Fixed Sidebar for Desktop */}
      <AppSidebar />

      {/* Main Content Area */}
      <div className="flex-1 md:ml-64 min-h-screen pb-24 md:pb-8 flex flex-col relative w-full overflow-x-hidden">
        <ReadinessHeader 
          isMspTenant={isMspTenant}
          onMenuClick={() => setMobileMenuOpen(true)} 
        />
        
        <main className="flex-1 w-full max-w-[1200px] mx-auto px-4 md:px-8 pt-4 pb-12">
          <Outlet />
        </main>

        {/* Persistent Ask ResilAI Bar */}
        <div className="fixed bottom-16 md:bottom-4 left-0 right-0 md:left-64 p-3 md:px-8 z-30 pointer-events-none">
          <div className="max-w-3xl mx-auto pointer-events-auto">
            <form onSubmit={handleSearchSubmit} className="relative flex items-center bg-surface-container-high/95 backdrop-blur-lg rounded-full p-1.5 border border-outline-variant/50 shadow-2xl shadow-black/50">
              <Sparkles className="w-4 h-4 text-ready-emerald ml-3 shrink-0" />
              <input 
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Ask ResilAI to analyze drift, generate reports, or query telemetry..."
                aria-label="Ask ResilAI to analyze drift, generate reports, or query telemetry"
                className="w-full bg-transparent border-none text-sm text-on-surface focus:outline-none focus:ring-0 placeholder-on-surface-variant/60 ml-2.5"
              />
              <button 
                type="submit"
                className="bg-ready-emerald text-on-primary-container w-8 h-8 rounded-full flex items-center justify-center hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald focus-visible:ring-offset-2 focus-visible:ring-offset-background transition-all shrink-0 cursor-pointer"
                title="Send query"
                aria-label="Send query"
              >
                <ArrowUp className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 z-50 flex md:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Navigation Menu"
        >
          <div 
            className="fixed inset-0 bg-background/80 backdrop-blur-sm transition-opacity" 
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true" 
          />
          <div className="relative w-4/5 max-w-xs bg-surface-container-low h-full flex flex-col z-50 shadow-2xl overflow-hidden border-r border-outline-variant">
            <AppSidebar mobile onClose={() => setMobileMenuOpen(false)} />
          </div>
        </div>
      )}

      {/* Mobile Bottom Navigation Bar */}
      <nav 
        className="md:hidden fixed bottom-0 left-0 right-0 bg-surface-container-low border-t border-outline-variant/40 z-50"
        aria-label="Mobile Bottom Navigation"
      >
        <ul className="flex justify-around items-center h-16 px-2">
          <li>
            <NavLink 
              to="/morning-brief" 
              className={({ isActive }) => 
                `flex flex-col items-center justify-center w-16 h-full text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald rounded-lg ${isActive ? 'text-ready-emerald font-semibold' : 'text-on-surface-variant'}`
              }
              aria-label="Today - Morning Brief"
            >
              <Calendar className="w-5 h-5 mb-1 shrink-0" />
              <span>Today</span>
            </NavLink>
          </li>
          <li>
            <NavLink 
              to="/needs-attention" 
              className={({ isActive }) => 
                `flex flex-col items-center justify-center w-16 h-full text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald rounded-lg ${isActive ? 'text-ready-emerald font-semibold' : 'text-on-surface-variant'}`
              }
              aria-label="Needs Attention - Triage"
            >
              <AlertTriangle className="w-5 h-5 mb-1 shrink-0" />
              <span>Triage</span>
            </NavLink>
          </li>
          <li>
            <NavLink 
              to="/recovery" 
              className={({ isActive }) => 
                `flex flex-col items-center justify-center w-16 h-full text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald rounded-lg ${isActive ? 'text-ready-emerald font-semibold' : 'text-on-surface-variant'}`
              }
              aria-label="Recovery Readiness"
            >
              <RotateCcw className="w-5 h-5 mb-1 shrink-0" />
              <span>Recovery</span>
            </NavLink>
          </li>
          <li>
            <NavLink 
              to="/operations" 
              className={({ isActive }) => 
                `flex flex-col items-center justify-center w-16 h-full text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald rounded-lg ${isActive ? 'text-ready-emerald font-semibold' : 'text-on-surface-variant'}`
              }
              aria-label="Operations Center"
            >
              <Layers className="w-5 h-5 mb-1 shrink-0" />
              <span>Ops</span>
            </NavLink>
          </li>
        </ul>
      </nav>
    </div>
  );
}
