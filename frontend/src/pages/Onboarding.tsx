import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { getOrganizations } from '../api';
import { CreateWorkspaceScreen } from '../components/onboarding/CreateWorkspaceScreen';

/**
 * /onboarding: one screen that creates the first workspace.
 *
 * - A signed-in user who already has a workspace is sent to the morning brief,
 *   unless they arrived with ?new=true to add another one.
 * - Everything the old six-step wizard explained now lives in the first-run
 *   checklist on the morning brief, next to the action it describes.
 */
export default function Onboarding() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, signOut, loading: authLoading } = useAuth();
  const isAdditional = new URLSearchParams(location.search).get('new') === 'true';
  const [checkingOrgs, setCheckingOrgs] = useState(!isAdditional);

  const isRealUser = Boolean(user && user.uid && user.uid !== 'demo-executive-uid');

  useEffect(() => {
    if (authLoading || isAdditional) return;
    if (!isRealUser) {
      setCheckingOrgs(false);
      return;
    }
    let cancelled = false;
    getOrganizations()
      .then((orgs) => {
        if (cancelled) return;
        if (orgs && orgs.length > 0) {
          const saved = localStorage.getItem('resilai_selected_org_id');
          const target = saved && orgs.find((o) => o.id === saved) ? saved : orgs[0].id;
          localStorage.setItem('resilai_selected_org_id', target);
          navigate('/morning-brief', { replace: true });
          return;
        }
        setCheckingOrgs(false);
      })
      .catch((err) => {
        console.warn('[Onboarding] Could not check organisations:', err);
        if (!cancelled) setCheckingOrgs(false);
      });
    return () => {
      cancelled = true;
    };
  }, [authLoading, isAdditional, isRealUser, navigate]);

  const handleSignOut = async () => {
    await signOut();
    navigate('/login', { replace: true });
  };

  if (authLoading || checkingOrgs) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-on-surface-variant text-sm">Getting things ready...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-on-surface flex flex-col selection:bg-ready-emerald/30 selection:text-ready-emerald">
      <header className="h-16 border-b border-outline-variant/40 bg-surface-container-low/90 backdrop-blur-md px-4 sm:px-8 flex items-center justify-between z-30">
        <div className="flex items-center gap-3">
          <img src="/brand/horizontal/resilai_horizontal_light_trans.png" alt="ResilAI" className="h-7 w-auto object-contain block dark:hidden" />
          <img src="/brand/horizontal/resilai_horizontal_dark_trans.png" alt="ResilAI" className="h-7 w-auto object-contain hidden dark:block" />
        </div>
        {user?.email && (
          <span className="text-xs text-on-surface-variant hidden sm:inline">
            Signed in as <strong className="text-on-surface">{user.email}</strong>
          </span>
        )}
      </header>

      <main className="flex-1 w-full px-4 py-8 sm:py-14 flex items-start justify-center">
        <CreateWorkspaceScreen isAdditional={isAdditional} />
      </main>

      <footer className="h-14 border-t border-outline-variant/30 px-6 flex items-center justify-end text-xs text-on-surface-variant bg-surface-container-lowest">
        <button
          type="button"
          onClick={handleSignOut}
          className="hover:text-critical-red flex items-center gap-1.5 transition-colors font-medium"
        >
          <LogOut className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Sign out</span>
        </button>
      </footer>
    </div>
  );
}
