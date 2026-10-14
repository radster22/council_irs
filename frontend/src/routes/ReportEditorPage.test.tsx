import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { api } from '../api/client';
import { ReportEditorPage } from './ReportEditorPage';
import type { SubmissionDetail } from '../types';

vi.mock('../api/client', () => ({
  api: {
    getSubmission: vi.fn(),
    saveSubmission: vi.fn(),
    validateBudget: vi.fn(),
    uploadAttachment: vi.fn(),
    adminEditSubmission: vi.fn(),
  },
}));

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    token: 'test-token',
    user: { id: 'user-1', email: 'submitter@example.org', full_name: 'Submitter', role: 'EXTERNAL_SUBMITTER', organization_ids: ['org-1'] },
  }),
}));

const mockedApi = vi.mocked(api);

function submission(overrides: Partial<SubmissionDetail> = {}): SubmissionDetail {
  return {
    submission_id: 'sub-1',
    initiative_id: 'init-1',
    organization_id: 'org-1',
    cycle_id: 'cycle-1',
    template_version: 1,
    status: 'DRAFT',
    form_data: {},
    budget_lines: [{ category: '', description: '', amount: '', actual_amount: '' }],
    form_schema: { fields: [] },
    attachments: [],
    initiative_name: 'Test Initiative',
    organization_name: 'Test Org',
    cycle_name: 'Mid-Year',
    allocated_budget: '1000.00',
    total_budget: '0.00',
    is_balanced: false,
    audit_history: [],
    versions: [],
    ...overrides,
  };
}

function renderEditor() {
  return render(
    <MemoryRouter initialEntries={['/reports/sub-1']}>
      <Routes><Route path="/reports/:reportId" element={<ReportEditorPage />} /></Routes>
    </MemoryRouter>,
  );
}

function fileOfSize(name: string, bytes: number) {
  const file = new File(['x'], name, { type: 'application/pdf' });
  Object.defineProperty(file, 'size', { value: bytes });
  return file;
}

describe('ReportEditorPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedApi.saveSubmission.mockResolvedValue({ submission_id: 'sub-1', status: 'DRAFT' } as never);
    mockedApi.validateBudget.mockResolvedValue({ line_count: 1, total: '0.00', errors: [] } as never);
  });
  afterEach(cleanup);

  it('keeps focus in a budget category input while typing', async () => {
    mockedApi.getSubmission.mockResolvedValue(submission());
    renderEditor();

    const category = await screen.findByPlaceholderText('Category');
    category.focus();
    fireEvent.change(category, { target: { value: 'S' } });
    fireEvent.change(screen.getByPlaceholderText('Category'), { target: { value: 'St' } });

    const current = screen.getByPlaceholderText('Category');
    expect(current).toBe(category);
    expect(current).toHaveFocus();
    expect(current).toHaveValue('St');
  });

  it('shows the latest reviewer revision comment while revision is requested', async () => {
    mockedApi.getSubmission.mockResolvedValue(submission({
      status: 'REVISION_REQUESTED',
      audit_history: [
        { action: 'REQUEST_REVISION', actor_role: 'COUNCIL_REVIEWER', created_at: '2026-10-01T10:00:00', state_diff: { comment: 'Old comment' } },
        { action: 'SUBMIT', actor_role: 'EXTERNAL_SUBMITTER', created_at: '2026-10-02T10:00:00', state_diff: {} },
        { action: 'REQUEST_REVISION', actor_role: 'COUNCIL_REVIEWER', created_at: '2026-10-03T10:00:00', state_diff: { comment: 'Attach the signed budget.' } },
      ],
    }));
    renderEditor();

    expect(await screen.findByText('Council Finance requested updates')).toBeInTheDocument();
    expect(screen.getByText('Attach the signed budget.')).toBeInTheDocument();
    expect(screen.queryByText('Old comment')).not.toBeInTheDocument();
  });

  it('rejects a file over 25 MB at selection with a correction message beside the upload control', async () => {
    mockedApi.getSubmission.mockResolvedValue(submission());
    renderEditor();

    const input = await screen.findByLabelText('Supporting documents');
    fireEvent.change(input, { target: { files: [fileOfSize('large.pdf', 25 * 1024 * 1024 + 1)] } });

    expect(screen.getByRole('alert')).toHaveTextContent('large.pdf is larger than 25 MB. Upload a file smaller than 25 MB.');
    expect(screen.getByRole('button', { name: /upload file/i })).toBeDisabled();
    expect(mockedApi.uploadAttachment).not.toHaveBeenCalled();
  });

  it('accepts a file of exactly 25 MB and shows backend upload errors beside the upload control', async () => {
    mockedApi.getSubmission.mockResolvedValue(submission());
    mockedApi.uploadAttachment.mockRejectedValue(new Error('File content does not match its extension.'));
    renderEditor();

    const input = await screen.findByLabelText('Supporting documents');
    fireEvent.change(input, { target: { files: [fileOfSize('exact.pdf', 25 * 1024 * 1024)] } });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /upload file/i }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('File content does not match its extension.'));
    expect(mockedApi.uploadAttachment).toHaveBeenCalledTimes(1);
  });
});
