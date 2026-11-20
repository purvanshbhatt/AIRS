import { describe, it, expect } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { ToastProvider, useToast, type Toast } from '../components/ui/Toast';

/**
 * Regression: a "drift" toast (shown when a connector sync fails) had no icon
 * entry, so React rendered an undefined component and the whole app fell over
 * to the "Application Error" screen.
 */
const TYPES: NonNullable<Toast['type']>[] = ['ready', 'drift', 'success', 'warning', 'error', 'info'];

let add: ReturnType<typeof useToast>['addToast'];
function Grab() {
  add = useToast().addToast;
  return null;
}

describe('Toast', () => {
  it.each(TYPES)('renders a "%s" toast without crashing', (type) => {
    render(
      <ToastProvider>
        <Grab />
      </ToastProvider>,
    );
    act(() => add({ title: `Title ${type}`, message: 'Body', type, duration: 0 }));
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent(`Title ${type}`);
    expect(alert.querySelector('svg')).not.toBeNull();
  });

  it('falls back to the info look for an unknown type', () => {
    render(
      <ToastProvider>
        <Grab />
      </ToastProvider>,
    );
    act(() => add({ title: 'Odd', type: 'mystery' as Toast['type'], duration: 0 }));
    expect(screen.getByRole('alert')).toHaveTextContent('Odd');
  });
});
