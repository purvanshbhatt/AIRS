import { useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { SEOHead } from './SEOHead';
import { alternatesFor, canonicalFor, findPublicRoute, schemaFor } from '../../seo';

/**
 * Sets the title, description, canonical link and structured data for public
 * pages that do not set their own. Without it those pages keep the tags of
 * whichever page the visitor opened first.
 */
export function RouteSEO() {
  const { pathname } = useLocation();
  const route = findPublicRoute(pathname);
  const managed = route && route.managed ? route : undefined;
  const schema = useMemo(() => (managed ? schemaFor(managed) : undefined), [managed]);
  const alternates = useMemo(() => alternatesFor(managed), [managed]);

  if (!managed) return null;

  return (
    <SEOHead
      title={managed.title}
      description={managed.description}
      keywords={managed.keywords}
      canonicalUrl={canonicalFor(managed.path)}
      schema={schema}
      alternates={alternates}
    />
  );
}

export default RouteSEO;
