import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function Layout({ children, portal }: { children: React.ReactNode; portal: 'submitter' | 'council' }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const navItems = portal === 'submitter'
    ? [{ to: '/submit', label: 'My Reports' }]
    : [
      { to: '/review', label: 'Submission Oversight' },
      ...(user?.role === 'COUNCIL_ADMIN' ? [{ to: '/user_page', label: 'User Administration' }] : []),
      ...(user?.role === 'COUNCIL_ADMIN' ? [{ to: '/admin/initiatives', label: 'Initiatives & Forms' }] : []),
      ...(user?.role === 'COUNCIL_ADMIN' ? [{ to: '/admin/rollover', label: 'Annual Rollover' }] : []),
    ];

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800">
      <aside className="fixed inset-y-0 left-0 w-72 bg-slate-900 text-slate-100">
        <div className="flex h-16 items-center justify-between border-b border-slate-700 px-6">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-slate-400">NYC</div>
            <div className="text-lg font-semibold">{portal === 'submitter' ? 'Submitter Portal' : 'Finance Admin Hub'}</div>
          </div>
        </div>

        <nav className="space-y-2 p-4">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive ? 'bg-brand-500 text-white' : 'text-slate-200 hover:bg-slate-800'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 w-full border-t border-slate-700 p-4 text-sm text-slate-300">
          <div className="font-medium text-white">{user?.full_name ?? 'Session user'}</div>
          <div className="text-xs text-slate-400">{user?.role ?? 'Role pending'}</div>
          <button
            type="button"
            onClick={() => {
              logout();
              navigate('/login', { replace: true });
            }}
            className="mt-3 w-full rounded-md border border-slate-600 px-3 py-2 text-left text-slate-200 hover:bg-slate-800"
          >
            Log out
          </button>
        </div>
      </aside>

      <main className="ml-72 min-h-screen p-8">
        <div className="mx-auto max-w-6xl">{children}</div>
      </main>
    </div>
  );
}
