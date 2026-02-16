/**
 * User Data Utilities
 * 
 * Functions for managing user-specific cached data.
 * Used to prevent cross-user data leakage on logout.
 */

// All localStorage keys used by the app for user data
const USER_DATA_KEYS = [
  'airs_assessment_draft',  // Draft assessment data
  // Add any other user-specific keys here as they're added
];

/**
 * Clear all user-specific data from localStorage and sessionStorage.
 * Call this on logout to prevent cross-user data leakage.
 */
export function clearUserData(): void {
  console.log('[UserData] Clearing user-specific cached data');
  
  // Clear known user data keys from localStorage
  USER_DATA_KEYS.forEach((key) => {
    localStorage.removeItem(key);
  });
  
  // Clear all sessionStorage (session-scoped data)
  sessionStorage.clear();
  
  console.log('[UserData] User data cleared');
}

/**
 * Clear all local synthetic/staging data.
 * This is a more aggressive clear that removes all app-related localStorage.
 */
export function clearAllLocalData(): void {
  console.log('[UserData] Clearing all local data');
  
  // Clear all AIRS-related localStorage keys
  const keysToRemove: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith('airs_')) {
      keysToRemove.push(key);
    }
  }
  keysToRemove.forEach((key) => localStorage.removeItem(key));
  
  // Also clear sessionStorage
  sessionStorage.clear();
  
  console.log('[UserData] All local data cleared');
}

/**
 * Get a summary of what data is stored locally.
 * Useful for debugging and the Settings page.
 */
export function getLocalDataSummary(): { key: string; size: number }[] {
  const summary: { key: string; size: number }[] = [];
  
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith('airs_')) {
      const value = localStorage.getItem(key) || '';
      summary.push({
        key,
        size: value.length,
      });
    }
  }
  
  return summary;
}
