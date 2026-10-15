import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api, saveBlob } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import type { ReviewQueueItem } from '../types';

function toCents(value: string): bigint {
  const [whole, fraction = ''] = value.split('.');
  if (!/^\d+$/.test(whole) || !/^\d{0,2}$/.test(fraction)) return 0n;
  return BigInt(whole) * 100n + BigInt(fraction.padEnd(2, '0'));
}

function barWidth(value: string, maximum: string): number {
  const max = toCents(maximum);
  if (max === 0n) return 0;
  return Number((toCents(value) * 10000n) / max) / 100;
}

export function ReviewPage() {
  const { token, user } = useAuth();
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [unbalancedOnly, setUnbalancedOnly] = useState(false);
  const [ein, setEin] = useState('');
  const [borough, setBorough] = useState('');
  const [fiscalYear, setFiscalYear] = useState('');
  const [initiativeFilter, setInitiativeFilter] = useState('');
  const [cycleFilter, setCycleFilter] = useState('');

  const { data: items = [], error } = useQuery<ReviewQueueItem[], Error>({
    queryKey: ['review-queue', token, query, status, unbalancedOnly, ein, borough, fiscalYear, initiativeFilter, cycleFilter],
    enabled: Boolean(token),
    queryFn: () => {
      if (!token) throw new Error('Authentication is required.');
      return api.reviewQueue(token, {
        query,
        status: status || undefined,
        balanced: unbalancedOnly ? false : undefined,
        ein: ein || undefined,
        borough: borough || undefined,
        fiscal_year: fiscalYear ? Number(fiscalYear) : undefined,
        initiative: initiativeFilter || undefined,
        cycle: cycleFilter || undefined,
      });
    },
  });
  const { data: analytics } = useQuery({ queryKey: ['admin-analytics', token], enabled: Boolean(token), queryFn: () => api.getAnalytics(token!) });
  const { data: obligations = [] } = useQuery({ queryKey: ['open-obligations', token], enabled: Boolean(token), queryFn: () => api.getOpenObligations(token!) });

  const downloadExport = async (kind: 'csv' | 'xlsx') => {
    if (!token) return;
    try {
      saveBlob(await api.downloadExport(kind, token), kind === 'csv' ? 'council-reporting-csv.zip' : 'council-reporting.xlsx');
    } catch (err) {
      window.alert(err instanceof Error ? err.message : 'Export failed.');
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Council Finance Admin Hub</p>
          <h1 className="page-title">Submission oversight</h1>
          <p className="page-lead">Review incoming reports, find flagged budget balances, and track dispositions.</p>
        </div>
        <div className="no-print flex flex-wrap gap-2">
          <button onClick={() => downloadExport('xlsx')} className="btn-secondary px-3">Download Excel</button>
          <button onClick={() => downloadExport('csv')} className="btn-secondary px-3">Download CSV bundle</button>
          {user?.role === 'COUNCIL_ADMIN' ? <Link to="/admin/initiatives" className="btn-secondary px-3">Initiatives & forms</Link> : null}
          {user?.role === 'COUNCIL_ADMIN' ? <Link to="/admin/rollover" className="rounded-lg border border-brand-300 bg-white px-3 py-2 text-sm font-semibold text-brand-700">Annual rollover</Link> : null}
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-4">
        {[
          ['Submitted reports', analytics?.submitted_count ?? 0],
          ['Reported budget', `$${analytics?.reported_budget ?? '0.00'}`],
          ['Allocated budget', `$${analytics?.allocated_budget ?? '0.00'}`],
          ['Balanced reports', analytics?.balanced_count ?? 0],
        ].map(([label, value]) => <div key={String(label)} className="rounded-xl border border-slate-200 bg-white p-4"><div className="text-xs uppercase tracking-wide text-slate-500">{label}</div><div className="mt-1 text-xl font-bold text-slate-900">{value}</div></div>)}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="card p-5"><h2 className="font-semibold text-slate-900">Submission status</h2><div className="mt-4 space-y-3">
          {Object.entries(analytics?.status_counts ?? {}).map(([label, value]) => { const maximum = Math.max(1, ...Object.values(analytics?.status_counts ?? {})); return <div key={label}><div className="mb-1 flex justify-between text-sm"><span>{label}</span><span>{value}</span></div><div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-brand-500" style={{ width: `${Math.max(3, (value / maximum) * 100)}%` }} /></div></div>; })}
          {!Object.keys(analytics?.status_counts ?? {}).length ? <p className="text-sm text-slate-500">No submissions are recorded.</p> : null}
        </div></div>
        <div className="card p-5"><h2 className="font-semibold text-slate-900">Reported budget by borough</h2><div className="mt-4 space-y-3">
          {(analytics?.borough_totals ?? []).map((item) => { const values = analytics?.borough_totals ?? []; const maximum = values.reduce((current, entry) => toCents(entry.total) > toCents(current) ? entry.total : current, '0.00'); return <div key={item.borough}><div className="mb-1 flex justify-between text-sm"><span>{item.borough}</span><span>${item.total}</span></div><div className="h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-emerald-600" style={{ width: `${Math.max(3, barWidth(item.total, maximum))}%` }} /></div></div>; })}
          {!analytics?.borough_totals.length ? <p className="text-sm text-slate-500">No borough totals are available.</p> : null}
        </div></div>
      </section>

      <section className="card p-5">
        <h2 className="font-semibold text-slate-900">Open reporting obligations</h2>
        <p className="mt-1 text-sm text-slate-600">Eligible organization and cycle assignments without a started report.</p>
        <div className="mt-3 overflow-x-auto"><table className="w-full min-w-[700px] text-left text-sm"><thead><tr className="border-b text-xs uppercase text-slate-500"><th className="py-2">Initiative</th><th>Organization</th><th>Cycle</th><th>Due</th><th>Awarded</th></tr></thead><tbody>
          {obligations.map((item) => <tr key={`${item.initiative_id}-${item.organization_id}-${item.cycle_id}`} className="border-b border-slate-100"><td className="py-2">{item.initiative_name}</td><td>{item.organization_name}</td><td>{item.cycle_name}</td><td>{item.due_date}{item.is_overdue ? <span className="ml-2 inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800">Overdue</span> : null}</td><td>${item.awarded_amount}</td></tr>)}
        </tbody></table>{!obligations.length ? <p className="py-4 text-sm text-slate-500">No open unstarted obligations.</p> : null}</div>
      </section>

      <section className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-2 xl:grid-cols-4">
        <label className="field-label">Search
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Initiative, organization, cycle, or ID" className="input mt-1 font-normal" />
        </label>
        <label className="field-label">Organization EIN
          <input value={ein} onChange={(event) => setEin(event.target.value)} placeholder="Search EIN" className="input mt-1 font-normal" />
        </label>
        <label className="field-label">Borough
          <select value={borough} onChange={(event) => setBorough(event.target.value)} className="input mt-1 font-normal">
            <option value="">All boroughs</option>
            {['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island', 'Citywide'].map((value) => <option key={value}>{value}</option>)}
          </select>
        </label>
        <label className="field-label">Fiscal year
          <input type="number" min="2000" max="2200" value={fiscalYear} onChange={(event) => setFiscalYear(event.target.value)} placeholder="All years" className="input mt-1 font-normal" />
        </label>
        <label className="field-label">Initiative
          <input value={initiativeFilter} onChange={(event) => setInitiativeFilter(event.target.value)} placeholder="Initiative name" className="input mt-1 font-normal" />
        </label>
        <label className="field-label">Reporting cycle
          <input value={cycleFilter} onChange={(event) => setCycleFilter(event.target.value)} placeholder="Cycle name" className="input mt-1 font-normal" />
        </label>
        <label className="field-label">Status
          <select value={status} onChange={(event) => setStatus(event.target.value)} className="input mt-1 font-normal">
            <option value="">All reports</option>
            {['DRAFT', 'SUBMITTED', 'IN_REVIEW', 'REVISION_REQUESTED', 'APPROVED', 'REJECTED'].map((value) => <option key={value}>{value}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2 self-end pb-2 text-sm text-slate-700">
          <input type="checkbox" checked={unbalancedOnly} onChange={(event) => setUnbalancedOnly(event.target.checked)} className="h-4 w-4 rounded border-slate-300" />
          Unbalanced only
        </label>
      </section>

      {error ? <div className="alert-error">{error.message}</div> : null}
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="grid grid-cols-[1.1fr_1.2fr_1fr_150px_120px_110px] gap-3 border-b border-slate-200 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
          <span>Initiative</span><span>Organization</span><span>Cycle</span><span>Status</span><span>Budget</span><span>Balance</span>
        </div>
        {items.length ? items.map((item) => (
          <Link key={item.submission_id} to={`/review/${encodeURIComponent(item.submission_id)}`} className="grid grid-cols-[1.1fr_1.2fr_1fr_150px_120px_110px] gap-3 border-b border-slate-100 px-5 py-4 text-sm text-slate-700 last:border-0 hover:bg-slate-50">
            <span className="font-medium text-slate-900">{item.initiative_name}<span className="ml-1 text-xs font-normal text-slate-500">FY{item.fiscal_year}</span></span><span>{item.organization_name}<span className="block text-xs text-slate-500">{item.organization_ein}{item.borough ? ` · ${item.borough}` : ''}</span></span><span>{item.cycle_name}</span><span>{item.status}{item.is_incomplete ? ' · Incomplete' : ''}</span><span>${item.total_budget}</span>
            <span className={item.is_balanced ? 'text-emerald-700' : 'font-semibold text-amber-700'}>{item.is_balanced ? 'Balanced' : 'Flagged'}</span>
            {item.validation_errors.length ? <span className="col-span-6 -mt-2 text-xs text-amber-800">{item.validation_errors.join(' ')}</span> : null}
          </Link>
        )) : <p className="px-5 py-10 text-center text-sm text-slate-500">No reports match these filters.</p>}
      </section>
    </div>
  );
}
