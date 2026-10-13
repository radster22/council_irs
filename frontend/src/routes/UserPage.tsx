import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import type { AdminUser, Role } from '../types';

type OrganizationOption = { id: string; ein: string; legal_name: string };
const roles: Role[] = ['COUNCIL_ADMIN', 'COUNCIL_REVIEWER', 'EXTERNAL_SUBMITTER', 'VIEW_ONLY'];

export function UserPage() {
  const { token, user: currentUser } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [organizations, setOrganizations] = useState<OrganizationOption[]>([]);
  const [selected, setSelected] = useState<Record<string, string[]>>({});
  const [passwords, setPasswords] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const refresh = async () => {
    if (!token) return;
    const [accounts, orgs] = await Promise.all([api.listUsers(token), api.listOrganizations(token)]);
    setUsers(accounts);
    setOrganizations(orgs);
    setSelected((previous) => Object.fromEntries(accounts.map((account) => [account.id,
      previous[account.id] ?? account.organization_ids])));
  };

  useEffect(() => {
    refresh().catch((err: unknown) => setError(err instanceof Error ? err.message : 'Could not load account data.'))
      .finally(() => setLoading(false));
  }, [token]);

  const updateAccount = async (account: AdminUser, event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) return;
    const form = new FormData(event.currentTarget);
    setBusyId(account.id); setError(''); setMessage('');
    try {
      await api.updateUser(account.id, {
        role: String(form.get('role')),
        is_active: form.get('is_active') === 'on',
        organization_eins: organizations.filter((org) => (selected[account.id] ?? []).includes(org.id)).map((org) => org.ein),
      }, token);
      setMessage(`Updated ${account.email}.`);
      await refresh();
    } catch (err) { setError(err instanceof Error ? err.message : 'Account update failed.'); }
    finally { setBusyId(''); }
  };

  const resetPassword = async (account: AdminUser) => {
    if (!token) return;
    const password = passwords[account.id] ?? '';
    setBusyId(account.id); setError(''); setMessage('');
    try {
      await api.resetUserPassword(account.id, password, token);
      setPasswords((current) => ({ ...current, [account.id]: '' }));
      setMessage(`Password reset for ${account.email}.`);
    } catch (err) { setError(err instanceof Error ? err.message : 'Password reset failed.'); }
    finally { setBusyId(''); }
  };

  const toggleOrganization = (userId: string, organizationId: string) => {
    setSelected((current) => {
      const values = current[userId] ?? [];
      return { ...current, [userId]: values.includes(organizationId)
        ? values.filter((id) => id !== organizationId) : [...values, organizationId] };
    });
  };

  return <div className="space-y-6">
    <header><p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-500">Administration</p><h1 className="mt-2 text-3xl font-bold text-slate-900">User accounts</h1><p className="mt-2 text-sm text-slate-600">Manage roles, active access, organization scope and password resets. External users need at least one organization.</p></header>
    {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
    {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}
    {loading ? <p className="text-sm text-slate-500">Loading accounts…</p> : users.length ? users.map((account) => <article key={account.id} className="rounded-2xl border border-slate-200 bg-white p-5">
      <div><h2 className="font-semibold text-slate-900">{account.full_name}</h2><p className="text-sm text-slate-500">{account.email}</p></div>
      <form onSubmit={(event) => void updateAccount(account, event)} className="mt-4 grid gap-4 lg:grid-cols-[1fr_1fr_auto]">
        <label className="text-sm font-medium">Role<select name="role" defaultValue={account.role} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2">{roles.map((role) => <option key={role}>{role}</option>)}</select></label>
        <label className="flex items-center gap-2 self-end pb-2 text-sm"><input name="is_active" type="checkbox" defaultChecked={account.is_active} /> Active account</label>
        <button disabled={busyId === account.id} className="self-end rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{busyId === account.id ? 'Saving…' : 'Save account'}</button>
        <fieldset className="lg:col-span-3"><legend className="text-sm font-semibold text-slate-700">Organization access by EIN</legend><div className="mt-2 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">{organizations.map((org) => <label key={org.id} className="flex items-center gap-2 rounded-lg bg-slate-50 p-2 text-sm"><input type="checkbox" checked={(selected[account.id] ?? []).includes(org.id)} onChange={() => toggleOrganization(account.id, org.id)} />{org.legal_name} <span className="text-xs text-slate-500">{org.ein}</span></label>)}</div>{!organizations.length ? <p className="text-sm text-slate-500">No active organizations are available.</p> : null}</fieldset>
      </form>
      <div className="mt-4 flex flex-col gap-2 border-t border-slate-100 pt-4 sm:flex-row sm:items-end">
        <label className="block flex-1 text-sm font-medium">Set new password<input type="password" minLength={12} maxLength={72} autoComplete="new-password" value={passwords[account.id] ?? ''} onChange={(event) => setPasswords((current) => ({ ...current, [account.id]: event.target.value }))} placeholder="At least 12 characters" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
        <button type="button" disabled={busyId === account.id || (passwords[account.id] ?? '').length < 12} onClick={() => void resetPassword(account)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50">Reset password</button>
      </div>
      {currentUser?.id === account.id ? <p className="mt-2 text-xs text-slate-500">Your own administrator role and active status are protected from lockout.</p> : null}
    </article>) : <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">No user accounts are present in the database.</p>}
  </div>;
}
