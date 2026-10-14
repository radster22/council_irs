import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Layout } from './Layout';

const logout = vi.fn();

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    token: 'test-token',
    user: { id: 'admin-1', email: 'admin@example.org', full_name: 'Morgan Admin', role: 'COUNCIL_ADMIN', organization_ids: [] },
    logout,
  }),
}));

function renderLayout() {
  return render(
    <MemoryRouter initialEntries={['/review']}>
      <Layout portal="council"><p>Page content</p></Layout>
    </MemoryRouter>,
  );
}

describe('Layout sidebar', () => {
  beforeEach(() => { localStorage.clear(); logout.mockClear(); });
  afterEach(cleanup);

  it('collapses to initials and a logout icon, then expands again', () => {
    renderLayout();
    const sidebar = screen.getByRole('complementary', { name: 'Sidebar' });
    expect(within(sidebar).getByText('Finance Admin Hub')).toBeInTheDocument();
    expect(within(sidebar).getByText('Morgan Admin')).toBeInTheDocument();
    expect(within(sidebar).getByText('Submission Oversight')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Collapse sidebar' }));

    expect(sidebar).toHaveAttribute('data-collapsed', 'true');
    expect(within(sidebar).queryByText('Finance Admin Hub')).not.toBeInTheDocument();
    expect(within(sidebar).queryByText('Morgan Admin')).not.toBeInTheDocument();
    expect(within(sidebar).getByRole('img', { name: 'Morgan Admin' })).toHaveTextContent('M');
    const oversight = within(sidebar).getByRole('link', { name: 'Submission Oversight' });
    expect(oversight).toHaveTextContent(/^S$/);
    const logoutButton = within(sidebar).getByRole('button', { name: 'Log out' });
    expect(logoutButton).not.toHaveTextContent('Log out');
    expect(logoutButton.querySelector('svg')).not.toBeNull();
    expect(localStorage.getItem('council-sidebar-collapsed')).toBe('true');

    fireEvent.click(screen.getByRole('button', { name: 'Expand sidebar' }));
    expect(sidebar).toHaveAttribute('data-collapsed', 'false');
    expect(within(sidebar).getByText('Morgan Admin')).toBeInTheDocument();
  });

  it('restores the collapsed state and still logs out from the icon button', () => {
    localStorage.setItem('council-sidebar-collapsed', 'true');
    renderLayout();
    expect(screen.getByRole('complementary', { name: 'Sidebar' })).toHaveAttribute('data-collapsed', 'true');

    fireEvent.click(screen.getByRole('button', { name: 'Log out' }));
    expect(logout).toHaveBeenCalledTimes(1);
  });
});
