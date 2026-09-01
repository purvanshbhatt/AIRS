/**
 * Authentication Context
 *
 * Provides Firebase authentication state and methods throughout the app.
 * Automatically injects auth tokens into API requests.
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
} from 'react';
import {
  User as FirebaseUser,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  onAuthStateChanged,
} from 'firebase/auth';
import { auth, isFirebaseConfigured } from '../lib/firebase';
import { setTokenProvider } from '../api';
import { clearUserData } from '../lib/userData';

// User type exposed to app
export interface User {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
}

// Auth context value
interface AuthContextValue {
  user: User | null;
  loading: boolean;
  error: string | null;
  isConfigured: boolean;
  hasOrganizations: boolean | null;
  getToken: () => Promise<string | null>;
  signInWithGoogle: () => Promise<void>;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  signInAsDemo: () => Promise<void>;
  signOut: () => Promise<void>;
  clearError: () => void;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// Hook to access auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Convert Firebase user to our User type
function toUser(firebaseUser: FirebaseUser): User {
  return {
    uid: firebaseUser.uid,
    email: firebaseUser.email,
    displayName: firebaseUser.displayName,
    photoURL: firebaseUser.photoURL,
  };
}

// Auth provider component
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(() => {
    const isDemo = typeof window !== 'undefined' ? localStorage.getItem('resilai_demo_user') : null;
    if (isDemo === 'true') {
      return {
        uid: 'demo-executive-uid',
        email: 'executive@acme-health.resilai.io',
        displayName: 'Dr. Evelyn Reed (CMO & Exec Lead)',
        photoURL: null,
      };
    }
    return null;
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasOrganizations, setHasOrganizations] = useState<boolean | null>(() => {
    const isDemo = typeof window !== 'undefined' ? localStorage.getItem('resilai_demo_user') : null;
    return isDemo === 'true' ? true : null;
  });

  // Listen for auth state changes
  useEffect(() => {
    const isDemoActive = localStorage.getItem('resilai_demo_user') === 'true';

    if (!isFirebaseConfigured || !auth) {
      console.log('[Auth] Firebase not configured, skipping auth listener');
      setLoading(false);
      return;
    }

    console.log('[Auth] Setting up auth state listener');
    let isMounted = true;

    // Await authStateReady to prevent 401 race condition during initial page hydration
    auth.authStateReady()
      .then(() => {
        if (!isMounted) return;
        if (auth.currentUser) {
          localStorage.removeItem('resilai_demo_user');
          setUser(toUser(auth.currentUser));
        }
      })
      .catch((err) => {
        console.error('[Auth] authStateReady error:', err);
      });

    const unsubscribe = onAuthStateChanged(
      auth,
      (firebaseUser) => {
        if (!isMounted) return;
        if (firebaseUser) {
          console.log('[Auth] User signed in:', firebaseUser.email);
          localStorage.removeItem('resilai_demo_user');
          setUser(toUser(firebaseUser));
          
          // Verify workspace context and handle missing org profiles gracefully
          setTokenProvider(async () => firebaseUser.getIdToken());
          import('../api').then(({ getOrganizations }) => {
            getOrganizations().then(orgs => {
              if (orgs && orgs.length > 0) {
                setHasOrganizations(true);
                const saved = localStorage.getItem('resilai_selected_org_id');
                if (!saved || !orgs.find(o => o.id === saved)) {
                  localStorage.setItem('resilai_selected_org_id', orgs[0].id);
                }
              } else {
                setHasOrganizations(false);
                localStorage.removeItem('resilai_selected_org_id');
              }
              setLoading(false);
            }).catch(err => {
              console.error('[Auth] Failed to fetch orgs:', err);
              setLoading(false);
            });
          }).catch(err => {
            console.error('[Auth] Failed to import API:', err);
            setLoading(false);
          });
          
        } else {
          if (localStorage.getItem('resilai_demo_user') === 'true') {
            console.log('[Auth] Active Sandbox demo session retained');
            setUser({
              uid: 'demo-executive-uid',
              email: 'executive@acme-health.resilai.io',
              displayName: 'Dr. Evelyn Reed (CMO & Exec Lead)',
              photoURL: null,
            });
            setHasOrganizations(true);
            setLoading(false);
          } else {
            console.log('[Auth] No user signed in');
            setUser(null);
            setHasOrganizations(null);
            localStorage.removeItem('resilai_selected_org_id');
            setLoading(false);
          }
        }
      },
      (err) => {
        if (!isMounted) return;
        console.warn('[Auth] Auth state observer notice (unauthenticated):', err);
        // Do NOT set a blocking form error on initial passive page load
        setUser(null);
        setHasOrganizations(null);
        localStorage.removeItem('resilai_selected_org_id');
        setLoading(false);
      }
    );

    return () => {
      isMounted = false;
      unsubscribe();
    };
  }, []);

  // Get auth token for API requests
  const getToken = useCallback(async (): Promise<string | null> => {
    if (!auth) {
      return null;
    }
    try {
      if (typeof auth.authStateReady === 'function') {
        await auth.authStateReady();
      }
      if (!auth.currentUser) {
        return null;
      }
      const token = await auth.currentUser.getIdToken();
      return token;
    } catch (err) {
      console.error('[Auth] Failed to get token:', err);
      return null;
    }
  }, []);

  // Register token provider with API client
  useEffect(() => {
    setTokenProvider(getToken);
  }, [getToken]);

  // Sign in with Google
  const signInWithGoogle = useCallback(async (): Promise<void> => {
    if (!isFirebaseConfigured || !auth) {
      setError('Firebase not configured. Check environment variables.');
      return;
    }

    setError(null);
    try {
      const provider = new GoogleAuthProvider();
      provider.setCustomParameters({ prompt: 'select_account' });
      await signInWithPopup(auth, provider);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to sign in with Google';
      console.error('[Auth] Google sign in error:', err);
      // Don't show popup closed errors
      if (!message.includes('popup-closed') && !message.includes('cancelled-popup-request')) {
        setError(formatFirebaseError(message));
      }
      throw err;
    }
  }, []);

  // Sign in with email/password
  const signInWithEmail = useCallback(async (email: string, password: string): Promise<void> => {
    if (!isFirebaseConfigured || !auth) {
      setError('Firebase not configured. Check environment variables.');
      return;
    }

    setError(null);
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to sign in';
      console.error('[Auth] Email sign in error:', err);
      setError(formatFirebaseError(message));
      throw err;
    }
  }, []);

  // Sign up with email/password
  const signUpWithEmail = useCallback(async (email: string, password: string): Promise<void> => {
    if (!isFirebaseConfigured || !auth) {
      setError('Firebase not configured. Check environment variables.');
      return;
    }

    setError(null);
    try {
      await createUserWithEmailAndPassword(auth, email, password);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create account';
      console.error('[Auth] Email sign up error:', err);
      setError(formatFirebaseError(message));
      throw err;
    }
  }, []);

  // Enter Sandbox Demo Mode as Demo Healthcare Executive
  const signInAsDemo = useCallback(async (): Promise<void> => {
    setError(null);
    localStorage.setItem('resilai_demo_user', 'true');
    localStorage.setItem('resilai_selected_org_id', 'demo-health-org');
    const demoUser: User = {
      uid: 'demo-executive-uid',
      email: 'executive@acme-health.resilai.io',
      displayName: 'Dr. Evelyn Reed (CMO & Exec Lead)',
      photoURL: null,
    };
    setUser(demoUser);
    setHasOrganizations(true);
    setLoading(false);
  }, []);

  // Sign out
  const signOut = useCallback(async (): Promise<void> => {
    // Clear user-specific cached data to prevent cross-user leakage
    clearUserData();
    localStorage.removeItem('resilai_demo_user');
    localStorage.removeItem('resilai_selected_org_id');
    setUser(null);
    setHasOrganizations(null);
    
    if (!auth) {
      return;
    }

    try {
      await firebaseSignOut(auth);
    } catch (err) {
      console.error('[Auth] Sign out error:', err);
    }
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Force a refresh of the user's context (e.g. after creating an organization)
  const refreshAuth = useCallback(async (): Promise<void> => {
    if (!auth || !auth.currentUser) return;
    try {
      setLoading(true);
      const { getOrganizations } = await import('../api');
      const orgs = await getOrganizations();
      if (orgs && orgs.length > 0) {
        setHasOrganizations(true);
        const saved = localStorage.getItem('resilai_selected_org_id');
        if (!saved || !orgs.find(o => o.id === saved)) {
          localStorage.setItem('resilai_selected_org_id', orgs[0].id);
        }
      } else {
        setHasOrganizations(false);
        localStorage.removeItem('resilai_selected_org_id');
      }
    } catch (err) {
      console.error('[Auth] Failed to refresh orgs:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const value: AuthContextValue = {
    user,
    loading,
    error,
    isConfigured: isFirebaseConfigured,
    hasOrganizations,
    getToken,
    signInWithGoogle,
    signInWithEmail,
    signUpWithEmail,
    signInAsDemo,
    signOut,
    clearError,
    refreshAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Format Firebase error messages to be user-friendly
function formatFirebaseError(message: string): string {
  if (message.includes('auth/invalid-email')) {
    return 'Invalid email address.';
  }
  if (message.includes('auth/user-disabled')) {
    return 'This account has been disabled.';
  }
  if (message.includes('auth/user-not-found')) {
    return 'No account found with this email.';
  }
  if (message.includes('auth/wrong-password') || message.includes('auth/invalid-credential')) {
    return 'Invalid email or password.';
  }
  if (message.includes('auth/email-already-in-use')) {
    return 'An account with this email already exists. Please switch to Sign in.';
  }
  if (message.includes('auth/weak-password')) {
    return 'Password should be at least 6 characters.';
  }
  if (message.includes('auth/popup-blocked')) {
    return 'Sign-in popup was blocked by your browser. Please allow popups for this site.';
  }
  if (message.includes('auth/popup-closed-by-user')) {
    return '';
  }
  if (message.includes('auth/network-request-failed')) {
    return 'Network error. Check your connection.';
  }
  if (message.includes('auth/too-many-requests')) {
    return 'Too many attempts. Please try again later.';
  }
  if (message.includes('auth/api-keys-are-not-supported-by-this-api')) {
    return 'Authentication service is re-authenticating. Please try signing in again with email/password or reload the page.';
  }
  return message;
}

export default AuthContext;
