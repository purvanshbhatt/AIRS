import { Suspense, lazy } from 'react';
import { Loader2 } from 'lucide-react';
import type { ApiExplorerProps } from './ApiExplorer';

export type { ApiExplorerProps } from './ApiExplorer';

// The explorer is only needed on the pages that show it, so it is split into
// its own chunk. Import it from here (not from './ApiExplorer') to keep it out
// of the main bundle.
const LazyExplorer = lazy(() => import('./ApiExplorer'));

/**
 * The in-app API explorer, loaded on demand.
 *
 *   import { ApiExplorerLazy } from '../components/apidocs';
 *   <ApiExplorerLazy />
 */
export function ApiExplorerLazy(props: ApiExplorerProps) {
  return (
    <Suspense
      fallback={
        <div
          className={`rounded-2xl border border-outline-variant bg-surface-container-low p-4 text-sm text-on-surface-variant sm:p-5 ${props.className ?? ''}`}
          aria-busy="true"
        >
          <span className="inline-flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            Loading the API explorer
          </span>
        </div>
      }
    >
      <LazyExplorer {...props} />
    </Suspense>
  );
}

export default ApiExplorerLazy;
