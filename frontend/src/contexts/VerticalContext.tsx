/**
 * VerticalContext Provider & Hook
 * 
 * Provides host-aware and path-aware multi-vertical positioning context
 * with strict precedence:
 * 1. URL Query parameter (?vertical=healthcare | legal | general)
 * 2. URL Path prefix (/healthcare, /legal, /general)
 * 3. Hostname subdomain (healthcare.staging.resilai.org, legal.staging.resilai.org, etc.)
 * 4. Default fallback: 'general'
 * 
 * Guarantees synchronous static config availability with optional public config enrichment.
 */

import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import type {
  VerticalKey,
  VerticalConfig,
  VerticalContextType,
  VerticalSource,
  PublicProductConfigResponse,
} from '../types/vertical';
import {
  DEFAULT_VERTICAL,
  VERTICAL_CONFIGS,
  isVerticalKey,
  getVerticalConfig,
} from '../config/verticals';

export interface LocationParts {
  search?: string;
  pathname?: string;
  hostname?: string;
}

/**
 * Pure function to detect the active vertical and its detection source.
 * Order of Precedence:
 * 1. URL Query parameter (?vertical=...)
 * 2. URL Path prefix (/healthcare, /legal, /general)
 * 3. Hostname subdomain (healthcare.*, legal.*)
 * 4. Default ('general')
 */
export function detectVerticalFromLocation(loc?: LocationParts): {
  vertical: VerticalKey;
  source: VerticalSource;
} {
  const search = loc?.search ?? (typeof window !== 'undefined' ? window.location.search : '');
  const pathname = loc?.pathname ?? (typeof window !== 'undefined' ? window.location.pathname : '');
  const hostname = loc?.hostname ?? (typeof window !== 'undefined' ? window.location.hostname : '');

  // 1. Query parameter (?vertical=healthcare | legal | general)
  if (search) {
    const params = new URLSearchParams(search);
    const queryVertical = params.get('vertical')?.toLowerCase();
    if (isVerticalKey(queryVertical)) {
      return { vertical: queryVertical, source: 'query' };
    }
  }

  // 2. Pathname prefix (/healthcare, /legal, /general)
  if (pathname) {
    const normalizedPath = pathname.toLowerCase();
    if (normalizedPath === '/healthcare' || normalizedPath.startsWith('/healthcare/')) {
      return { vertical: 'healthcare', source: 'path' };
    }
    if (normalizedPath === '/legal' || normalizedPath.startsWith('/legal/')) {
      return { vertical: 'legal', source: 'path' };
    }
    if (normalizedPath === '/general' || normalizedPath.startsWith('/general/')) {
      return { vertical: 'general', source: 'path' };
    }
  }

  // 3. Hostname subdomain (healthcare.staging.resilai.org, legal.staging.resilai.org, etc.)
  if (hostname) {
    const lowerHost = hostname.toLowerCase();
    const firstSubdomain = lowerHost.split('.')[0];

    if (firstSubdomain === 'healthcare' || lowerHost.startsWith('healthcare-')) {
      return { vertical: 'healthcare', source: 'subdomain' };
    }
    if (firstSubdomain === 'legal' || lowerHost.startsWith('legal-')) {
      return { vertical: 'legal', source: 'subdomain' };
    }
    if (firstSubdomain === 'general' || lowerHost.startsWith('general-')) {
      return { vertical: 'general', source: 'subdomain' };
    }
  }

  // 4. Default fallback
  return { vertical: DEFAULT_VERTICAL, source: 'default' };
}

const VerticalContext = createContext<VerticalContextType | undefined>(undefined);

export interface VerticalProviderProps {
  children: React.ReactNode;
  initialVertical?: VerticalKey;
}

export const VerticalProvider: React.FC<VerticalProviderProps> = ({
  children,
  initialVertical,
}) => {
  const initialDetection = useMemo(() => {
    if (initialVertical && isVerticalKey(initialVertical)) {
      return { vertical: initialVertical, source: 'default' as VerticalSource };
    }
    return detectVerticalFromLocation();
  }, [initialVertical]);

  const [currentVertical, setCurrentVerticalState] = useState<VerticalKey>(initialDetection.vertical);
  const [source, setSource] = useState<VerticalSource>(initialDetection.source);
  const [config, setConfig] = useState<VerticalConfig>(() => getVerticalConfig(initialDetection.vertical));
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const setVertical = useCallback((newVertical: VerticalKey) => {
    if (!isVerticalKey(newVertical)) return;
    setCurrentVerticalState(newVertical);
    setConfig(getVerticalConfig(newVertical));
  }, []);

  // Sync state if initialVertical prop changes
  const prevInitialVerticalRef = React.useRef(initialVertical);
  useEffect(() => {
    if (initialVertical && isVerticalKey(initialVertical) && prevInitialVerticalRef.current !== initialVertical) {
      prevInitialVerticalRef.current = initialVertical;
      setCurrentVerticalState(initialVertical);
      setConfig(getVerticalConfig(initialVertical));
    }
  }, [initialVertical]);

  // Listen for browser popstate changes to update vertical dynamically on navigation
  useEffect(() => {
    const handleLocationChange = () => {
      const detected = detectVerticalFromLocation();
      if (detected.vertical !== currentVertical) {
        setCurrentVerticalState(detected.vertical);
        setSource(detected.source);
        setConfig(getVerticalConfig(detected.vertical));
      }
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('popstate', handleLocationChange);
      return () => {
        window.removeEventListener('popstate', handleLocationChange);
      };
    }
  }, [currentVertical]);

  // Optional background fetch to enrich config from GET /api/public/product-config
  useEffect(() => {
    let isCancelled = false;

    const fetchConfig = async () => {
      try {
        setIsLoading(true);
        const res = await fetch(`/api/public/product-config?vertical=${currentVertical}`, {
          headers: {
            'X-ResilAI-Vertical': currentVertical,
          },
        });
        if (!res.ok) {
          // If public API returns non-200, retain static fallback
          return;
        }
        const data: PublicProductConfigResponse = await res.json();
        if (!isCancelled && data && data.vertical_key === currentVertical) {
          setConfig((prev) => ({
            ...prev,
            displayName: data.display_name || prev.displayName,
            industryLabel: data.industry_label || prev.industryLabel,
            headline: data.headline || prev.headline,
            coreQuestion: data.core_question || prev.coreQuestion,
            focusAreas: Array.isArray(data.focus_areas) && data.focus_areas.length > 0 ? data.focus_areas : prev.focusAreas,
            demoOrgId: data.demo_org_id || prev.demoOrgId,
            demoOrgName: data.demo_org_name || prev.demoOrgName,
          }));
        }
      } catch {
        // Network or offline: seamlessly rely on synchronous static fallback
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchConfig();

    return () => {
      isCancelled = true;
    };
  }, [currentVertical]);

  const value = useMemo<VerticalContextType>(
    () => ({
      currentVertical,
      config,
      setVertical,
      isLoading,
      source,
    }),
    [currentVertical, config, setVertical, isLoading, source]
  );

  return <VerticalContext.Provider value={value}>{children}</VerticalContext.Provider>;
};

export function useVertical(): VerticalContextType {
  const context = useContext(VerticalContext);
  if (!context) {
    throw new Error('useVertical must be used within a VerticalProvider');
  }
  return context;
}
