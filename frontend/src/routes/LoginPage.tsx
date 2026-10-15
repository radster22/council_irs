import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const COUNCIL_PORTAL_ROLES = ['COUNCIL_ADMIN', 'COUNCIL_REVIEWER', 'VIEW_ONLY'];

export function LoginPage() {
  const navigate = useNavigate();
  const { login, logout } = useAuth();
  const [persona, setPersona] = useState<'submitter' | 'council'>('submitter');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting) return;

    setError('');
    setSubmitting(true);

    try {
      const currentUser = await login(email, password);
      const canAccessSelectedPortal = persona === 'submitter'
        ? currentUser.role === 'EXTERNAL_SUBMITTER'
        : COUNCIL_PORTAL_ROLES.includes(currentUser.role);

      if (!canAccessSelectedPortal) {
        logout();
        setError('Access denied. Your account role does not permit access to the selected portal.');
        return;
      }

      navigate(persona === 'submitter' ? '/submit' : '/review', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
        <div className="mb-6 text-center">
          <div className="text-xs uppercase tracking-[0.28em] text-brand-500">Council Portal</div>
          <h1 className="page-title">Sign in</h1>
        </div>

        <div className="mb-5">
          <p className="mb-2 text-sm font-medium text-slate-700">Choose a portal</p>
          <div className="grid grid-cols-2 gap-2">
            {([
              ['submitter', 'External Submitter'],
              ['council', 'Council Finance'],
            ] as const).map(([value, label]) => (
              <button key={value} type="button" onClick={() => setPersona(value)} aria-pressed={persona === value} disabled={submitting}
                className={`rounded-lg border px-3 py-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-60 ${persona === value ? 'border-brand-500 bg-brand-50 text-brand-800' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
                {label}
              </button>
            ))}
          </div>
          <p className="mt-2 text-xs text-slate-500">Choose the portal assigned to your account. Access is denied if your account role does not match.</p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              disabled={submitting}
              onChange={(event) => setEmail(event.target.value)}
              className="input outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              disabled={submitting}
              onChange={(event) => setPassword(event.target.value)}
              className="input outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
              required
            />
          </div>

          {error ? (
            <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-brand-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
          Sign in with an active account provisioned in the connected MySQL database.
        </div>
      </div>
    </div>
  );
}
