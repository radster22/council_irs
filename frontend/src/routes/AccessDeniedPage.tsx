import { Link } from 'react-router-dom';

export function AccessDeniedPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <section className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-red-600">403 · Access denied</p>
        <h1 className="mt-3 text-2xl font-bold text-slate-900">You do not have access to this page.</h1>
        <p className="page-lead">Your account role does not permit this route.</p>
        <Link to="/" className="mt-6 inline-block rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white">Return to your portal</Link>
      </section>
    </main>
  );
}
