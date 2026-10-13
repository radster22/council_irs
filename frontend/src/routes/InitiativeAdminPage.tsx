import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import type { InitiativeAdminItem } from '../types';

const inputClass = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm';

export function InitiativeAdminPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<InitiativeAdminItem[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [fiscalYear, setFiscalYear] = useState('');
  const [cycleName, setCycleName] = useState('');
  const [startDate, setStartDate] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [cycleStatus, setCycleStatus] = useState('UPCOMING');
  const [ein, setEin] = useState('');
  const [awardedAmount, setAwardedAmount] = useState('');
  const [schemaText, setSchemaText] = useState('{\n  "title": "",\n  "sections": [],\n  "fields": []\n}');
  const [publish, setPublish] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    if (!token) return;
    const data = await api.listInitiatives(token);
    setItems(data);
    setSelectedId((current) => current || data[0]?.id || '');
  };

  useEffect(() => { refresh().catch((err: unknown) => setError(err instanceof Error ? err.message : 'Could not load initiatives.')); }, [token]);

  const perform = async (action: () => Promise<unknown>, success: string) => {
    setBusy(true); setError(''); setMessage('');
    try { await action(); setMessage(success); await refresh(); }
    catch (err) { setError(err instanceof Error ? err.message : 'The change could not be saved.'); }
    finally { setBusy(false); }
  };

  const createInitiative = (event: React.FormEvent) => {
    event.preventDefault();
    if (!token) return;
    void perform(() => api.createInitiative({ code, name, fiscal_year: Number(fiscalYear) }, token), 'Initiative created.');
  };
  const createCycle = (event: React.FormEvent) => {
    event.preventDefault();
    if (!token || !selectedId) return;
    void perform(() => api.createCycle(selectedId, { cycle_name: cycleName, start_date: startDate, due_date: dueDate, status: cycleStatus }, token), 'Reporting cycle created.');
  };
  const createAssignment = (event: React.FormEvent) => {
    event.preventDefault();
    if (!token || !selectedId) return;
    void perform(() => api.createAssignment(selectedId, { ein, awarded_amount: awardedAmount }, token), 'Organization assignment created.');
  };
  const createTemplate = (event: React.FormEvent) => {
    event.preventDefault();
    if (!token || !selectedId) return;
    try {
      const schema = JSON.parse(schemaText) as Record<string, unknown>;
      void perform(() => api.createTemplate(selectedId, { schema_definition: schema, is_published: publish }, token), 'New versioned form template created.');
    } catch { setError('Form schema must be valid JSON.'); }
  };

  return <div className="space-y-6">
    <header><p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-500">Administration</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Initiatives, cycles, assignments & forms</h1><p className="mt-2 text-sm text-slate-600">Configuration is stored in the existing MySQL tables. Published form versions are never edited in place.</p></header>
    {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
    {message ? <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p> : null}
    <form onSubmit={createInitiative} className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-5 md:grid-cols-4"><h2 className="md:col-span-4 text-lg font-semibold">Create initiative</h2><input required value={code} onChange={(e) => setCode(e.target.value)} placeholder="Unique code" maxLength={50} className={inputClass} /><input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Initiative name" maxLength={255} className={inputClass} /><input required type="number" min="2000" max="2200" value={fiscalYear} onChange={(e) => setFiscalYear(e.target.value)} placeholder="Fiscal year" className={inputClass} /><button disabled={busy} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Create initiative</button></form>
    <label className="block rounded-xl border border-slate-200 bg-white p-4 text-sm font-medium">Configure initiative<select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} className={`${inputClass} mt-2`}><option value="">Select an initiative</option>{items.map((item) => <option key={item.id} value={item.id}>{item.fiscal_year} · {item.name} ({item.code})</option>)}</select></label>
    {selectedId ? <div className="grid gap-5 xl:grid-cols-3">
      <form onSubmit={createCycle} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5"><h2 className="text-lg font-semibold">Add reporting cycle</h2><input required value={cycleName} onChange={(e) => setCycleName(e.target.value)} placeholder="Cycle name" maxLength={100} className={inputClass} /><label className="block text-sm">Starts<input required type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className={`${inputClass} mt-1`} /></label><label className="block text-sm">Due<input required type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className={`${inputClass} mt-1`} /></label><label className="block text-sm">Status<select value={cycleStatus} onChange={(e) => setCycleStatus(e.target.value)} className={`${inputClass} mt-1`}><option>UPCOMING</option><option>OPEN</option><option>CLOSED</option></select></label><button disabled={busy} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white">Add cycle</button></form>
      <form onSubmit={createAssignment} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5"><h2 className="text-lg font-semibold">Assign organization</h2><input required value={ein} onChange={(e) => setEin(e.target.value)} placeholder="Organization EIN" maxLength={10} className={inputClass} /><label className="block text-sm">Awarded amount<input required inputMode="decimal" pattern="\\d+(\\.\\d{1,2})?" value={awardedAmount} onChange={(e) => setAwardedAmount(e.target.value)} placeholder="0.00" className={`${inputClass} mt-1`} /></label><p className="text-xs text-slate-500">EIN must already exist in the active organizations registry.</p><button disabled={busy} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white">Assign organization</button></form>
      <form onSubmit={createTemplate} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5"><h2 className="text-lg font-semibold">Create form version</h2><textarea required value={schemaText} onChange={(e) => setSchemaText(e.target.value)} rows={10} className={`${inputClass} font-mono`} /><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={publish} onChange={(e) => setPublish(e.target.checked)} />Publish this version</label><button disabled={busy} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white">Create form version</button></form>
    </div> : null}
    <section className="space-y-3">{items.map((item) => <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-lg font-semibold">{item.name} <span className="text-sm font-normal text-slate-500">FY{item.fiscal_year} · {item.status}</span></h2><select aria-label={`Status for ${item.name}`} value={item.status} onChange={(e) => token && void perform(() => api.updateInitiative(item.id, { status: e.target.value }, token), 'Initiative status updated.')} className="rounded-lg border border-slate-300 px-2 py-1 text-xs"><option>ACTIVE</option><option>COMBINED</option><option>RETIRED</option></select></div><p className="text-sm text-slate-500">{item.code}</p>{item.lineage.length ? <p className="mt-1 text-xs text-slate-500">Lineage: {item.lineage.map((line) => `${line.relationship_type} ${line.direction} ${line.initiative_code}`).join(' · ')}</p> : null}<div className="mt-3 grid gap-4 text-sm md:grid-cols-3"><div><h3 className="font-semibold">Cycles</h3>{item.cycles.map((cycle) => <div key={cycle.id} className="mt-1 flex flex-wrap items-center justify-between gap-2"><span>{cycle.cycle_name} · due {cycle.due_date}</span><select aria-label={`Status for ${cycle.cycle_name}`} value={cycle.status} onChange={(e) => token && void perform(() => api.updateCycle(cycle.id, e.target.value, token), 'Cycle status updated.')} className="rounded border border-slate-300 px-2 py-1 text-xs"><option>UPCOMING</option><option>OPEN</option><option>CLOSED</option></select></div>)}{!item.cycles.length ? <p className="text-slate-500">None</p> : null}</div><div><h3 className="font-semibold">Assignments</h3>{item.assignments.map((assignment) => <p key={assignment.organization_id}>{assignment.legal_name} · {assignment.ein} · ${assignment.awarded_amount}</p>)}{!item.assignments.length ? <p className="text-slate-500">None</p> : null}</div><div><h3 className="font-semibold">Form versions</h3>{item.templates.map((template) => <p key={template.id}>v{template.version} · {template.is_published ? 'Published' : 'Draft'}</p>)}{!item.templates.length ? <p className="text-slate-500">None</p> : null}</div></div></article>)}</section>
  </div>;
}
