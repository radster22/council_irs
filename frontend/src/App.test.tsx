import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { api } from './api/client';
import App from './App';
import { AuthProvider } from './hooks/useAuth';
import type { AuthUser, LoginResponse, Role } from './types';

vi.mock('./api/client', () => ({
  api: {
    login: vi.fn(),
    me: vi.fn(),
  },
}));

vi.mock('./routes/DashboardPage', async () => {
  const { createElement } = await import('react');
  return { DashboardPage: () => createElement('div', { 'data-testid': 'dashboard-page' }) };
});

vi.mock('./routes/ReportEditorPage', async () => {
  const { createElement } = await import('react');
  return { ReportEditorPage: () => createElement('div', { 'data-testid': 'report-editor-page' }) };
});

vi.mock('./routes/ReviewPage', async () => {
  const { createElement } = await import('react');
  return { ReviewPage: () => createElement('div', { 'data-testid': 'review-page' }) };
});

vi.mock('./routes/ReviewDetailPage', async () => {
  const { createElement } = await import('react');
  return { ReviewDetailPage: () => createElement('div', { 'data-testid': 'review-detail-page' }) };
});

vi.mock('./routes/UserPage', async () => {
  const { createElement } = await import('react');
  return { UserPage: () => createElement('div', { 'data-testid': 'user-page' }) };
});

const users: Record<Role, AuthUser> = {
  EXTERNAL_SUBMITTER: {
    id: 'submitter-1',
    email: 'submitter@example.org',
    full_name: 'Test Submitter',
    role: 'EXTERNAL_SUBMITTER',
    organization_ids: ['org-1'],
  },
  COUNCIL_ADMIN: {
    id: 'admin-1',
    email: 'admin@example.org',
    full_name: 'Test Admin',
    role: 'COUNCIL_ADMIN',
    organization_ids: [],
  },
  COUNCIL_REVIEWER: {
    id: 'reviewer-1',
    email: 'reviewer@example.org',
    full_name: 'Test Reviewer',
    role: 'COUNCIL_REVIEWER',
    organization_ids: [],
  },
  VIEW_ONLY: {
    id: 'viewer-1',
    email: 'viewer@example.org',
    full_name: 'Test Viewer',
    role: 'VIEW_ONLY',
    organization_ids: [],
  },
};

const protectedRoutes = [
  { path: '/', testId: undefined, roles: ['EXTERNAL_SUBMITTER', 'COUNCIL_ADMIN', 'COUNCIL_REVIEWER', 'VIEW_ONLY'] },
  { path: '/submit', testId: 'dashboard-page', roles: ['EXTERNAL_SUBMITTER'] },
  { path: '/reports/report-1', testId: 'report-editor-page', roles: ['EXTERNAL_SUBMITTER'] },
  { path: '/review', testId: 'review-page', roles: ['COUNCIL_ADMIN', 'COUNCIL_REVIEWER', 'VIEW_ONLY'] },
  { path: '/review/submission-1', testId: 'review-detail-page', roles: ['COUNCIL_ADMIN', 'COUNCIL_REVIEWER', 'VIEW_ONLY'] },
  { path: '/user_page', testId: 'user-page', roles: ['COUNCIL_ADMIN'] },
] as const;

const mockedApi = vi.mocked(api);

function renderAt(path: string, role?: Role) {
  if (role) {
    localStorage.setItem('council-auth-token', 'stored-token');
    mockedApi.me.mockResolvedValue(users[role]);
  }

  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
  mockedApi.login.mockResolvedValue({
    access_token: 'issued-token',
    token_type: 'bearer',
    role: 'EXTERNAL_SUBMITTER',
    user_id: users.EXTERNAL_SUBMITTER.id,
    email: users.EXTERNAL_SUBMITTER.email,
  });
  mockedApi.me.mockResolvedValue(users.EXTERNAL_SUBMITTER);
});

afterEach(() => {
  cleanup();
});

describe('application route authorization', () => {
  it.each(protectedRoutes.map(({ path }) => path))('redirects anonymous access to %s to login', async (path) => {
    renderAt(path);
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
  });

  for (const route of protectedRoutes) {
    for (const role of Object.keys(users) as Role[]) {
      const allowed = (route.roles as readonly Role[]).includes(role);
      it(`${role} ${allowed ? 'can access' : 'is denied'} ${route.path}`, async () => {
        renderAt(route.path, role);

        if (!allowed) {
          expect(await screen.findByRole('heading', { name: /you do not have access/i })).toBeInTheDocument();
          return;
        }

        if (route.testId) {
          expect(await screen.findByTestId(route.testId)).toBeInTheDocument();
        } else if (role === 'EXTERNAL_SUBMITTER') {
          expect(await screen.findByTestId('dashboard-page')).toBeInTheDocument();
        } else {
          expect(await screen.findByTestId('review-page')).toBeInTheDocument();
        }
      });
    }
  }

  it.each([
    ['EXTERNAL_SUBMITTER', 'dashboard-page'],
    ['COUNCIL_ADMIN', 'review-page'],
    ['COUNCIL_REVIEWER', 'review-page'],
    ['VIEW_ONLY', 'review-page'],
  ] as const)('routes authenticated %s users from home to their portal', async (role, page) => {
    renderAt('/', role);
    expect(await screen.findByTestId(page)).toBeInTheDocument();
  });

  it('sends unknown authenticated paths to the role landing page', async () => {
    renderAt('/not-a-route', 'COUNCIL_REVIEWER');
    expect(await screen.findByTestId('review-page')).toBeInTheDocument();
  });
});

describe('authentication session flows', () => {
  it('routes a submitter account to the selected external portal and persists the token', async () => {
    mockedApi.me.mockResolvedValue(users.EXTERNAL_SUBMITTER);
    renderAt('/login');

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'submitter@example.org' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'valid-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByTestId('dashboard-page')).toBeInTheDocument();
    expect(mockedApi.login).toHaveBeenCalledWith('submitter@example.org', 'valid-password');
    expect(localStorage.getItem('council-auth-token')).toBe('issued-token');
  });

  it('denies a submitter account when the council portal is selected', async () => {
    mockedApi.me.mockResolvedValue(users.EXTERNAL_SUBMITTER);
    renderAt('/login');

    fireEvent.click(screen.getByRole('button', { name: 'Council Finance' }));
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'submitter@example.org' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'valid-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/access denied/i);
    expect(screen.queryByTestId('dashboard-page')).not.toBeInTheDocument();
    expect(screen.queryByTestId('review-page')).not.toBeInTheDocument();
    expect(localStorage.getItem('council-auth-token')).toBeNull();
  });

  it('denies a council account when the external submitter portal is selected', async () => {
    mockedApi.me.mockResolvedValue(users.COUNCIL_ADMIN);
    renderAt('/login');
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'admin@example.org' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'valid-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/access denied/i);
    expect(screen.queryByTestId('dashboard-page')).not.toBeInTheDocument();
    expect(screen.queryByTestId('review-page')).not.toBeInTheDocument();
    expect(localStorage.getItem('council-auth-token')).toBeNull();
  });

  it.each([
    ['submitter', false],
    ['council', true],
  ] as const)('denies an unsupported account role from the %s portal', async (portal, selectCouncil) => {
    const unsupportedUser = { ...users.COUNCIL_ADMIN, role: 'SYSTEM_ADMIN' } as unknown as AuthUser;
    mockedApi.me.mockResolvedValue(unsupportedUser);
    renderAt('/login');

    if (selectCouncil) fireEvent.click(screen.getByRole('button', { name: 'Council Finance' }));
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'admin@example.org' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'valid-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/access denied/i);
    expect(screen.queryByTestId('dashboard-page')).not.toBeInTheDocument();
    expect(screen.queryByTestId('review-page')).not.toBeInTheDocument();
    expect(localStorage.getItem('council-auth-token')).toBeNull();
  });

  it('locks portal selection and ignores duplicate submits while authentication is pending', async () => {
    let resolveLogin!: (response: LoginResponse) => void;
    mockedApi.login.mockImplementation(() => new Promise<LoginResponse>((resolve) => {
      resolveLogin = resolve;
    }));
    mockedApi.me.mockResolvedValue(users.EXTERNAL_SUBMITTER);
    renderAt('/login');
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'submitter@example.org' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'valid-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(screen.getByRole('button', { name: 'Council Finance' })).toBeDisabled();
    fireEvent.submit(screen.getByRole('button', { name: 'Signing in...' }).closest('form')!);
    expect(mockedApi.login).toHaveBeenCalledTimes(1);

    resolveLogin({
      access_token: 'issued-token',
      token_type: 'bearer',
      role: 'EXTERNAL_SUBMITTER',
      user_id: users.EXTERNAL_SUBMITTER.id,
      email: users.EXTERNAL_SUBMITTER.email,
    });

    expect(await screen.findByTestId('dashboard-page')).toBeInTheDocument();
  });

  it.each([
    ['COUNCIL_ADMIN', 'review-page'],
    ['COUNCIL_REVIEWER', 'review-page'],
    ['VIEW_ONLY', 'review-page'],
  ] as const)('routes a successful %s login to the council portal', async (role, page) => {
    const currentUser = users[role];
    mockedApi.login.mockResolvedValue({
      access_token: 'council-token',
      token_type: 'bearer',
      role,
      user_id: currentUser.id,
      email: currentUser.email,
    });
    mockedApi.me.mockResolvedValue(currentUser);
    renderAt('/login');

    fireEvent.click(screen.getByRole('button', { name: 'Council Finance' }));
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: currentUser.email } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'valid-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByTestId(page)).toBeInTheDocument();
    expect(localStorage.getItem('council-auth-token')).toBe('council-token');
  });

  it('shows invalid-credential errors and does not persist a token', async () => {
    mockedApi.login.mockRejectedValue(new Error('Invalid credentials'));
    renderAt('/login');
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'unknown@example.org' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument();
    expect(localStorage.getItem('council-auth-token')).toBeNull();
  });

  it('does not persist a token if user identity lookup fails after login', async () => {
    mockedApi.me.mockRejectedValue(new Error('Account unavailable'));
    renderAt('/login');
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'submitter@example.org' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'valid-password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByText('Account unavailable')).toBeInTheDocument();
    expect(localStorage.getItem('council-auth-token')).toBeNull();
  });

  it('restores a valid stored token and clears a rejected stored token', async () => {
    renderAt('/review', 'COUNCIL_ADMIN');
    expect(await screen.findByTestId('review-page')).toBeInTheDocument();

    cleanup();
    localStorage.setItem('council-auth-token', 'expired-token');
    mockedApi.me.mockRejectedValueOnce(new Error('Invalid or expired token'));
    renderAt('/submit');

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(localStorage.getItem('council-auth-token')).toBeNull();
  });

  it('logs out by clearing the token and returning to login', async () => {
    renderAt('/submit', 'EXTERNAL_SUBMITTER');
    fireEvent.click(await screen.findByRole('button', { name: 'Log out' }));

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(localStorage.getItem('council-auth-token')).toBeNull();
  });
});