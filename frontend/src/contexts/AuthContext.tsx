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
  getToken: () => Promise<string | null>;
  signInWithGoogle: () => Promise<void>;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  clearError: () => void;
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
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Listen for auth state changes
  useEffect(() => {
    if (!isFirebaseConfigured || !auth) {
      console.log('[Auth] Firebase not configured, skipping auth listener');
      setLoading(false);
      return;
    }

    console.log('[Auth] Setting up auth state listener');
    const unsubscribe = onAuthStateChanged(
      auth,
      (firebaseUser) => {
        if (firebaseUser) {
          console.log('[Auth] User signed in:', firebaseUser.email);
          setUser(toUser(firebaseUser));
        } else {
          console.log('[Auth] No user signed in');
          setUser(null);
        }
        setLoading(false);
      },
      (err) => {
        console.error('[Auth] Auth state error:', err);
        setError(err.message);
        setLoading(false);
      }
    );

    return () => unsubscribe();
  }, []);

  // Get auth token for API requests
  const getToken = useCallback(async (): Promise<string | null> => {
    if (!auth?.currentUser) {
      return null;
    }
    try {
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
      await signInWithPopup(auth, provider);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to sign in with Google';
      console.error('[Auth] Google sign in error:', err);
      // Don't show popup closed errors
      if (!message.includes('popup-closed')) {
        setError(message);
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

  // Sign out
  const signOut = useCallback(async (): Promise<void> => {
    // Clear user-specific cached data to prevent cross-user leakage
    clearUserData();
    
    if (!auth) {
      setUser(null);
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

  const value: AuthContextValue = {
    user,
    loading,
    error,
    isConfigured: isFirebaseConfigured,
    getToken,
    signInWithGoogle,
    signInWithEmail,
    signUpWithEmail,
    signOut,
    clearError,
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
    return 'An account with this email already exists.';
  }
  if (message.includes('auth/weak-password')) {
    return 'Password should be at least 6 characters.';
  }
  if (message.includes('auth/network-request-failed')) {
    return 'Network error. Check your connection.';
  }
  if (message.includes('auth/too-many-requests')) {
    return 'Too many attempts. Please try again later.';
  }
  return message;
}

export default AuthContext;
