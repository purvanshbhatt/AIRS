import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Button, Input } from '../components/ui';
import { Shield, Mail, Lock, Chrome, AlertCircle } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { signInWithGoogle, signInWithEmail, signUpWithEmail, error, clearError, isConfigured, loading } = useAuth();

  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as { from?: string })?.from || '/dashboard';

  const handleGoogleSignIn = async () => {
    setSubmitting(true);
    clearError();
    try {
      await signInWithGoogle();
      navigate(from, { replace: true });
    } catch {
      // Error is handled by AuthContext
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
      // Error is handled by AuthContext
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="animate-pulse text-gray-500 dark:text-slate-300">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-slate-950 dark:to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">ResilAI</h1>
          <p className="text-gray-500 dark:text-slate-300 text-sm mt-1">AI Incident Readiness Score</p>
        </div>

        <Card variant="elevated">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-xl">
              {mode === 'signin' ? 'Welcome Back' : 'Create Account'}
            </CardTitle>
            <CardDescription>
              {mode === 'signin'
                ? 'Sign in to access your security assessments'
                : 'Create an account to get started'}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {!isConfigured && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm flex items-start gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium">Firebase not configured</p>
                  <p className="text-xs mt-1">
                    Set VITE_FIREBASE_API_KEY, VITE_FIREBASE_AUTH_DOMAIN, and VITE_FIREBASE_PROJECT_ID
                  </p>
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-start gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <Button
              onClick={handleGoogleSignIn}
              disabled={!isConfigured || submitting}
              variant="outline"
              className="w-full flex items-center justify-center gap-2"
            >
              <Chrome className="w-4 h-4" />
              Continue with Google
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200 dark:border-slate-700" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white dark:bg-gray-900 text-gray-500 dark:text-slate-300">or</span>
              </div>
            </div>

            <form onSubmit={handleEmailSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-1">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    className="pl-10"
                    disabled={!isConfigured || submitting}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-1">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="********"
                    className="pl-10"
                    disabled={!isConfigured || submitting}
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={!isConfigured || submitting || !email.trim() || !password.trim()}
                className="w-full"
              >
                {submitting
                  ? 'Please wait...'
                  : mode === 'signin' ? 'Sign In' : 'Create Account'}
              </Button>
            </form>

            <div className="text-center text-sm">
              {mode === 'signin' ? (
                <p className="text-gray-600 dark:text-slate-300">
                  Don&apos;t have an account?{' '}
                  <button
                    onClick={() => {
                      setMode('signup');
                      clearError();
                    }}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Sign up
                  </button>
                </p>
              ) : (
                <p className="text-gray-600 dark:text-slate-300">
                  Already have an account?{' '}
                  <button
                    onClick={() => {
                      setMode('signin');
                      clearError();
                    }}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Sign in
                  </button>
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-gray-400 dark:text-slate-400 mt-6">
          Public Beta environment with synthetic example data.
        </p>
      </div>
    </div>
  );
}
