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

function isMissingOrFakeApiKey(value?: string): boolean {
  if (!value) return true;
  const normalized = value.trim().toLowerCase();
  return (
    normalized.length < 20 ||
    normalized.includes('fake') ||
    normalized.includes('replace') ||
    normalized.includes('placeholder')
  );
}

// Check if Firebase config is available and key looks valid for web auth usage.
export const isFirebaseConfigured = Boolean(
  firebaseConfig.authDomain &&
  firebaseConfig.projectId &&
  firebaseConfig.apiKey &&
  !isMissingOrFakeApiKey(firebaseConfig.apiKey)
);

// Initialize Firebase only if configured
let app: FirebaseApp | null = null;
let auth: Auth | null = null;
const isDevelopmentMode = import.meta.env.MODE === 'development';
const authEmulatorUrl =
  import.meta.env.VITE_FIREBASE_AUTH_EMULATOR ||
  (isDevelopmentMode ? 'http://127.0.0.1:9099' : '');

if (isFirebaseConfigured) {
  // Initialize Firebase (avoid duplicate initialization)
  app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
  auth = getAuth(app);

  // In development mode, keep Auth traffic local by default.
  // Call emulator wiring immediately after getAuth() and only once.
  if (isDevelopmentMode && authEmulatorUrl) {
    const alreadyConnected = Boolean((auth as unknown as { emulatorConfig?: unknown }).emulatorConfig);
    if (!alreadyConnected) {
      connectAuthEmulator(auth, authEmulatorUrl);
      console.log('[Firebase] Auth emulator enabled at:', authEmulatorUrl);
    }
  }
  
  console.log('[Firebase] Initialized with project:', firebaseConfig.projectId);
} else {
  console.warn('[Firebase] Not configured. Auth features will be disabled.');
  console.warn('[Firebase] Set VITE_FIREBASE_API_KEY, VITE_FIREBASE_AUTH_DOMAIN, VITE_FIREBASE_PROJECT_ID');
  if (isMissingOrFakeApiKey(firebaseConfig.apiKey)) {
    console.warn('[Firebase] VITE_FIREBASE_API_KEY is missing or placeholder/fake in this build.');
  }
}

export { app, auth };
export default app;
