import {
  resolveSchema,
  typeLabel,
  type OpenApiDocument,
  type SchemaObject,
} from './openapi';

const MAX_DEPTH = 4;

interface Shape {
  properties: Record<string, SchemaObject>;
  required: Set<string>;
  names: string[];
  circular: boolean;
}

/** The fields of an object schema (or of the objects inside a list), if it has any. */
function shapeOf(
  document: OpenApiDocument | null,
  schema: SchemaObject | undefined,
  seen: ReadonlySet<string>,
): Shape | null {
  const resolved = resolveSchema(document, schema, seen);
  if (resolved.circular) return { properties: {}, required: new Set(), names: resolved.names, circular: true };
  const s = resolved.schema;
  const nextSeen = new Set([...seen, ...resolved.names]);

  if (s.items) {
    const inner = shapeOf(document, s.items, nextSeen);
    return inner ? { ...inner, names: [...resolved.names, ...inner.names] } : null;
  }
  const variants = s.anyOf ?? s.oneOf;
  if (variants && variants.length > 0) {
    for (const variant of variants) {
      const inner = shapeOf(document, variant, nextSeen);
      if (inner && (inner.circular || Object.keys(inner.properties).length > 0)) {
        return { ...inner, names: [...resolved.names, ...inner.names] };
      }
    }
    return null;
  }

  const properties: Record<string, SchemaObject> = { ...(s.properties ?? {}) };
  const required = new Set<string>(s.required ?? []);
  const names = [...resolved.names];
  for (const part of s.allOf ?? []) {
    const inner = shapeOf(document, part, nextSeen);
    if (!inner) continue;
    Object.assign(properties, inner.properties);
    inner.required.forEach((name) => required.add(name));
    names.push(...inner.names);
  }
  if (Object.keys(properties).length === 0) return null;
  return { properties, required, names, circular: false };
}

interface SchemaFieldsProps {
  document: OpenApiDocument | null;
  schema: SchemaObject | undefined;
  /** Reference names already open above this point (cycle guard). */
  seen?: ReadonlySet<string>;
  depth?: number;
}

/** A plain list of the fields in a schema, with nested objects folded away. */
export function SchemaFields({ document, schema, seen = new Set(), depth = 0 }: SchemaFieldsProps) {
  const shape = shapeOf(document, schema, seen);

  if (!shape) {
    return (
      <p className="text-xs text-on-surface-variant">
        Type: <span className="font-semibold text-on-surface">{typeLabel(document, schema, seen)}</span>
      </p>
    );
  }
  if (shape.circular) {
    return (
      <p className="text-xs text-on-surface-variant">
        Same fields as {shape.names[shape.names.length - 1] ?? 'the item above'} (it contains itself).
      </p>
    );
  }

  const nextSeen = new Set([...seen, ...shape.names]);

  return (
    <ul className="space-y-1.5">
      {Object.entries(shape.properties).map(([name, property]) => {
        const nested = depth < MAX_DEPTH ? shapeOf(document, property, nextSeen) : null;
        const description = resolveSchema(document, property, nextSeen).schema.description ?? property.description;
        return (
          <li key={name} className="rounded-lg border border-outline-variant bg-surface-container px-2.5 py-1.5">
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
              <code className="break-all font-mono text-xs font-bold text-on-surface">{name}</code>
              <span className="text-[11px] text-on-surface-variant">{typeLabel(document, property, nextSeen)}</span>
              {shape.required.has(name) && (
                <span className="rounded border border-outline-variant px-1 text-[10px] font-bold uppercase tracking-wide text-on-surface">
                  Required
                </span>
              )}
            </div>
            {description && <p className="mt-0.5 text-[11px] text-on-surface-variant">{description}</p>}
            {nested && (
              <details className="mt-1">
                <summary className="cursor-pointer text-[11px] font-semibold text-on-surface-variant hover:text-on-surface">
                  Show fields
                </summary>
                <div className="mt-1.5 border-l border-outline-variant pl-2.5">
                  <SchemaFields document={document} schema={property} seen={nextSeen} depth={depth + 1} />
                </div>
              </details>
            )}
          </li>
        );
      })}
    </ul>
  );
}

export default SchemaFields;
