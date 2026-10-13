import { useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';

export function RolloverPage() {
  const { token } = useAuth();
  const [source, setSource] = useState('');
  const [destination, setDestination] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<{ initiatives_created: number; cycles_created: number; templates_created: number; assignments_created: number } | null>(null);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!token) return;
    setBusy(true); setError(''); setResult(null);
    try { setResult(await api.rollover(Number(source), Number(destination), token)); }
    catch (err) { setError(err instanceof Error ? err.message : 'Annual rollover failed.'); }
    finally { setBusy(false); }
  };
  return <div className="mx-auto max-w-2xl space-y-6"><header><p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-500">Administration</p><h1 className="mt-2 text-3xl font-bold">Annual initiative rollover</h1><p className="mt-2 text-sm text-slate-600">Creates next-year initiative records, future reporting cycles, copied eligibility and new versioned form records. Source year data stays intact; each new initiative links to its predecessor.</p></header><form onSubmit={submit} className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6"><label className="block text-sm font-medium">Source fiscal year<input required type="number" min="2000" max="2200" value={source} onChange={(e) => setSource(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label><label className="block text-sm font-medium">Destination fiscal year<input required type="number" min={Number(source || 2000) + 1} max="2201" value={destination} onChange={(e) => setDestination(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label><button disabled={busy || !source || !destination || Number(destination) <= Number(source)} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{busy ? 'Creating rollover…' : 'Create annual rollover'}</button></form>{error ? <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}{result ? <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900"><h2 className="font-semibold">Rollover created</h2><p>Initiatives: {result.initiatives_created} · Cycles: {result.cycles_created} · Templates: {result.templates_created} · Assignments: {result.assignments_created}</p></section> : null}</div>;
}
