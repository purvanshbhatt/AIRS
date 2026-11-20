import { describe, it, expect } from 'vitest';

/**
 * Everything under src/ is shipped to the browser, so anything written here is
 * public. The sign-in page once carried a "quick sign in" button with a test
 * account's email and password in the code, and it went to production. These
 * checks read the source so that cannot come back unnoticed.
 */

const sources = import.meta.glob('../**/*.{ts,tsx}', { query: '?raw', import: 'default', eager: true }) as Record<
  string,
  string
>;

const shipped = Object.entries(sources).filter(([path]) => !path.includes('/test/'));

describe('no sign-in credentials in page code', () => {
  it('reads the application source', () => {
    expect(shipped.length).toBeGreaterThan(50);
    expect(shipped.some(([path]) => path.endsWith('/pages/Login.tsx'))).toBe(true);
  });

  it('never calls a sign-in function with a password written in the code', () => {
    // signInWithEmail('someone@example.com', 'a-literal-password')
    const literalSignIn = /signInWith(?:Email|EmailAndPassword)\s*\(\s*(?:\w+\s*,\s*)?['"`][^'"`]+['"`]\s*,\s*['"`][^'"`]+['"`]/;
    const offenders = shipped.filter(([, text]) => literalSignIn.test(text)).map(([path]) => path);

    expect(offenders).toEqual([]);
  });

  it('never fills the password field from a value written in the code', () => {
    const literalPassword = /setPassword\s*\(\s*['"`][^'"`]+['"`]\s*\)/;
    const offenders = shipped.filter(([, text]) => literalPassword.test(text)).map(([path]) => path);

    expect(offenders).toEqual([]);
  });

  it('the sign-in page offers no built-in test account', () => {
    const [, login] = shipped.find(([path]) => path.endsWith('/pages/Login.tsx'))!;

    expect(login).not.toMatch(/staging-tester/i);
    expect(login).not.toMatch(/Quick sign in/i);
    expect(login).not.toMatch(/test account/i);
  });
});
