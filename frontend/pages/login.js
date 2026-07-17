import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { api, auth } from '../services/api';

export default function Login() {
  const router = useRouter();
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ email: '', password: '', name: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (auth.token()) router.replace('/');
  }, [router]);

  const isRegister = mode === 'register';

  async function submit(e) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      const data = isRegister
        ? await api.register(form.email, form.password, form.name)
        : await api.login(form.email, form.password);
      auth.save(data.access_token, data.user);
      router.push('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const field =
    'w-full rounded-lg border border-line bg-paper-raised px-3 py-2.5 text-[15px] ' +
    'placeholder:text-ink-mute focus:border-ink focus:outline-none';

  return (
    <main className="flex min-h-screen items-center justify-center px-5 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold tracking-tight">TechMart</h1>
          <p className="mt-1 font-mono text-[11px] uppercase tracking-widest text-ink-mute">
            support console
          </p>
          <p className="mt-4 text-[15px] leading-relaxed text-ink-soft">
            Ask about orders, refunds, devices, or anything else. Your question is
            routed to the specialist who handles it.
          </p>
        </div>

        <form onSubmit={submit} className="space-y-3">
          {isRegister && (
            <div>
              <label htmlFor="name" className="mb-1.5 block text-[13px] font-medium">
                Name
              </label>
              <input
                id="name"
                className={field}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Priya Sharma"
                required
                autoComplete="name"
              />
            </div>
          )}

          <div>
            <label htmlFor="email" className="mb-1.5 block text-[13px] font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              className={field}
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1.5 block text-[13px] font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              className={field}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder={isRegister ? 'At least 8 characters' : ''}
              required
              minLength={isRegister ? 8 : undefined}
              autoComplete={isRegister ? 'new-password' : 'current-password'}
            />
          </div>

          {error && (
            // States what went wrong and what to do, in the interface's voice.
            <p
              role="alert"
              className="rounded-lg bg-complaint/8 px-3 py-2 text-[13px] text-complaint"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-ink px-4 py-2.5 text-[15px] font-medium
                       text-paper transition hover:bg-ink-soft disabled:opacity-50"
          >
            {busy ? 'Working…' : isRegister ? 'Create account' : 'Sign in'}
          </button>
        </form>

        <p className="mt-5 text-center text-[13px] text-ink-mute">
          {isRegister ? 'Already have an account?' : 'New here?'}{' '}
          <button
            onClick={() => {
              setMode(isRegister ? 'login' : 'register');
              setError('');
            }}
            className="font-medium text-ink underline underline-offset-2"
          >
            {isRegister ? 'Sign in' : 'Create an account'}
          </button>
        </p>
      </div>
    </main>
  );
}
