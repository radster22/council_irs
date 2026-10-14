import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const COLLAPSED_STORAGE_KEY = 'council-sidebar-collapsed';

// Remembering the sidebar state is a per-browser convenience; storage may be unavailable.
function readCollapsed() {
  try { return localStorage.getItem(COLLAPSED_STORAGE_KEY) === 'true'; } catch { return false; }
}

function writeCollapsed(value: boolean) {
  try { localStorage.setItem(COLLAPSED_STORAGE_KEY, String(value)); } catch { /* ignore */ }
}

const initial = (text: string | undefined, fallback = '?') => text?.trim().charAt(0).toUpperCase() || fallback;

function LogoutIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 shrink-0">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

function ToggleIcon({ collapsed }: { collapsed: boolean }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
      {collapsed ? <polyline points="9 18 15 12 9 6" /> : <polyline points="15 18 9 12 15 6" />}
    </svg>
  );
}

export function Layout({ children, portal }: { children: React.ReactNode; portal: 'submitter' | 'council' }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(readCollapsed);

  const toggleCollapsed = () => {
    const next = !collapsed;
    writeCollapsed(next);
    setCollapsed(next);
  };

  const portalName = portal === 'submitter' ? 'Submitter Portal' : 'Finance Admin Hub';
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
      <aside
        aria-label="Sidebar"
        data-collapsed={collapsed}
        className={`fixed inset-y-0 left-0 z-20 flex flex-col bg-slate-900 text-slate-100 transition-[width] duration-200 ${collapsed ? 'w-16' : 'w-72'}`}
      >
        <div className={`flex h-16 shrink-0 items-center border-b border-slate-700 ${collapsed ? 'justify-center px-2' : 'justify-between px-6'}`}>
          {collapsed ? null : (
            <div className="min-w-0">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">NYC</div>
              <div className="truncate text-lg font-semibold">{portalName}</div>
            </div>
          )}
          <button
            type="button"
            onClick={toggleCollapsed}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-expanded={!collapsed}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="rounded-md p-1.5 text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <ToggleIcon collapsed={collapsed} />
          </button>
        </div>

        <nav className={`flex-1 space-y-2 overflow-y-auto ${collapsed ? 'p-2' : 'p-4'}`}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              aria-label={collapsed ? item.label : undefined}
              title={collapsed ? item.label : undefined}
              className={({ isActive }) =>
                `flex items-center rounded-lg text-sm font-medium transition ${collapsed ? 'h-10 justify-center' : 'px-3 py-2'} ${
                  isActive ? 'bg-brand-500 text-white' : 'text-slate-200 hover:bg-slate-800'
                }`
              }
            >
              {collapsed ? <span aria-hidden="true" className="text-base font-semibold">{initial(item.label)}</span> : item.label}
            </NavLink>
          ))}
        </nav>

        <div className={`shrink-0 border-t border-slate-700 text-sm text-slate-300 ${collapsed ? 'flex flex-col items-center gap-3 p-2 py-4' : 'p-4'}`}>
          {collapsed ? (
            <div
              title={`${user?.full_name ?? 'Session user'} · ${user?.role ?? 'Role pending'}`}
              aria-label={user?.full_name ?? 'Session user'}
              role="img"
              className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-500 font-semibold text-white"
            >
              {initial(user?.full_name, 'U')}
            </div>
          ) : (
            <>
              <div className="font-medium text-white">{user?.full_name ?? 'Session user'}</div>
              <div className="text-xs text-slate-400">{user?.role ?? 'Role pending'}</div>
            </>
          )}
          <button
            type="button"
            aria-label="Log out"
            title={collapsed ? 'Log out' : undefined}
            onClick={() => {
              logout();
              navigate('/login', { replace: true });
            }}
            className={`flex items-center rounded-md border border-slate-600 text-slate-200 hover:bg-slate-800 ${collapsed ? 'h-9 w-9 justify-center' : 'mt-3 w-full gap-2 px-3 py-2 text-left'}`}
          >
            <LogoutIcon />
            {collapsed ? null : <span>Log out</span>}
          </button>
        </div>
      </aside>

      <main className={`min-h-screen p-8 transition-[margin] duration-200 ${collapsed ? 'ml-16' : 'ml-72'}`}>
        <div className="mx-auto max-w-6xl">{children}</div>
      </main>
    </div>
  );
}
