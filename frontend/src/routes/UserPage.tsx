import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import type { AdminUser } from '../types';

export function UserPage() {
  const { token } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) return;
    let active = true;
    api.listUsers(token)
      .then((data) => { if (active) setUsers(data); })
      .catch((err: unknown) => { if (active) setError(err instanceof Error ? err.message : 'Could not load accounts.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [token]);

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-500">Administration</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">User accounts</h1>
        <p className="mt-2 text-sm text-slate-600">Account and organization assignments loaded from the reporting database.</p>
      </header>
      {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="grid grid-cols-[1fr_1.2fr_180px_100px_1.2fr] gap-3 border-b border-slate-200 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
          <span>Name</span><span>Email</span><span>Role</span><span>State</span><span>Organization IDs</span>
        </div>
        {loading ? <p className="px-5 py-8 text-sm text-slate-500">Loading accounts…</p> : users.length ? users.map((account) => (
          <div key={account.id} className="grid grid-cols-[1fr_1.2fr_180px_100px_1.2fr] gap-3 border-b border-slate-100 px-5 py-4 text-sm last:border-0">
            <span className="font-medium text-slate-900">{account.full_name}</span><span>{account.email}</span><span>{account.role}</span>
            <span className={account.is_active ? 'text-emerald-700' : 'text-slate-500'}>{account.is_active ? 'Active' : 'Inactive'}</span>
            <span className="break-all text-slate-600">{account.organization_ids.join(', ') || '—'}</span>
          </div>
        )) : !loading ? <p className="px-5 py-8 text-sm text-slate-500">No user accounts are present in the database.</p> : null}
      </section>
    </div>
  );
}
