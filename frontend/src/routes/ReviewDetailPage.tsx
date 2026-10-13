import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import type { SubmissionDetail } from '../types';

export function ReviewDetailPage() {
  const { submissionId = '' } = useParams();
  const { token, user } = useAuth();
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [comment, setComment] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const canReview = user?.role === 'COUNCIL_ADMIN' || user?.role === 'COUNCIL_REVIEWER';

  const load = useCallback(async () => {
    if (!token || !submissionId) return;
    const data = await api.getSubmission(submissionId, token);
    setSubmission(data);
  }, [submissionId, token]);

  useEffect(() => { load().catch((err: unknown) => setError(err instanceof Error ? err.message : 'Could not load this report.')); }, [load]);

  const act = async (action: 'START_REVIEW' | 'REQUEST_REVISION' | 'APPROVE' | 'REJECT') => {
    if (!token) return;
    setBusy(true); setError(''); setMessage('');
    try {
      const result = await api.reviewSubmission(submissionId, action, comment, token);
      setMessage(`Review action recorded. Status: ${result.status}.`);
      setComment('');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update review status.');
    } finally { setBusy(false); }
  };

  const download = async (attachmentId: string, filename: string) => {
    if (!token) return;
    try {
      const blob = await api.downloadAttachment(submissionId, attachmentId, token);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = filename;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not download attachment.');
    }
  };

  if (error && !submission) return <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>;
  if (!submission) return <p className="text-sm text-slate-500">Loading report…</p>;
  const fields = Array.isArray(submission.form_schema.fields) ? submission.form_schema.fields as { id: string; label?: string }[] : [];
  const canStart = submission.status === 'SUBMITTED';
  const canDispose = submission.status === 'IN_REVIEW';

  return (
    <div className="space-y-6">
      <Link to="/review" className="text-sm font-medium text-brand-700 hover:underline">← Back to oversight queue</Link>
      <header>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-500">Council review</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">{submission.initiative_name}</h1>
        <p className="mt-2 text-slate-600">{submission.organization_name} · {submission.cycle_name}</p>
        <div className="no-print mt-3 flex gap-3">
          <button type="button" onClick={() => window.print()} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700">Print / Save PDF</button>
          {user?.role === 'COUNCIL_ADMIN' && submission.status !== 'DRAFT' ? <Link to={`/review/${encodeURIComponent(submissionId)}/edit`} className="rounded-lg bg-brand-600 px-3 py-2 text-sm font-semibold text-white">Edit with audit version</Link> : null}
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-4">
        {[
          ['Status', submission.status], ['Budget total', `$${submission.total_budget}`], ['Allocated', `$${submission.allocated_budget}`], ['Balance', submission.is_balanced ? 'Balanced' : 'Flagged'],
        ].map(([label, value]) => <div key={label} className="rounded-xl border border-slate-200 bg-white p-4"><div className="text-xs uppercase tracking-wide text-slate-500">{label}</div><div className="mt-1 font-semibold text-slate-900">{value}</div></div>)}
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-slate-900">Report responses</h2>
        <dl className="mt-4 grid gap-4 md:grid-cols-2">
          {fields.map((field) => <div key={field.id} className="rounded-lg bg-slate-50 p-4"><dt className="text-sm font-medium text-slate-500">{field.label ?? field.id}</dt><dd className="mt-1 whitespace-pre-wrap text-sm text-slate-900">{String(submission.form_data[field.id] ?? '—')}</dd></div>)}
        </dl>
        <h3 className="mt-6 font-semibold text-slate-900">Budget lines</h3>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full min-w-[620px] text-left text-sm"><thead><tr className="border-b border-slate-200 text-xs uppercase text-slate-500"><th className="py-2">Line</th><th>Category</th><th>Description</th><th>Budgeted</th><th>Actual</th></tr></thead><tbody>
          {submission.budget_lines.map((line, index) => <tr key={`${line.category}-${index}`} className="border-b border-slate-100"><td className="py-2">{index + 1}</td><td>{line.category}</td><td>{line.description || '—'}</td><td>${line.amount}</td><td>{line.actual_amount ? `$${line.actual_amount}` : '—'}</td></tr>)}
          </tbody></table>
          {!submission.budget_lines.length ? <p className="py-3 text-sm text-slate-500">No budget lines recorded.</p> : null}
        </div>
        <h3 className="mt-6 font-semibold text-slate-900">Supporting documents</h3>
        <ul className="mt-2 space-y-2 text-sm text-slate-700">
          {submission.attachments.map((item) => <li key={item.attachment_id} className="flex items-center justify-between gap-4 rounded-lg bg-slate-50 px-3 py-2"><span>{item.original_filename} <span className="text-slate-500">({item.file_size_bytes} bytes)</span></span><button type="button" onClick={() => download(item.attachment_id, item.original_filename)} className="font-medium text-brand-700 hover:underline">Download</button></li>)}
          {!submission.attachments.length ? <li className="text-slate-500">No supporting documents attached.</li> : null}
        </ul>
      </section>

      {canReview ? <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-slate-900">Review disposition</h2>
        <label className="mt-3 block text-sm font-medium text-slate-700">Comment <span className="font-normal text-slate-500">(optional; included in audit history)</span>
          <textarea value={comment} onChange={(event) => setComment(event.target.value)} maxLength={5000} rows={3} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
        </label>
        <div className="mt-4 flex flex-wrap gap-3">
          {canStart ? <button disabled={busy} onClick={() => act('START_REVIEW')} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Start review</button> : null}
          {canDispose ? <>
            <button disabled={busy} onClick={() => act('REQUEST_REVISION')} className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-900 disabled:opacity-50">Request updates</button>
            <button disabled={busy} onClick={() => act('APPROVE')} className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Approve</button>
            <button disabled={busy} onClick={() => act('REJECT')} className="rounded-lg border border-red-300 bg-red-50 px-4 py-2 text-sm font-semibold text-red-800 disabled:opacity-50">Reject</button>
          </> : null}
          {!canStart && !canDispose ? <span className="py-2 text-sm text-slate-500">No review action is available for this status.</span> : null}
        </div>
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}{message ? <p className="mt-3 text-sm text-emerald-700">{message}</p> : null}
      </section> : null}

      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-slate-900">Submission versions</h2>
        <ol className="mt-3 space-y-3">
          {submission.versions.map((version) => <li key={version.version_number} className="border-l-2 border-brand-300 pl-4 text-sm"><div className="font-medium text-slate-800">Version {version.version_number} · Form version {version.template_version}</div><div className="text-xs text-slate-500">{version.submitted_at ?? 'Time unavailable'}</div>{version.reviewer_notes ? <p className="mt-1 whitespace-pre-wrap text-slate-700">{version.reviewer_notes}</p> : null}<details className="mt-2"><summary className="cursor-pointer text-brand-700">View immutable snapshot</summary><pre className="mt-2 max-h-96 overflow-auto rounded-lg bg-slate-50 p-3 text-xs">{JSON.stringify({ form: version.form_snapshot, budget: version.budget_snapshot }, null, 2)}</pre></details></li>)}
          {!submission.versions.length ? <li className="text-sm text-slate-500">No immutable submission snapshots recorded.</li> : null}
        </ol>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-slate-900">Audit history</h2>
        <ol className="mt-3 space-y-3">
          {submission.audit_history.map((event, index) => <li key={`${event.action}-${event.created_at}-${index}`} className="border-l-2 border-slate-200 pl-4 text-sm">
            <div className="font-medium text-slate-800">{event.action} <span className="font-normal text-slate-500">by {event.actor_role}</span></div>
            <div className="text-xs text-slate-500">{event.created_at ?? 'Time unavailable'} · {String(event.state_diff.from ?? '')} → {String(event.state_diff.to ?? '')}</div>
            {typeof event.state_diff.comment === 'string' && event.state_diff.comment ? <p className="mt-1 whitespace-pre-wrap text-slate-700">{event.state_diff.comment}</p> : null}
          </li>)}
          {!submission.audit_history.length ? <li className="text-sm text-slate-500">No audit events recorded.</li> : null}
        </ol>
      </section>
    </div>
  );
}
