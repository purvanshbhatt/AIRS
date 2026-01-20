/**
 * Authentication Context
 *
 * Provides auth state and methods throughout the app.
 * Currently a placeholder that returns null - ready for Firebase Auth integration.
 *
 * ## Firebase Integration (Future)
 *
 * To integrate Firebase Auth:
 *
 * 1. Install Firebase:
 *    ```bash
 *    npm install firebase
 *    ```
 *
 * 2. Create `src/lib/firebase.ts`:
 *    ```typescript
 *    import { initializeApp } from 'firebase/app';
 *    import { getAuth } from 'firebase/auth';
 *
 *    const firebaseConfig = {
 *      apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
 *      authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
 *      projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
 *    };
 *
 *    export const app = initializeApp(firebaseConfig);
 *    export const auth = getAuth(app);
 *    ```
 *
 * 3. Update this context to use Firebase:
 *    - Import `auth` from firebase.ts
 *    - Use `onAuthStateChanged` to track user
 *    - Use `signInWithPopup` / `signInWithEmailAndPassword` for login
 *    - Use `auth.currentUser.getIdToken()` to get JWT for API calls
 *
 * 4. Update `api.ts` to include token in headers:
 *    ```typescript
 *    const token = await getToken();
 *    headers: { Authorization: `Bearer ${token}` }
 *    ```
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
} from 'react';
import { setTokenProvider } from '../api';

// User type - matches Firebase User structure
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
  getToken: () => Promise<string | null>;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
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

// Auth provider component
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize auth state
  useEffect(() => {
    // TODO: Replace with Firebase onAuthStateChanged
    // For now, simulate checking auth state
    const checkAuth = async () => {
      try {
        // Placeholder: In local dev, we don't require auth
        // When Firebase is integrated, this will check actual auth state
        setUser(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Auth error');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Get auth token for API requests
  const getToken = useCallback(async (): Promise<string | null> => {
    // TODO: Replace with Firebase getIdToken()
    // return user ? await auth.currentUser?.getIdToken() : null;

    // Placeholder: Return null (no token required in local mode)
    return null;
  }, []);

  // Register token provider with API client
  useEffect(() => {
    setTokenProvider(getToken);
  }, [getToken]);

  // Sign in method
  const signIn = useCallback(async (): Promise<void> => {
    // TODO: Replace with Firebase signInWithPopup or signInWithEmailAndPassword
    // Example:
    // const provider = new GoogleAuthProvider();
    // await signInWithPopup(auth, provider);

    setError('Sign in not implemented - Firebase integration required');
    console.warn('Auth: signIn() called but Firebase is not configured');
  }, []);

  // Sign out method
  const signOut = useCallback(async (): Promise<void> => {
    // TODO: Replace with Firebase signOut
    // await auth.signOut();

    setUser(null);
    console.warn('Auth: signOut() called but Firebase is not configured');
  }, []);

  const value: AuthContextValue = {
    user,
    loading,
    error,
    getToken,
    signIn,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthContext;
