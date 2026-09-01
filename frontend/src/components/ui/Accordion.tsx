import { useState, createContext, useContext, HTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { ChevronDown } from 'lucide-react';

// Accordion Context
interface AccordionContextValue {
  openItems: Set<string>;
  toggle: (value: string) => void;
  type: 'single' | 'multiple';
}

const AccordionContext = createContext<AccordionContextValue | null>(null);

function useAccordionContext() {
  const context = useContext(AccordionContext);
  if (!context) {
    throw new Error('Accordion components must be used within an Accordion provider');
  }
  return context;
}

// Accordion Root
export interface AccordionProps extends HTMLAttributes<HTMLDivElement> {
  type?: 'single' | 'multiple';
  defaultValue?: string | string[];
  defaultOpen?: string | string[];
}

export function Accordion({
  type = 'multiple',
  defaultValue,
  defaultOpen,
  className,
  children,
  ...props
}: AccordionProps) {
  const initial = defaultOpen || defaultValue;
  const [openItems, setOpenItems] = useState<Set<string>>(() => {
    if (!initial) return new Set();
    return new Set(Array.isArray(initial) ? initial : [initial]);
  });

  const toggle = (value: string) => {
    setOpenItems((prev) => {
      const next = new Set(prev);
      if (next.has(value)) {
        next.delete(value);
      } else {
        if (type === 'single') {
          next.clear();
        }
        next.add(value);
      }
      return next;
    });
  };

  return (
    <AccordionContext.Provider value={{ openItems, toggle, type }}>
      <div className={clsx('divide-y divide-gray-200 dark:divide-slate-800', className)} {...props}>
        {children}
      </div>
    </AccordionContext.Provider>
  );
}

// Accordion Item Context
interface AccordionItemContextValue {
  value: string;
  isOpen: boolean;
}

const AccordionItemContext = createContext<AccordionItemContextValue | null>(null);

function useAccordionItemContext() {
  const context = useContext(AccordionItemContext);
  if (!context) {
    throw new Error('AccordionItem components must be used within an AccordionItem');
  }
  return context;
}

export interface AccordionItemProps extends HTMLAttributes<HTMLDivElement> {
  value?: string;
  id?: string;
}

export function AccordionItem({ value, id, className, children, ...props }: AccordionItemProps) {
  const { openItems } = useAccordionContext();
  const itemValue = value || id || '';
  const isOpen = openItems.has(itemValue);

  return (
    <AccordionItemContext.Provider value={{ value: itemValue, isOpen }}>
      <div className={clsx('py-2', className)} {...props}>
        {children}
      </div>
    </AccordionItemContext.Provider>
  );
}

// Accordion Trigger
export interface AccordionTriggerProps extends HTMLAttributes<HTMLButtonElement> {}

export function AccordionTrigger({ className, children, ...props }: AccordionTriggerProps) {
  const { toggle } = useAccordionContext();
  const { value, isOpen } = useAccordionItemContext();

  return (
    <button
      type="button"
      className={clsx(
        'flex w-full items-center justify-between py-3 text-left text-sm font-medium text-gray-900 dark:text-slate-100 hover:text-primary-600 dark:hover:text-primary-300 transition-colors',
        className
      )}
      onClick={() => toggle(value)}
      aria-expanded={isOpen}
      {...props}
    >
      {children}
      <ChevronDown
        className={clsx(
          'h-4 w-4 text-gray-500 dark:text-slate-400 transition-transform duration-200 flex-shrink-0',
          isOpen && 'rotate-180'
        )}
      />
    </button>
  );
}

// Accordion Content
export interface AccordionContentProps extends HTMLAttributes<HTMLDivElement> {}

export function AccordionContent({ className, children, ...props }: AccordionContentProps) {
  const { isOpen } = useAccordionItemContext();

  if (!isOpen) return null;

  return (
    <div className={clsx('pb-3 text-sm text-gray-600 dark:text-slate-300', className)} {...props}>
      {children}
    </div>
  );
}

export default Accordion;
