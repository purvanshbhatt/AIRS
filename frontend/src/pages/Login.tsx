import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Button, Input } from '../components/ui';
import { Mail, Lock, Chrome, AlertCircle, Sparkles, KeyRound, ShieldCheck, ShieldAlert } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { signInWithGoogle, signInWithEmail, signUpWithEmail, signInAsDemo, error, clearError, isConfigured, loading } = useAuth();

  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as { from?: string })?.from || '/morning-brief';

  // Always clear any stale auth error on page mount
  useEffect(() => {
    clearError();
  }, [clearError]);

  const handleDemoSignIn = async () => {
    setSubmitting(true);
    clearError();
    try {
      await signInAsDemo();
      navigate(from, { replace: true });
    } catch {
      // Handled by context
    } finally {
      setSubmitting(false);
    }
  };

  const handleQuickStagingSignIn = async () => {
    setSubmitting(true);
    clearError();
    setEmail('staging-tester@resilai.io');
    setPassword('TestPassword123!');
    try {
      await signInWithEmail('staging-tester@resilai.io', 'TestPassword123!');
      navigate(from, { replace: true });
    } catch {
      // Handled by context
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setSubmitting(true);
    clearError();
    try {
      await signInWithGoogle();
      navigate(from, { replace: true });
    } catch {
      // Handled by context
    } finally {
      setSubmitting(false);
    }
  };

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;

    setSubmitting(true);
    clearError();
    try {
      if (mode === 'signin') {
        await signInWithEmail(email, password);
      } else {
        await signUpWithEmail(email, password);
      }
      navigate(from, { replace: true });
    } catch {
      // Handled by context
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-on-surface-variant font-mono text-xs">Authenticating workspace...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center mb-2">
            <div className="w-14 h-14 rounded-2xl bg-ready-emerald/15 border border-ready-emerald/30 flex items-center justify-center shadow-lg shadow-ready-emerald/10">
              <ShieldAlert className="w-8 h-8 text-ready-emerald" />
            </div>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-on-surface mt-2">ResilAI</h1>
          <p className="text-on-surface-variant text-xs mt-0.5">Healthcare Readiness & Compliance Intelligence</p>
        </div>

        <Card className="bg-surface-container-low border-surface-bright shadow-2xl">
          {/* Mode Switch Tabs */}
          <div className="grid grid-cols-2 p-1.5 bg-surface-container border-b border-outline-variant/30 text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setMode('signin');
                clearError();
              }}
              className={`py-2 rounded-lg transition-all ${
                mode === 'signin'
                  ? 'bg-surface-container-high text-ready-emerald font-bold shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Sign In to Workspace
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('signup');
                clearError();
              }}
              className={`py-2 rounded-lg transition-all ${
                mode === 'signup'
                  ? 'bg-surface-container-high text-ready-emerald font-bold shadow-sm'
                  : 'text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Register New Organization
            </button>
          </div>

          <CardHeader className="text-center pt-4 pb-2">
            <CardTitle className="text-lg text-on-surface">
              {mode === 'signin' ? 'Sign In to Live Workspace' : 'Create Organization Account'}
            </CardTitle>
            <CardDescription className="text-on-surface-variant text-xs">
              {mode === 'signin'
                ? 'Authenticate to access your organization evidence & connectors'
                : 'Register your email to establish an isolated clinic tenant'}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 bg-critical-red/10 border border-critical-red/30 rounded-xl text-critical-red text-xs flex items-start gap-2 animate-in fade-in">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span className="leading-relaxed">{error}</span>
              </div>
            )}

            {/* Email / Password Form (Primary) */}
            <form onSubmit={handleEmailSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@yourclinic.com"
                    className="pl-10 bg-surface-container border-outline-variant/50 focus:border-ready-emerald text-on-surface text-xs"
                    disabled={submitting}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-on-surface mb-1">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="pl-10 bg-surface-container border-outline-variant/50 focus:border-ready-emerald text-on-surface text-xs"
                    disabled={submitting}
                    required
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={submitting || !email.trim() || !password.trim()}
                className="w-full bg-ready-emerald hover:brightness-110 text-on-primary-container font-bold py-2.5 text-xs rounded-xl shadow-sm"
              >
                {submitting
                  ? 'Authenticating...'
                  : mode === 'signin' ? 'Sign In to Live Workspace' : 'Create & Onboard Organization'}
              </Button>
            </form>

            {/* 1-Click Staging Quick Sign-In Helper */}
            {mode === 'signin' && (
              <div className="p-3 bg-ready-emerald/10 border border-ready-emerald/30 rounded-xl flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <KeyRound className="w-4 h-4 text-ready-emerald shrink-0" />
                  <div className="text-left">
                    <p className="text-[11px] font-bold text-on-surface">Staging Test Account</p>
                    <p className="text-[10px] text-on-surface-variant font-mono">staging-tester@resilai.io</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleQuickStagingSignIn}
                  disabled={submitting}
                  className="px-3 py-1.5 bg-ready-emerald text-on-primary-container text-[11px] font-bold rounded-lg hover:brightness-110 transition-all shrink-0 shadow-sm"
                >
                  Quick Sign In
                </button>
              </div>
            )}

            {/* Social Authentication */}
            <div className="relative pt-1">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-outline-variant/40" />
              </div>
              <div className="relative flex justify-center text-[10px] uppercase tracking-wider">
                <span className="px-2 bg-surface-container-low text-on-surface-variant font-mono">or OAuth</span>
              </div>
            </div>

            <Button
              onClick={handleGoogleSignIn}
              disabled={submitting}
              variant="outline"
              className="w-full flex items-center justify-center gap-2 border-surface-bright hover:bg-surface-container-high text-on-surface py-2 text-xs rounded-xl"
            >
              <Chrome className="w-3.5 h-3.5" />
              <span>Continue with Google</span>
            </Button>

            {/* Evaluation Demo Sandbox */}
            <div className="pt-3 border-t border-outline-variant/40">
              <div className="p-3 bg-surface-container rounded-xl border border-surface-bright space-y-2 text-left">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-on-surface uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                    Evaluation Sandbox
                  </span>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-500 border border-amber-500/30">SIMULATED DATA</span>
                </div>
                <p className="text-[11px] text-on-surface-variant leading-relaxed">
                  Explore ResilAI with pre-populated healthcare clinic telemetry without creating an account.
                </p>
                <Button
                  onClick={handleDemoSignIn}
                  disabled={submitting}
                  variant="outline"
                  className="w-full flex items-center justify-center gap-1.5 border-ready-emerald/40 text-ready-emerald hover:bg-ready-emerald/10 font-semibold py-1.5 rounded-lg text-xs"
                >
                  <span>Enter Demo Environment (Acme Health)</span>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-[11px] text-on-surface-variant mt-4 font-mono">
          Deterministic incident readiness powered by live evidence verification.
        </p>
      </div>
    </div>
  );
}
