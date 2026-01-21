/**
 * Firebase Configuration
 * 
 * Initializes Firebase app and exports auth instance.
 * Uses environment variables for configuration.
 */

import { initializeApp, getApps, getApp, FirebaseApp } from 'firebase/app';
import { getAuth, connectAuthEmulator, Auth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
};

// Check if Firebase config is available
export const isFirebaseConfigured = Boolean(
  firebaseConfig.apiKey && 
  firebaseConfig.authDomain && 
  firebaseConfig.projectId
);

// Initialize Firebase only if configured
let app: FirebaseApp | null = null;
let auth: Auth | null = null;

if (isFirebaseConfigured) {
  // Initialize Firebase (avoid duplicate initialization)
  app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
  auth = getAuth(app);
  
  // Connect to emulator in development if configured
  if (import.meta.env.DEV && import.meta.env.VITE_FIREBASE_AUTH_EMULATOR) {
    connectAuthEmulator(auth, import.meta.env.VITE_FIREBASE_AUTH_EMULATOR);
  }
  
  console.log('[Firebase] Initialized with project:', firebaseConfig.projectId);
} else {
  console.warn('[Firebase] Not configured. Auth features will be disabled.');
  console.warn('[Firebase] Set VITE_FIREBASE_API_KEY, VITE_FIREBASE_AUTH_DOMAIN, VITE_FIREBASE_PROJECT_ID');
}

export { app, auth };
export default app;
