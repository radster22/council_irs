import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import type { AttachmentSummary, AttachmentUpload, BudgetLine, BudgetValidationSummary } from '../types';

const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;

type FormField = {
  id: string;
  type?: string;
  label?: string;
  required?: boolean;
  options?: string[];
  minimum?: number;
  maximum?: number;
  max_length?: number;
  max_words?: number;
  visible_when?: { field_id: string; equals?: unknown; not_equals?: unknown };
};

function amountToCents(value: string): bigint | null {
  const match = value.trim().match(/^(-?)(?:(\d+)(?:\.(\d{0,2}))?|\.(\d{1,2}))$/);
  if (!match) return null;
  const cents = BigInt(match[2] || '0') * 100n + BigInt((match[3] ?? match[4] ?? '').padEnd(2, '0') || '0');
  return match[1] === '-' ? -cents : cents;
}

function formatCents(cents: bigint): string {
  const sign = cents < 0n ? '-' : '';
  const absolute = cents < 0n ? -cents : cents;
  return `${sign}${absolute / 100n}.${String(absolute % 100n).padStart(2, '0')}`;
}

export function ReportEditorPage() {
  const params = useParams();
  const reportId = params.reportId ?? params.submissionId;
  const location = useLocation();
  const navigate = useNavigate();
  const isAdminEdit = location.pathname.endsWith('/edit');
  const { token, user } = useAuth();
  const [lines, setLines] = useState<BudgetLine[]>([]);
  const [formData, setFormData] = useState<Record<string, unknown>>({});
  const [formFields, setFormFields] = useState<FormField[]>([]);
  const [submissionStatus, setSubmissionStatus] = useState('DRAFT');
  const [isBalanced, setIsBalanced] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [summary, setSummary] = useState<BudgetValidationSummary | null>(null);
  const [error, setError] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<AttachmentSummary[]>([]);
  const [uploadError, setUploadError] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [isDirty, setIsDirty] = useState(false);
  const [adminEditComment, setAdminEditComment] = useState('');
  const [autosaveState, setAutosaveState] = useState('All changes saved');
  const [revisionRequest, setRevisionRequest] = useState<{ comment: string; created_at: string | null } | null>(null);
  const editVersion = useRef(0);

  const markDirty = () => {
    editVersion.current += 1;
    setIsDirty(true);
    setAutosaveState('Unsaved changes');
  };

  const total = useMemo(
    () => formatCents(lines.reduce((sum, line) => sum + (amountToCents(line.amount) ?? 0n), 0n)),
    [lines],
  );
  const actualTotal = useMemo(
    () => formatCents(lines.reduce((sum, line) => sum + (amountToCents(line.actual_amount ?? '') ?? 0n), 0n)),
    [lines],
  );
  const variance = useMemo(() => formatCents((amountToCents(actualTotal) ?? 0n) - (amountToCents(total) ?? 0n)), [actualTotal, total]);
  const canEdit = Boolean(
    user && (isAdminEdit
      ? user.role === 'COUNCIL_ADMIN' && submissionStatus !== 'DRAFT'
      : user.role === 'EXTERNAL_SUBMITTER' && ['DRAFT', 'REVISION_REQUESTED'].includes(submissionStatus)),
  );
  const visibleFormFields = formFields.filter((field) => {
    const condition = field.visible_when;
    if (!condition) return true;
    const sourceValue = formData[condition.field_id];
    if (Object.prototype.hasOwnProperty.call(condition, 'equals')) return sourceValue === condition.equals;
    if (Object.prototype.hasOwnProperty.call(condition, 'not_equals')) return sourceValue != null && sourceValue !== '' && sourceValue !== condition.not_equals;
    return false;
  });

  useEffect(() => {
    if (!token || !reportId) return;
    let active = true;
    setLoading(true);
    api.getSubmission(reportId, token)
      .then((submission) => {
        if (!active) return;
        setLines(submission.budget_lines);
        setFormData(submission.form_data);
        setSubmissionStatus(submission.status);
        setIsBalanced(submission.is_balanced);
        setUploadedFiles(submission.attachments);
        // audit_history is oldest-first; the last revision request is the one the submitter must address.
        const latestRequest = [...submission.audit_history].reverse().find((event) => event.action === 'REQUEST_REVISION');
        const requestComment = latestRequest?.state_diff.comment;
        setRevisionRequest(latestRequest && typeof requestComment === 'string' && requestComment
          ? { comment: requestComment, created_at: latestRequest.created_at }
          : null);
        setIsDirty(false);
        setAutosaveState('All changes saved');
        const fields = submission.form_schema.fields;
        setFormFields(Array.isArray(fields) ? fields.filter((field): field is FormField => (
          typeof field === 'object' && field !== null && 'id' in field && typeof field.id === 'string'
        )) : []);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Could not load this report.'))
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [reportId, token]);

  const updateLine = (index: number, field: keyof BudgetLine, value: string) => {
    markDirty();
    setLines((current) => current.map((line, lineIndex) => (lineIndex === index ? { ...line, [field]: value } : line)));
  };

  const addLine = () => {
    markDirty();
    setLines((current) => [...current, { category: '', description: '', amount: '', actual_amount: '' }]);
  };

  const removeLine = (index: number) => {
    markDirty();
    setLines((current) => current.filter((_, lineIndex) => lineIndex !== index));
  };

  const updateFormField = (id: string, value: unknown) => {
    markDirty();
    setFormData((current) => ({ ...current, [id]: value }));
  };

  const validateBudget = async () => {
    if (!token) {
      setError('A valid session token is required to validate budgets.');
      return;
    }

    setSaving(true);
    setError('');

    try {
      const nextSummary = await api.validateBudget(lines, token);
      setSummary(nextSummary);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Budget validation failed');
    } finally {
      setSaving(false);
    }
  };

  const saveSubmission = async (status: 'DRAFT' | 'SUBMITTED') => {
    if (!token || !reportId) {
      setError('A valid session token is required to save this report.');
      return;
    }

    const savingVersion = editVersion.current;
    setSaving(true);
    setError('');
    setStatusMessage('');

    try {
      if (isAdminEdit) {
        if (!adminEditComment.trim()) {
          setError('Add an audit note explaining the Council edit.');
          return;
        }
        const response = await api.adminEditSubmission(reportId, {
          form_data: formData,
          budget_lines: lines,
          comment: adminEditComment,
        }, token);
        setIsDirty(false);
        setAutosaveState('Audited changes saved');
        setStatusMessage(`A new immutable version was recorded (${response.action}).`);
        return;
      }
      if (status === 'SUBMITTED') {
        const nextSummary = await api.validateBudget(lines, token);
        if (!nextSummary.is_valid) {
          setSummary(nextSummary);
          setError(nextSummary.errors.join(' '));
          return;
        }
      }

      const response = await api.saveSubmission(reportId, {
        status,
        form_data: formData,
        budget_lines: lines,
      }, token);

      setSummary({
        line_count: response.line_count,
        total: response.total_budget,
        is_valid: response.is_valid,
        errors: response.validation_errors,
      });
      setSubmissionStatus(response.status);
      setIsBalanced(response.is_balanced);
      if (editVersion.current === savingVersion) {
        setIsDirty(false);
        setAutosaveState('All changes saved');
      }
      setStatusMessage(status === 'DRAFT'
        ? (response.is_valid && response.validation_errors.length === 0 ? 'Draft saved successfully.' : 'Draft saved. Complete the flagged fields before submitting.')
        : 'Submission saved successfully.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Report save failed');
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    if (isAdminEdit || !isDirty || loading || saving || !canEdit || !token || !reportId) return;
    const savingVersion = editVersion.current;
    const timeout = window.setTimeout(async () => {
      setAutosaveState('Saving…');
      setSaving(true);
      try {
        const response = await api.saveSubmission(reportId, {
          status: 'DRAFT',
          form_data: formData,
          budget_lines: lines,
        }, token);
        setSummary({ line_count: response.line_count, total: response.total_budget,
          is_valid: response.is_valid, errors: response.validation_errors });
        setIsBalanced(response.is_balanced);
        setSubmissionStatus(response.status);
        if (editVersion.current === savingVersion) {
          setIsDirty(false);
          setAutosaveState('All changes saved');
        }
      } catch (err) {
        setAutosaveState('Autosave failed');
        setError(err instanceof Error ? err.message : 'Could not autosave this report.');
      } finally {
        setSaving(false);
      }
    }, 900);
    return () => window.clearTimeout(timeout);
  }, [canEdit, formData, isAdminEdit, isDirty, lines, loading, reportId, saving, token]);

  // Mirror the backend 25 MiB cap so oversized files are rejected before any network transfer.
  const oversizedFileMessage = (files: File[]) => {
    const oversized = files.filter((file) => file.size > MAX_UPLOAD_BYTES);
    if (!oversized.length) return '';
    const names = oversized.map((file) => file.name).join(', ');
    return `${names} ${oversized.length === 1 ? 'is' : 'are'} larger than 25 MB. Upload a file smaller than 25 MB.`;
  };

  const selectFiles = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    const message = oversizedFileMessage(files);
    setUploadError(message);
    setStatusMessage('');
    if (message) {
      event.target.value = '';
      setSelectedFiles([]);
      return;
    }
    setSelectedFiles(files);
  };

  const uploadSelectedFile = async () => {
    if (!token || !reportId || !selectedFiles.length) {
      setUploadError('Choose a file before uploading.');
      return;
    }
    const sizeMessage = oversizedFileMessage(selectedFiles);
    if (sizeMessage) {
      setUploadError(sizeMessage);
      setStatusMessage('');
      return;
    }

    setSaving(true);
    setUploadError('');
    setStatusMessage('');

    try {
      const attachments: AttachmentUpload[] = [];
      for (const file of selectedFiles) attachments.push(await api.uploadAttachment(reportId, file, token));
      setUploadedFiles((current) => [...attachments, ...current]);
      setStatusMessage(`${attachments.length} file${attachments.length === 1 ? '' : 's'} uploaded successfully.`);
      setSelectedFiles([]);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600">Loading report workspace…</div>;
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-500">Reporting</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">{isAdminEdit ? 'Council report edit' : 'Submission editor'}</h1>
        <p className="mt-2 text-sm text-slate-600">{isAdminEdit ? 'Changes are saved as a new immutable version and recorded in the audit history.' : 'Complete each stage, save your draft, then submit after reviewing the server checks.'}</p>
        <p aria-live="polite" className="mt-2 text-xs font-medium text-slate-500">{autosaveState}</p>
      </header>

      {submissionStatus === 'REVISION_REQUESTED' && revisionRequest ? (
        <section role="status" className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-900">Council Finance requested updates</p>
          {revisionRequest.created_at ? <p className="text-xs text-amber-700">{revisionRequest.created_at}</p> : null}
          <p className="mt-2 whitespace-pre-wrap text-sm text-amber-900">{revisionRequest.comment}</p>
        </section>
      ) : null}

      <nav aria-label="Report workflow" className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ['report-step-1', '1', 'Report questions'],
          ['report-step-2', '2', 'Budget grid'],
          ['report-step-3', '3', 'Documents'],
          ['report-step-4', '4', 'Review and submit'],
        ].map(([target, number, label]) => (
          <button key={target} type="button" onClick={() => document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-3 text-left hover:border-brand-400">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-700">{number}</span>
            <span className="text-sm font-semibold text-slate-800">{label}</span>
          </button>
        ))}
      </nav>

      {!loading ? (
        <section id="report-step-1" className="scroll-mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-600">Step 1 · Programmatic metrics and narrative</p>
          <h2 className="mb-4 text-xl font-semibold text-slate-900">Report questions</h2>
          {visibleFormFields.length === 0 ? <p className="text-sm text-slate-500">No questions apply to the current responses. Continue to the budget stage.</p> : null}
          <div className="grid gap-4 md:grid-cols-2">
            {visibleFormFields.map((field) => {
              const value = formData[field.id] == null ? '' : String(formData[field.id]);
              const label = field.label ?? field.id;
              const className = 'w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100';
              return (
                <label key={field.id} className="block text-sm font-medium text-slate-700">
                  <span className="mb-1 block">{label}{field.required ? ' *' : ''}</span>
                  {field.type === 'boolean' ? (
                    <input disabled={!canEdit} type="checkbox" checked={formData[field.id] === true} onChange={(event) => updateFormField(field.id, event.target.checked)} className="mr-2 h-4 w-4 rounded border-slate-300 text-brand-600" />
                  ) : field.type === 'textarea' || field.type === 'narrative' ? (
                    <textarea disabled={!canEdit} required={field.required} maxLength={field.max_length} value={value} onChange={(event) => updateFormField(field.id, event.target.value)} className={className} rows={4} />
                  ) : field.options ? (
                    <select disabled={!canEdit} required={field.required} value={value} onChange={(event) => updateFormField(field.id, event.target.value)} className={className}>
                      <option value="">Select an option</option>
                      {field.options.map((option) => <option key={option} value={option}>{option}</option>)}
                    </select>
                  ) : (
                    <input
                      disabled={!canEdit}
                      required={field.required}
                      type={field.type === 'integer' || field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text'}
                      step={field.type === 'integer' ? '1' : 'any'}
                      min={field.minimum}
                      max={field.maximum}
                      maxLength={field.max_length}
                      value={value}
                      onChange={(event) => updateFormField(field.id, event.target.value)}
                      className={className}
                    />
                  )}
                  {field.max_words ? <span className="mt-1 block text-xs font-normal text-slate-500">{value.trim() ? value.trim().split(/\s+/).length : 0} / {field.max_words} words</span> : null}
                </label>
              );
            })}
          </div>
        </section>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-[1.5fr_0.8fr]">
        <div id="report-step-2" className="scroll-mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-brand-600">Step 2 · Budget</p>
              <h2 className="text-xl font-semibold text-slate-900">Budget grid</h2>
            </div>
            <button
              type="button"
              onClick={addLine}
              disabled={!canEdit || lines.length >= 100}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Add line
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[850px] border-collapse text-left text-sm">
              <thead><tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500"><th className="px-2 py-2">Line</th><th className="px-2 py-2">Category</th><th className="px-2 py-2">Description</th><th className="px-2 py-2">Budgeted amount</th><th className="px-2 py-2">Actual amount</th><th className="px-2 py-2">Action</th></tr></thead>
              <tbody>
                {lines.map((line, index) => (
                  <tr key={index} className="border-b border-slate-100">
                    <td className="px-2 py-2 font-medium text-slate-600">{index + 1}</td>
                    <td className="px-2 py-2"><input disabled={!canEdit} value={line.category} onChange={(event) => updateLine(index, 'category', event.target.value)} placeholder="Category" maxLength={100} className="w-full rounded-lg border border-slate-300 px-3 py-2" /></td>
                    <td className="px-2 py-2"><input disabled={!canEdit} value={line.description ?? ''} onChange={(event) => updateLine(index, 'description', event.target.value)} placeholder="Optional description" maxLength={500} className="w-full rounded-lg border border-slate-300 px-3 py-2" /></td>
                    <td className="px-2 py-2"><input disabled={!canEdit} value={line.amount} onChange={(event) => updateLine(index, 'amount', event.target.value)} placeholder="0.00" inputMode="decimal" className="w-full rounded-lg border border-slate-300 px-3 py-2" /></td>
                    <td className="px-2 py-2"><input disabled={!canEdit} value={line.actual_amount ?? ''} onChange={(event) => updateLine(index, 'actual_amount', event.target.value)} placeholder="Optional" inputMode="decimal" className="w-full rounded-lg border border-slate-300 px-3 py-2" /></td>
                    <td className="px-2 py-2"><button type="button" onClick={() => removeLine(index)} disabled={!canEdit} className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-100">Remove</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-5 flex items-center justify-between rounded-xl bg-slate-50 p-4 text-sm">
            <span className="font-medium text-slate-700">Live budget total · {lines.length} / 100 rows</span>
            <span className="text-lg font-bold text-slate-900">Budgeted ${total} · Actual ${actualTotal} · Variance ${variance}</span>
          </div>

          <div id="report-step-3" className="mt-6 scroll-mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-brand-600">Step 3 · Documents</p>
            <h3 className="text-lg font-semibold text-slate-900">Supporting documents</h3>
            <p className="mt-1 text-sm text-slate-600">Upload one or more files. Each file may be up to 25 MiB.</p>
            <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
              <input
                disabled={!canEdit}
                type="file"
                multiple
                accept=".pdf,.csv,.xlsx,.xls,.doc,.docx,.txt,.jpg,.jpeg,.png"
                aria-label="Supporting documents"
                aria-describedby={uploadError ? 'upload-error' : undefined}
                onChange={selectFiles}
                className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-brand-500 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
              />
              <button
                type="button"
                onClick={uploadSelectedFile}
                disabled={!canEdit || !selectedFiles.length || saving}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Upload {selectedFiles.length > 1 ? `${selectedFiles.length} files` : 'file'}
              </button>
            </div>
            {uploadError ? <p id="upload-error" role="alert" className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{uploadError}</p> : null}

            {uploadedFiles.length > 0 ? (
              <ul className="mt-3 space-y-2 text-sm text-slate-600">
                {uploadedFiles.map((item) => (
              <li key={item.attachment_id} className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2">
                    {item.original_filename} • {item.file_size_bytes} bytes
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        </div>

        <div id="report-step-4" className="scroll-mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-brand-600">Step 4 · Review and final submit</p>
          <h2 className="text-xl font-semibold text-slate-900">Review your report</h2>
          <dl className="mt-4 space-y-3 text-sm text-slate-600">
            <div className="flex justify-between gap-3"><dt>Report ID</dt><dd className="font-medium text-slate-800">{reportId}</dd></div>
            <div className="flex justify-between gap-3"><dt>Status</dt><dd className="font-medium text-slate-800">{submissionStatus}</dd></div>
            <div className="flex justify-between gap-3"><dt>Computed total</dt><dd className="font-medium text-slate-800">${total}</dd></div>
            <div className="flex justify-between gap-3"><dt>Configured balance check</dt><dd className={`font-semibold ${isBalanced ? 'text-emerald-700' : 'text-amber-700'}`}>{isBalanced ? 'Passed' : 'Needs review'}</dd></div>
          </dl>
          <p className="mt-3 text-xs text-slate-500">The final submission check runs against the published form’s configured reconciliation rule on the server.</p>

          <div className="mt-6 grid gap-3">
            {isAdminEdit ? <label className="text-sm font-medium text-slate-700">Required audit note<textarea value={adminEditComment} onChange={(event) => setAdminEditComment(event.target.value)} maxLength={5000} rows={3} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" /></label> : null}
            {isAdminEdit ? <button type="button" onClick={() => saveSubmission('SUBMITTED')} disabled={!canEdit || saving || !adminEditComment.trim()} className="w-full rounded-lg bg-brand-500 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">{saving ? 'Saving audited version...' : 'Save audited changes'}</button> : null}
            {!isAdminEdit ? <>
            <button
              type="button"
              onClick={() => saveSubmission('DRAFT')}
              disabled={!canEdit || saving}
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? 'Saving...' : 'Save draft'}
            </button>
            <button
              type="button"
              onClick={() => saveSubmission('SUBMITTED')}
              disabled={!canEdit || saving}
              className="w-full rounded-lg bg-brand-500 px-4 py-3 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? 'Submitting...' : 'Submit report'}
            </button>
            </> : null}
          </div>

          {submissionStatus === 'SUBMITTED' ? (
            <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
              <p className="font-semibold">Submission confirmation</p>
              <p className="mt-1">Your report was submitted successfully. Keep this report ID for your records: {reportId}</p>
              <button type="button" onClick={() => window.print()} className="no-print mt-3 rounded-lg border border-emerald-300 bg-white px-3 py-2 text-sm font-semibold text-emerald-800">Print / Save receipt as PDF</button>
            </div>
          ) : null}

          {error ? <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
          {statusMessage ? <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{statusMessage}</div> : null}

          {summary ? (
            <div className={`mt-4 rounded-lg border p-3 text-sm ${summary.is_valid && !summary.errors.length ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'}`}>
              <div className="font-semibold">{summary.is_valid && !summary.errors.length ? 'Budget valid' : 'Draft requires attention'}</div>
              <div className="mt-1">Total: ${summary.total}</div>
              {summary.errors.length > 0 ? (
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {summary.errors.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}
