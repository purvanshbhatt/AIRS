import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { AppSidebar } from './AppSidebar';
import { ReadinessHeader } from '../readiness/ReadinessHeader';
import { useDemoMode } from '../../contexts/DemoModeContext';
import { useToast } from '../ui';
import { Sparkles, ArrowUp, Calendar, AlertTriangle, RotateCcw, Layers, X } from 'lucide-react';

export default function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
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
      {/* Fixed Sidebar for Desktop & Tablets */}
      <AppSidebar />

      {/* Main Content Area */}
      <div className="flex-1 md:ml-20 lg:ml-64 min-h-screen pb-24 sm:pb-28 md:pb-8 flex flex-col relative w-full overflow-x-hidden">
        <ReadinessHeader 
          isMspTenant={isMspTenant}
          onMenuClick={() => setMobileMenuOpen(true)} 
        />
        
        <main className="flex-1 w-full max-w-[1200px] mx-auto px-4 sm:px-6 md:px-8 pt-4 pb-16 md:pb-12">
          <Outlet />
        </main>

        {/* Desktop / Tablet Persistent Ask ResilAI Bar */}
        <div className="hidden md:block fixed bottom-4 left-20 lg:left-64 right-0 p-3 md:px-8 z-30 pointer-events-none">
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
                className="bg-ready-emerald text-on-primary-container w-8 h-8 rounded-full flex items-center justify-center hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald focus-visible:ring-offset-2 focus-visible:ring-offset-background transition-all shrink-0 cursor-pointer min-touch-target"
                title="Send query"
                aria-label="Send query"
              >
                <ArrowUp className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>

        {/* Mobile Floating Action Button (M3 Extended FAB) */}
        {!mobileSearchOpen && (
          <button
            onClick={() => setMobileSearchOpen(true)}
            className="md:hidden fixed bottom-20 right-4 z-40 flex items-center gap-2 h-12 px-4 rounded-full bg-ready-emerald text-slate-950 font-bold shadow-lg shadow-ready-emerald/25 hover:shadow-ready-emerald/40 active:scale-95 transition-all min-touch-target cursor-pointer m3-state-layer m3-elevation-3"
            aria-label="Ask ResilAI"
            title="Ask ResilAI"
          >
            <Sparkles className="w-4 h-4 text-slate-950 shrink-0" />
            <span className="text-xs font-bold text-slate-950">Ask ResilAI</span>
          </button>
        )}

        {/* Mobile Ask ResilAI Bottom Sheet Modal */}
        {mobileSearchOpen && (
          <div 
            className="md:hidden fixed inset-0 z-50 flex flex-col justify-end bg-background/80 backdrop-blur-sm animate-fade-in"
            role="dialog"
            aria-modal="true"
            aria-label="Ask ResilAI Search"
          >
            <div 
              className="fixed inset-0"
              onClick={() => setMobileSearchOpen(false)}
              aria-hidden="true"
            />
            <div className="relative bg-surface-container-low border-t border-outline-variant rounded-t-3xl p-4 pb-safe shadow-2xl z-10 space-y-3">
              <div className="flex items-center justify-between pb-1 border-b border-outline-variant/30">
                <div className="flex items-center gap-2 text-ready-emerald font-bold text-sm">
                  <Sparkles className="w-4 h-4" />
                  <span>Ask ResilAI</span>
                </div>
                <button
                  onClick={() => setMobileSearchOpen(false)}
                  className="p-1 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors"
                  aria-label="Close search"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form 
                onSubmit={(e) => { 
                  handleSearchSubmit(e); 
                  setMobileSearchOpen(false); 
                }} 
                className="relative flex items-center bg-surface-container-high rounded-full p-1.5 border border-outline-variant/60 shadow-inner"
              >
                <input 
                  type="text"
                  value={searchQuery}
                  autoFocus
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Ask for a situation report, drift, or metrics..."
                  aria-label="Ask ResilAI query"
                  className="w-full bg-transparent border-none text-sm text-on-surface focus:outline-none focus:ring-0 placeholder-on-surface-variant/60 ml-3"
                />
                <button 
                  type="submit"
                  className="bg-ready-emerald text-slate-950 w-9 h-9 rounded-full flex items-center justify-center hover:brightness-110 active:scale-95 transition-all shrink-0 cursor-pointer min-touch-target"
                  title="Send query"
                  aria-label="Send query"
                >
                  <ArrowUp className="w-4 h-4" />
                </button>
              </form>

              <div className="flex flex-wrap gap-1.5 pt-1">
                {['Situation Report', 'Backup Verification', 'MFA Drift', 'RTO Status'].map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => setSearchQuery(prompt)}
                    className="text-[11px] px-2.5 py-1 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface-variant border border-outline-variant/40 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
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

      {/* Mobile Bottom Navigation Bar - Material 3 NavigationBar */}
      <nav 
        className="md:hidden fixed bottom-0 left-0 right-0 bg-surface-container-low/95 dark:bg-surface-container-low/95 backdrop-blur-xl border-t border-outline-variant/40 z-40 pb-safe m3-elevation-2"
        style={{ bottom: 0, top: 'auto' }}
        aria-label="Mobile Bottom Navigation"
      >
        <ul className="flex justify-around items-center h-16 px-1">
          {[
            { to: '/morning-brief', icon: Calendar, label: 'Today' },
            { to: '/needs-attention', icon: AlertTriangle, label: 'Triage' },
            { to: '/recovery', icon: RotateCcw, label: 'Recovery' },
            { to: '/operations', icon: Layers, label: 'Ops' },
          ].map(({ to, icon: Icon, label }) => (
            <li key={to} className="flex-1">
              <NavLink 
                to={to} 
                className={({ isActive }) => 
                  `flex flex-col items-center justify-center py-1 w-full text-xs transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald rounded-2xl min-touch-target ${
                    isActive ? 'text-ready-emerald font-bold' : 'text-on-surface-variant hover:text-on-surface'
                  }`
                }
                aria-label={label}
              >
                {({ isActive }) => (
                  <>
                    <div className={`px-4 py-1 rounded-full transition-all duration-200 ${isActive ? 'bg-ready-emerald/20 text-ready-emerald font-bold shadow-xs' : 'text-on-surface-variant'}`}>
                      <Icon className="w-5 h-5 shrink-0" />
                    </div>
                    <span className="text-[11px] font-medium tracking-tight mt-0.5">{label}</span>
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}

