import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import type { ReviewQueueItem } from '../types';

export function ReviewPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [unbalancedOnly, setUnbalancedOnly] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) return;
    let active = true;
    api.reviewQueue(token, { query, status: status || undefined, balanced: unbalancedOnly ? false : undefined })
      .then((data) => { if (active) { setItems(data); setError(''); } })
      .catch((err: unknown) => { if (active) setError(err instanceof Error ? err.message : 'Could not load the review queue.'); });
    return () => { active = false; };
  }, [token, query, status, unbalancedOnly]);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-500">Council Finance Admin Hub</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-900">Submission oversight</h1>
          <p className="mt-2 text-sm text-slate-600">Review incoming reports, find flagged budget balances, and track dispositions.</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">{items.length} matching reports</div>
      </header>

      <section className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-[1fr_220px_auto]">
        <label className="text-sm font-medium text-slate-700">Search
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Initiative, organization, cycle, or ID" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal" />
        </label>
        <label className="text-sm font-medium text-slate-700">Status
          <select value={status} onChange={(event) => setStatus(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-normal">
            <option value="">All submitted reports</option>
            {['SUBMITTED', 'IN_REVIEW', 'REVISION_REQUESTED', 'APPROVED', 'REJECTED'].map((value) => <option key={value}>{value}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2 self-end pb-2 text-sm text-slate-700">
          <input type="checkbox" checked={unbalancedOnly} onChange={(event) => setUnbalancedOnly(event.target.checked)} className="h-4 w-4 rounded border-slate-300" />
          Unbalanced only
        </label>
      </section>

      {error ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="grid grid-cols-[1.1fr_1.2fr_1fr_150px_120px_110px] gap-3 border-b border-slate-200 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
          <span>Initiative</span><span>Organization</span><span>Cycle</span><span>Status</span><span>Budget</span><span>Balance</span>
        </div>
        {items.length ? items.map((item) => (
          <Link key={item.submission_id} to={`/review/${encodeURIComponent(item.submission_id)}`} className="grid grid-cols-[1.1fr_1.2fr_1fr_150px_120px_110px] gap-3 border-b border-slate-100 px-5 py-4 text-sm text-slate-700 last:border-0 hover:bg-slate-50">
            <span className="font-medium text-slate-900">{item.initiative_name}</span><span>{item.organization_name}</span><span>{item.cycle_name}</span><span>{item.status}</span><span>${item.total_budget}</span>
            <span className={item.is_balanced ? 'text-emerald-700' : 'font-semibold text-amber-700'}>{item.is_balanced ? 'Balanced' : 'Flagged'}</span>
          </Link>
        )) : <p className="px-5 py-10 text-center text-sm text-slate-500">No submitted reports match these filters.</p>}
      </section>
      <p className="text-xs text-slate-500">Form administration, fiscal-year rollover, exports, notifications, and user provisioning are separate modules and are not available in this local demo increment.</p>
    </div>
  );
}
