import type {
  AttachmentUpload,
  AvailableReport,
  AuthUser,
  AdminUser,
  BudgetLine,
  BudgetValidationSummary,
  LoginResponse,
  SaveSubmissionPayload,
  SaveSubmissionResponse,
  SubmissionDetail,
  SubmissionListItem,
  ReviewQueueItem,
  InitiativeAdminItem,
  AdminAnalytics,
  OpenObligation,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

const getAuthHeaders = (token?: string, body?: BodyInit | null) => {
  const headers: Record<string, string> = {};

  if (body !== undefined && body !== null && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
};

async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
  responseType: 'auto' | 'blob' = 'auto',
): Promise<T> {
  const body = init.body;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...getAuthHeaders(token, body),
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'Request failed');
  }

  if (responseType === 'blob') {
    return (await response.blob()) as T;
  }

  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return (await response.json()) as T;
  }

  return (await response.text()) as T;
}

export const api = {
  login: async (email: string, password: string) =>
    apiRequest<LoginResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: async (token: string) => apiRequest<AuthUser>('/api/auth/me', { method: 'GET' }, token),
  listUsers: async (token: string) => apiRequest<AdminUser[]>('/api/admin/users', { method: 'GET' }, token),
  listOrganizations: async (token: string) => apiRequest<{ id: string; ein: string; legal_name: string }[]>('/api/admin/organizations', { method: 'GET' }, token),
  updateUser: async (userId: string, payload: { role: string; is_active: boolean; organization_eins?: string[] }, token: string) =>
    apiRequest<AdminUser>(`/api/admin/users/${encodeURIComponent(userId)}`, { method: 'PATCH', body: JSON.stringify(payload) }, token),
  resetUserPassword: async (userId: string, password: string, token: string) =>
    apiRequest<void>(`/api/admin/users/${encodeURIComponent(userId)}/reset-password`, { method: 'POST', body: JSON.stringify({ password }) }, token),
  listSubmissions: async (token: string) =>
    apiRequest<SubmissionListItem[]>('/api/submissions', { method: 'GET' }, token),
  reviewQueue: async (token: string, filters: { status?: string; query?: string; balanced?: boolean } = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.set('status', filters.status);
    if (filters.query) params.set('query', filters.query);
    if (filters.balanced !== undefined) params.set('balanced', String(filters.balanced));
    return apiRequest<ReviewQueueItem[]>(`/api/submissions/review-queue?${params.toString()}`, { method: 'GET' }, token);
  },
  reviewSubmission: async (submissionId: string, action: 'START_REVIEW' | 'REQUEST_REVISION' | 'APPROVE' | 'REJECT', comment: string, token: string) =>
    apiRequest<{ submission_id: string; status: string; action: string }>(
      `/api/submissions/${encodeURIComponent(submissionId)}/review`,
      { method: 'POST', body: JSON.stringify({ action, comment: comment || null }) },
      token,
    ),
  adminEditSubmission: async (submissionId: string, payload: { form_data: Record<string, unknown>; budget_lines: BudgetLine[]; comment: string }, token: string) =>
    apiRequest<{ submission_id: string; status: string; action: string }>(`/api/submissions/${encodeURIComponent(submissionId)}/admin-edit`,
      { method: 'POST', body: JSON.stringify(payload) }, token),
  listInitiatives: async (token: string) => apiRequest<InitiativeAdminItem[]>('/api/admin/initiatives', { method: 'GET' }, token),
  createInitiative: async (payload: { code: string; name: string; fiscal_year: number }, token: string) =>
    apiRequest<Record<string, unknown>>('/api/admin/initiatives', { method: 'POST', body: JSON.stringify(payload) }, token),
  updateInitiative: async (initiativeId: string, payload: { status: string; name?: string }, token: string) =>
    apiRequest<Record<string, unknown>>(`/api/admin/initiatives/${encodeURIComponent(initiativeId)}`, { method: 'PATCH', body: JSON.stringify(payload) }, token),
  createCycle: async (initiativeId: string, payload: { cycle_name: string; start_date: string; due_date: string; status: string }, token: string) =>
    apiRequest<Record<string, unknown>>(`/api/admin/initiatives/${encodeURIComponent(initiativeId)}/cycles`, { method: 'POST', body: JSON.stringify(payload) }, token),
  updateCycle: async (cycleId: string, status: string, token: string) =>
    apiRequest<Record<string, unknown>>(`/api/admin/cycles/${encodeURIComponent(cycleId)}`, { method: 'PATCH', body: JSON.stringify({ status }) }, token),
  createAssignment: async (initiativeId: string, payload: { ein: string; awarded_amount: string }, token: string) =>
    apiRequest<Record<string, unknown>>(`/api/admin/initiatives/${encodeURIComponent(initiativeId)}/assignments`, { method: 'POST', body: JSON.stringify(payload) }, token),
  createTemplate: async (initiativeId: string, payload: { schema_definition: Record<string, unknown>; is_published: boolean }, token: string) =>
    apiRequest<Record<string, unknown>>(`/api/admin/initiatives/${encodeURIComponent(initiativeId)}/templates`, { method: 'POST', body: JSON.stringify(payload) }, token),
  getAnalytics: async (token: string) => apiRequest<AdminAnalytics>('/api/admin/analytics', { method: 'GET' }, token),
  getOpenObligations: async (token: string) => apiRequest<OpenObligation[]>('/api/admin/obligations', { method: 'GET' }, token),
  rollover: async (source_fiscal_year: number, destination_fiscal_year: number, token: string) =>
    apiRequest<{ initiatives_created: number; cycles_created: number; templates_created: number; assignments_created: number }>(
      '/api/admin/rollover', { method: 'POST', body: JSON.stringify({ source_fiscal_year, destination_fiscal_year }) }, token),
  downloadExport: async (kind: 'csv' | 'xlsx', token: string) => apiRequest<Blob>(`/api/admin/exports/${kind}`, { method: 'GET' }, token, 'blob'),
  downloadAttachment: async (submissionId: string, attachmentId: string, token: string) =>
    apiRequest<Blob>(
      `/api/submissions/${encodeURIComponent(submissionId)}/attachments/${encodeURIComponent(attachmentId)}`,
      { method: 'GET' },
      token,
      'blob',
    ),
  availableReports: async (token: string) =>
    apiRequest<AvailableReport[]>('/api/submissions/available', { method: 'GET' }, token),
  createSubmission: async (report: AvailableReport, token: string) =>
    apiRequest<{ submission_id: string }>('/api/submissions', {
      method: 'POST',
      body: JSON.stringify({
        initiative_id: report.initiative_id,
        organization_id: report.organization_id,
        cycle_id: report.cycle_id,
      }),
    }, token),
  getSubmission: async (submissionId: string, token: string) =>
    apiRequest<SubmissionDetail>(`/api/submissions/${encodeURIComponent(submissionId)}`, { method: 'GET' }, token),
  validateBudget: async (lines: BudgetLine[], token: string) =>
    apiRequest<BudgetValidationSummary>(
      '/api/budgets/validate',
      {
        method: 'POST',
        body: JSON.stringify({ lines }),
      },
      token,
    ),
  saveSubmission: async (submissionId: string, payload: SaveSubmissionPayload, token: string) =>
    apiRequest<SaveSubmissionResponse>(
      `/api/submissions/${encodeURIComponent(submissionId)}/save`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      token,
    ),
  uploadAttachment: async (submissionId: string, file: File, token: string) => {
    const form = new FormData();
    form.append('file', file);

    return apiRequest<AttachmentUpload>(
      `/api/submissions/${encodeURIComponent(submissionId)}/attachments`,
      {
        method: 'POST',
        body: form,
      },
      token,
    );
  },
};
