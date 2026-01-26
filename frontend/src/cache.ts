/**
 * Simple in-memory cache for API responses.
 * 
 * Features:
 *   - TTL-based expiration (default 60 seconds)
 *   - Manual cache invalidation by key or prefix
 *   - Cache statistics for debugging
 */

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

export interface CacheStats {
  hits: number;
  misses: number;
  size: number;
  keys: string[];
}

class ApiCache {
  private cache: Map<string, CacheEntry<unknown>> = new Map();
  private defaultTTL: number = 60 * 1000; // 60 seconds
  private hits: number = 0;
  private misses: number = 0;

  /**
   * Get a cached value if it exists and is not expired.
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    
    if (!entry) {
      this.misses++;
      return null;
    }
    
    if (Date.now() > entry.expiresAt) {
      // Expired - remove and return null
      this.cache.delete(key);
      this.misses++;
      return null;
    }
    
    this.hits++;
    return entry.data as T;
  }

  /**
   * Set a cached value with optional TTL.
   */
  set<T>(key: string, data: T, ttlMs?: number): void {
    const now = Date.now();
    const ttl = ttlMs ?? this.defaultTTL;
    
    this.cache.set(key, {
      data,
      timestamp: now,
      expiresAt: now + ttl,
    });
  }

  /**
   * Invalidate a specific cache key.
   */
  invalidate(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Invalidate all cache keys that start with a prefix.
   */
  invalidatePrefix(prefix: string): number {
    let count = 0;
    for (const key of this.cache.keys()) {
      if (key.startsWith(prefix)) {
        this.cache.delete(key);
        count++;
      }
    }
    return count;
  }

  /**
   * Invalidate all cache entries.
   */
  invalidateAll(): void {
    this.cache.clear();
  }

  /**
   * Get cache statistics.
   */
  getStats(): CacheStats {
    return {
      hits: this.hits,
      misses: this.misses,
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    };
  }

  /**
   * Set the default TTL for new entries.
   */
  setDefaultTTL(ttlMs: number): void {
    this.defaultTTL = ttlMs;
  }
}

// Singleton cache instance
export const apiCache = new ApiCache();

// Cache keys
export const CACHE_KEYS = {
  ORGANIZATIONS: 'orgs',
  ASSESSMENTS: 'assessments',
  REPORTS: 'reports',
  SUMMARY: (id: string) => `summary:${id}`,
} as const;

// Cache TTLs (in milliseconds)
export const CACHE_TTL = {
  LIST: 60 * 1000,      // 60 seconds for list endpoints
  SUMMARY: 5 * 60 * 1000, // 5 minutes for summaries (rarely changes)
} as const;

/**
 * Cache-aware fetch wrapper.
 * Returns cached data if available, otherwise fetches and caches.
 */
export async function cachedFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttlMs: number = CACHE_TTL.LIST
): Promise<T> {
  // Check cache first
  const cached = apiCache.get<T>(key);
  if (cached !== null) {
    console.log(`[Cache] HIT: ${key}`);
    return cached;
  }
  
  // Cache miss - fetch data
  console.log(`[Cache] MISS: ${key}`);
  const data = await fetcher();
  apiCache.set(key, data, ttlMs);
  return data;
}

/**
 * Invalidate caches after mutations.
 */
export function invalidateAfterMutation(type: 'org' | 'assessment' | 'report'): void {
  switch (type) {
    case 'org':
      apiCache.invalidate(CACHE_KEYS.ORGANIZATIONS);
      // Also invalidate assessments since org names are included
      apiCache.invalidate(CACHE_KEYS.ASSESSMENTS);
      break;
    case 'assessment':
      apiCache.invalidate(CACHE_KEYS.ASSESSMENTS);
      // Invalidate all summaries since assessment changed
      apiCache.invalidatePrefix('summary:');
      break;
    case 'report':
      apiCache.invalidate(CACHE_KEYS.REPORTS);
      break;
  }
  console.log(`[Cache] Invalidated after ${type} mutation`);
}
