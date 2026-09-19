import { useState, useContext, useMemo } from 'react';
import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { Shield, Menu, X, ArrowRight, Sparkles, ExternalLink } from 'lucide-react';
import ThemeToggle from '../ui/ThemeToggle';
import { ThemeContext, ThemeProvider } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { useVertical, detectVerticalFromLocation } from '../../contexts/VerticalContext';
import { getVerticalConfig } from '../../config/verticals';
import type { VerticalKey, VerticalConfig } from '../../types/vertical';

function SafeThemeToggle() {
  const context = useContext(ThemeContext);
  if (!context) {
    return (
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );
  }
  return <ThemeToggle />;
}

export interface PublicNavbarProps {
  transparent?: boolean;
  currentVertical?: VerticalKey;
}

export function PublicNavbar({ transparent = false, currentVertical: propCurrentVertical }: PublicNavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  let navigate: ReturnType<typeof useNavigate> | undefined;
  try {
    navigate = useNavigate();
  } catch {
    // Outside Router
  }

  let locationSearch = '';
  let locationPathname = '';
  try {
    const loc = useLocation();
    locationSearch = loc.search;
    locationPathname = loc.pathname;
  } catch {
    // Outside Router
  }

  const { signInAsDemo, clearError } = useAuth();

  let contextVertical: VerticalKey = 'general';
  let contextConfig: VerticalConfig = getVerticalConfig('general');

  try {
    const vContext = useVertical();
    contextVertical = vContext.currentVertical;
    contextConfig = vContext.config;
  } catch {
    // Graceful fallback if rendered outside VerticalProvider
  }

  const detectedFromRoute = useMemo(() => {
    return detectVerticalFromLocation({
      search: locationSearch,
      pathname: locationPathname,
    });
  }, [locationSearch, locationPathname]);

  const effectiveVertical: VerticalKey = useMemo(() => {
    if (propCurrentVertical) {
      return propCurrentVertical;
    }
    if (detectedFromRoute.source === 'query' || detectedFromRoute.source === 'path') {
      return detectedFromRoute.vertical;
    }
    return contextVertical;
  }, [propCurrentVertical, detectedFromRoute, contextVertical]);

  const effectiveConfig: VerticalConfig = useMemo(() => {
    if (effectiveVertical === contextVertical) {
      return contextConfig;
    }
    return getVerticalConfig(effectiveVertical);
  }, [effectiveVertical, contextVertical, contextConfig]);

  const currentVertical = effectiveVertical;
  const config = effectiveConfig;

  const handleEnterSandbox = async () => {
    clearError();
    try {
      await signInAsDemo();
    } catch {
      // ignore
    } finally {
      localStorage.setItem('resilai_demo_user', 'true');
      localStorage.setItem('resilai_selected_org_id', config.demoOrgId);
      if (navigate) {
        navigate(`/morning-brief?vertical=${currentVertical}`, { replace: true });
      } else if (typeof window !== 'undefined') {
        window.location.href = `/morning-brief?vertical=${currentVertical}`;
      }
    }
  };

  const homeLink = currentVertical === 'general' ? '/' : `/${currentVertical}`;
  const loginLink = currentVertical === 'general' ? '/login' : `/login?vertical=${currentVertical}`;


  const navLinks = [
    { label: 'Product', to: currentVertical === 'general' ? '/#how-it-works' : `/${currentVertical}#how-it-works` },
    { label: 'Results', to: currentVertical === 'general' ? '/results' : `/results?vertical=${currentVertical}` },
    { label: 'AI Architecture', to: currentVertical === 'general' ? '/ai' : `/ai?vertical=${currentVertical}` },
    { label: 'Pricing', to: currentVertical === 'general' ? '/pricing' : `/pricing?vertical=${currentVertical}` },
    { label: 'About Us', to: currentVertical === 'general' ? '/about' : `/about?vertical=${currentVertical}` },
    { label: 'Contact', to: currentVertical === 'general' ? '/contact' : `/contact?vertical=${currentVertical}` },
  ];
  const docsLink = currentVertical === 'general' ? '/docs/methodology' : `/docs/methodology?vertical=${currentVertical}`;

  return (
    <header
      className={`sticky top-0 z-50 w-full transition-colors duration-300 ${
        transparent
          ? 'bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800/80'
          : 'bg-white/90 dark:bg-slate-950/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <Link
            to={homeLink}
            className="flex items-center gap-2.5 text-slate-900 dark:text-slate-100 font-bold tracking-tight text-lg group focus:outline-hidden focus-visible:ring-2 focus-visible:ring-primary-500 rounded-lg py-1 px-1.5"
            aria-label={`${config.displayName} Home`}
            data-testid="navbar-brand-link"
          >
            <img
              src="/logo_header.svg"
              alt="ResilAI Logo"
              className="h-9 w-auto dark:brightness-0 dark:invert transition-transform duration-300 group-hover:scale-105"
            />
            {currentVertical !== 'general' && (
              <span
                data-testid="navbar-vertical-badge"
                className="hidden sm:inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary-100 dark:bg-primary-950/60 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800/60"
              >
                {config.industryLabel}
              </span>
            )}
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1 xl:gap-2">
            {navLinks.map(({ label, to }) => {
              const isAnchor = to.includes('#');
              if (isAnchor) {
                return (
                  <a
                    key={label}
                    href={to}
                    className="px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors"
                  >
                    {label}
                  </a>
                );
              }
              return (
                <NavLink
                  key={label}
                  to={to}
                  className={({ isActive }) =>
                    `px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                      isActive
                        ? 'text-primary-600 dark:text-primary-400 bg-primary-50/70 dark:bg-primary-950/40 font-semibold'
                        : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
                    }`
                  }
                >
                  {label}
                </NavLink>
              );
            })}
            <Link
              to={docsLink}
              className="px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors flex items-center gap-1"
            >
              Docs
            </Link>
          </nav>

          {/* Right Action Buttons */}
          <div className="hidden sm:flex items-center gap-3">
            <SafeThemeToggle />
            <Link
              to={loginLink}
              className="text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white px-3 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors"
            >
              Sign In
            </Link>
            <button
              onClick={handleEnterSandbox}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 transition-all active:scale-[0.98] cursor-pointer"
              title={`Explore ${config.demoOrgName} Demo Sandbox`}
              data-testid="navbar-demo-cta"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>Demo</span>
            </button>
            <Link
              to={loginLink}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-primary-600 to-emerald-500 text-white shadow-xs hover:shadow-md hover:shadow-primary-500/20 transition-all active:scale-[0.98]"
            >
              <span>Get Started</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Mobile menu trigger */}
          <div className="flex items-center gap-2 lg:hidden">
            <SafeThemeToggle />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-primary-500"
              aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-950/95 backdrop-blur-lg px-4 pt-2 pb-6 space-y-3 animate-fadeIn">
          <nav className="flex flex-col space-y-1">
            {navLinks.map(({ label, to }) => {
              const isAnchor = to.includes('#');
              if (isAnchor) {
                return (
                  <a
                    key={label}
                    href={to}
                    onClick={() => setMobileMenuOpen(false)}
                    className="px-3 py-2.5 text-base font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60 rounded-lg transition-colors"
                  >
                    {label}
                  </a>
                );
              }
              return (
                <NavLink
                  key={label}
                  to={to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `px-3 py-2.5 text-base font-medium rounded-lg transition-colors ${
                      isActive
                        ? 'text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-950/40 font-semibold'
                        : 'text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60'
                    }`
                  }
                >
                  {label}
                </NavLink>
              );
            })}
            <Link
              to={docsLink}
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2.5 text-base font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60 rounded-lg transition-colors"
            >
              Scoring Methodology & Docs
            </Link>
          </nav>

          <div className="pt-4 border-t border-slate-200 dark:border-slate-800/80 flex flex-col gap-2.5">
            <Link
              to={loginLink}
              onClick={() => setMobileMenuOpen(false)}
              className="w-full text-center py-2.5 text-sm font-semibold text-slate-800 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
            >
              Sign In to Organization
            </Link>
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                handleEnterSandbox();
              }}
              className="w-full inline-flex items-center justify-center gap-2 py-2.5 text-sm font-semibold rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30 hover:bg-amber-500/20 transition-all"
              data-testid="navbar-mobile-demo-cta"
            >
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span>Explore Demo Sandbox ({config.demoOrgName})</span>
            </button>
            <Link
              to={loginLink}
              onClick={() => setMobileMenuOpen(false)}
              className="w-full inline-flex items-center justify-center gap-2 py-3 text-sm font-bold rounded-xl bg-gradient-to-r from-primary-600 to-emerald-500 text-white shadow-md hover:shadow-lg transition-all"
            >
              <span>Get Started</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

export default PublicNavbar;
