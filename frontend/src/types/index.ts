export type Role =
  | 'COUNCIL_ADMIN'
  | 'COUNCIL_REVIEWER'
  | 'EXTERNAL_SUBMITTER'
  | 'VIEW_ONLY';

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  organization_ids: string[];
};

export type AdminUser = {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  organization_ids: string[];
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  role: Role;
  user_id: string;
  email: string;
};

export type BudgetLine = {
  category: string;
  description?: string | null;
  amount: string;
  actual_amount?: string | null;
};

export type BudgetValidationSummary = {
  line_count: number;
  total: string;
  is_valid: boolean;
  errors: string[];
};

export type SaveSubmissionPayload = {
  status: 'DRAFT' | 'SUBMITTED';
  form_data: Record<string, unknown>;
  budget_lines: BudgetLine[];
};

export type SaveSubmissionResponse = {
  submission_id: string;
  status: string;
  form_data: Record<string, unknown>;
  total_budget: string;
  is_balanced: boolean;
  line_count: number;
  is_valid: boolean;
  validation_errors: string[];
  saved_by: string;
};

export type AvailableReport = {
  initiative_id: string;
  initiative_name: string;
  organization_id: string;
  organization_name: string;
  cycle_id: string;
  cycle_name: string;
  template_version: number;
};

export type SubmissionListItem = {
  submission_id: string;
  initiative_name: string;
  organization_name: string;
  cycle_name: string;
  status: string;
  total_budget: string;
};

export type SubmissionDetail = {
  submission_id: string;
  initiative_id: string;
  organization_id: string;
  cycle_id: string;
  template_version: number;
  status: string;
  form_data: Record<string, unknown>;
  budget_lines: BudgetLine[];
  form_schema: Record<string, unknown>;
  attachments: AttachmentSummary[];
  initiative_name: string;
  organization_name: string;
  cycle_name: string;
  allocated_budget: string;
  total_budget: string;
  is_balanced: boolean;
  audit_history: { action: string; actor_role: Role; created_at: string | null; state_diff: Record<string, unknown> }[];
  versions: { version_number: number; template_version: number; submitted_at: string | null; reviewer_notes: string | null; form_snapshot: Record<string, unknown>; budget_snapshot: Record<string, unknown> }[];
};

export type ReviewQueueItem = SubmissionListItem & {
  is_balanced: boolean;
  updated_at: string | null;
  is_incomplete: boolean;
  validation_errors: string[];
  organization_ein: string;
  borough: string | null;
  fiscal_year: number;
  initiative_id: string;
  cycle_id: string;
};

export type AttachmentSummary = {
  attachment_id: string;
  submission_id: string;
  original_filename: string;
  content_type: string;
  file_size_bytes: number;
  checksum_sha256: string;
};

export type AttachmentUpload = AttachmentSummary & {
  uploaded_by: string;
};

export type InitiativeSummary = {
  id: string;
  name: string;
  code: string;
  fiscal_year: number;
  status: string;
};

export type SubmissionSummary = {
  id: string;
  initiative_name: string;
  organization_name: string;
  cycle_name: string;
  status: string;
  total_budget: string;
};

export type InitiativeAdminItem = InitiativeSummary & {
  cycles: { id: string; cycle_name: string; start_date: string; due_date: string; status: string }[];
  assignments: { organization_id: string; ein: string; legal_name: string; awarded_amount: string }[];
  templates: { id: string; version: number; is_published: boolean; schema_definition: Record<string, unknown> }[];
  lineage: { relationship_type: string; direction: 'predecessor' | 'successor'; initiative_id: string; initiative_code: string }[];
};

export type AdminAnalytics = {
  status_counts: Record<string, number>;
  allocated_budget: string;
  reported_budget: string;
  submitted_count: number;
  balanced_count: number;
  borough_totals: { borough: string; total: string }[];
};

export type OpenObligation = {
  initiative_id: string;
  initiative_name: string;
  organization_id: string;
  organization_name: string;
  borough: string | null;
  cycle_id: string;
  cycle_name: string;
  due_date: string;
  awarded_amount: string;
  is_overdue: boolean;
};
