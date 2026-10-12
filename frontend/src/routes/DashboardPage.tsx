import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import type { AvailableReport, SubmissionListItem } from '../types';

export function DashboardPage() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [startingId, setStartingId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const {
    data: dashboardData,
    isPending: loading,
    error: dashboardError,
    refetch: loadDashboard,
  } = useQuery({
    queryKey: ['submitter-dashboard', token],
    enabled: Boolean(token),
    queryFn: async (): Promise<[SubmissionListItem[], AvailableReport[]]> => {
      if (!token) throw new Error('Authentication is required.');
      return Promise.all([
        api.listSubmissions(token),
        api.availableReports(token),
      ]);
    },
  });
  const submissions = dashboardData?.[0] ?? [];
  const available = dashboardData?.[1] ?? [];
  const loadError = error || (dashboardError instanceof Error ? dashboardError.message : '');
  const refreshDashboard = () => {
    setError('');
    void loadDashboard();
  };

  const startReport = async (report: AvailableReport) => {
    if (!token) return;
    const key = `${report.initiative_id}:${report.organization_id}:${report.cycle_id}`;
    setStartingId(key);
    setError('');
    try {
      const created = await api.createSubmission(report, token);
      navigate(`/reports/${encodeURIComponent(created.submission_id)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start the report.');
    } finally {
      setStartingId(null);
    }
  };

  const reportsInProgress = submissions.filter((item) => ['DRAFT', 'REVISION_REQUESTED'].includes(item.status)).length;
  const reportsSubmitted = submissions.filter((item) => ['SUBMITTED', 'IN_REVIEW', 'APPROVED', 'REJECTED'].includes(item.status)).length;
  const hasOrganizationAccess = (user?.organization_ids.length ?? 0) > 0;

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-500">Overview</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">Submitter dashboard</h1>
        <p className="mt-2 text-sm text-slate-600">Start a report assigned to your organization or continue work already saved.</p>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Organizations" value={String(user?.organization_ids.length ?? 0)} />
        <StatCard label="New report assignments" value={String(available.length)} />
        <StatCard label="Drafts / updates needed" value={String(reportsInProgress)} />
        <StatCard label="Submitted reports" value={String(reportsSubmitted)} />
      </section>

      {!loading && !hasOrganizationAccess ? (
        <section role="status" className="rounded-2xl border border-amber-300 bg-amber-50 p-5">
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-900">Account setup needed</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">This login is not linked to an organization.</h2>
          <p className="mt-2 text-sm text-slate-700">Ask your Council Finance administrator to connect your account to your organization’s EIN. After that, assigned initiatives with an open reporting cycle and published form will appear here.</p>
        </section>
      ) : null}

      {loadError ? <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{loadError}</div> : null}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-900">My reports</h2>
          <button type="button" onClick={refreshDashboard} className="text-sm font-medium text-brand-700 hover:underline">
            Refresh
          </button>
        </div>
        {loading ? <p className="text-sm text-slate-500">Loading reports…</p> : null}
        {!loading && submissions.length === 0 ? <p className="text-sm text-slate-500">No saved or submitted reports yet. When work is available, you can continue it from this list.</p> : null}
        <div className="space-y-3">
          {submissions.map((submission) => (
            <Link
              key={submission.submission_id}
              to={`/reports/${encodeURIComponent(submission.submission_id)}`}
              className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 p-4 hover:border-brand-300"
            >
              <div>
                <div className="font-semibold text-slate-900">{submission.initiative_name}</div>
                <div className="text-sm text-slate-500">{submission.organization_name} · {submission.cycle_name}</div>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="rounded-full bg-slate-100 px-3 py-1 font-semibold text-slate-700">{submission.status}</span>
                <span>${submission.total_budget}</span>
                <span className="font-semibold text-brand-700">{['DRAFT', 'REVISION_REQUESTED'].includes(submission.status) ? 'Continue report →' : 'View report →'}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {user?.role === 'EXTERNAL_SUBMITTER' ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-xl font-semibold text-slate-900">Available reports</h2>
          {!loading && available.length === 0 && hasOrganizationAccess ? (
            <p className="mb-4 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">There are no new eligible reports for your linked organizations right now. This list updates when Council opens an assigned reporting cycle and publishes its form.</p>
          ) : null}
          <div className="space-y-3">
            {available.map((report) => {
              const key = `${report.initiative_id}:${report.organization_id}:${report.cycle_id}`;
              return (
                <div key={key} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 p-4">
                  <div>
                    <div className="font-semibold text-slate-900">{report.initiative_name}</div>
                    <div className="text-sm text-slate-500">{report.organization_name} · {report.cycle_name}</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => void startReport(report)}
                    disabled={startingId !== null}
                    className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
                  >
                    {startingId === key ? 'Starting…' : 'Start report'}
                  </button>
                </div>
              );
            })}
          </div>
        </section>
      ) : null}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium uppercase tracking-wide text-brand-600">Reporting workflow</p>
            <h2 className="mt-1 text-xl font-semibold text-slate-900">What happens after you start a report</h2>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{hasOrganizationAccess ? 'Ready when an assignment is open' : 'Waiting for organization access'}</span>
        </div>
        <ol className="mt-5 grid gap-3 md:grid-cols-4">
          {[
            ['1', 'Open an assignment', 'Choose an initiative and reporting cycle assigned to your organization.'],
            ['2', 'Complete the report', 'Answer the programmatic questions configured for that initiative.'],
            ['3', 'Enter budget and files', 'Add up to 100 budget lines and attach supporting documents up to 25 MiB each.'],
            ['4', 'Review and submit', 'Check your answers and totals; the server validates required fields and configured budget balance.'],
          ].map(([number, title, description]) => (
            <li key={number} className="rounded-xl border border-slate-200 p-4">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-700">{number}</span>
              <h3 className="mt-3 font-semibold text-slate-900">{title}</h3>
              <p className="mt-1 text-sm leading-5 text-slate-600">{description}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-bold text-slate-900">{value}</div>
    </div>
  );
}
