-- Synthetic local-demo dataset for NYC Council Initiative Reporting System.
-- Run once, after database/schema.sql, against an empty council_irs_db schema.
-- Passwords below are demo-only bcrypt hashes; see README.md for local logins.

USE council_irs_db;

START TRANSACTION;

INSERT INTO organizations (id, ein, legal_name, org_type, borough, status) VALUES
    ('org-001', '13-1234567', 'Harlem Community Arts Coalition', 'CBO', 'Manhattan', 'ACTIVE'),
    ('org-002', '11-7654321', 'Queens Youth Literacy Initiative', 'CBO', 'Queens', 'ACTIVE'),
    ('org-003', '12-9876543', 'Department of Youth & Community Development', 'CITY_AGENCY', 'Citywide', 'ACTIVE'),
    ('org-004', '14-5551234', 'Bronx Environmental & Green Jobs Network', 'CBO', 'Bronx', 'ACTIVE'),
    ('org-005', '15-4449876', 'Brooklyn Legal & Tenant Advocacy Center', 'CBO', 'Brooklyn', 'ACTIVE'),
    ('org-006', '16-3332211', 'Staten Island Green Futures Collaborative', 'CBO', 'Staten Island', 'ACTIVE');

INSERT INTO initiatives (id, code, name, fiscal_year, status) VALUES
    ('init-101', 'INIT-YOUTH-01', 'Youth Development & Literacy Initiative', 2026, 'ACTIVE'),
    ('init-102', 'INIT-ARTS-02', 'Cultural & Community Arts Grant', 2026, 'ACTIVE'),
    ('init-103', 'INIT-GREEN-03', 'Urban Ecology & Green Infrastructure Fund', 2026, 'ACTIVE'),
    ('init-201', 'INIT-YOUTH-01-FY25', 'Youth Afterschool Enhancement Program (Legacy)', 2025, 'COMBINED');

INSERT INTO initiative_relationships (predecessor_id, successor_id, relationship_type) VALUES
    ('init-201', 'init-101', 'COMBINED');

INSERT INTO reporting_cycles (id, initiative_id, cycle_name, start_date, due_date, status) VALUES
    ('cyc-101-mid', 'init-101', 'FY2026 Mid-Year Reporting', '2026-07-01', '2026-11-15', 'OPEN'),
    ('cyc-101-final', 'init-101', 'FY2026 Final Reporting', '2026-12-01', '2027-04-30', 'UPCOMING'),
    ('cyc-102-mid', 'init-102', 'FY2026 Mid-Year Reporting', '2026-07-01', '2026-11-15', 'OPEN'),
    ('cyc-102-final', 'init-102', 'FY2026 Final Reporting', '2026-12-01', '2027-04-30', 'UPCOMING'),
    -- Deliberately overdue but still open to exercise overdue triage and completion.
    ('cyc-103-mid', 'init-103', 'FY2026 Mid-Year Reporting', '2026-07-01', '2026-09-30', 'OPEN'),
    ('cyc-103-final', 'init-103', 'FY2026 Final Reporting', '2026-12-01', '2027-04-30', 'UPCOMING'),
    ('cyc-201-final', 'init-201', 'FY2025 Final Reporting', '2025-12-01', '2026-04-30', 'CLOSED');

INSERT INTO initiative_organizations (initiative_id, organization_id, awarded_amount) VALUES
    ('init-101', 'org-001', 50000.00),
    ('init-101', 'org-002', 75000.00),
    ('init-102', 'org-003', 60000.00),
    ('init-103', 'org-004', 60000.00),
    ('init-102', 'org-005', 25000.00),
    ('init-101', 'org-005', 40000.00),
    ('init-101', 'org-006', 45000.00),
    ('init-103', 'org-006', 55000.00);

INSERT INTO form_templates (id, initiative_id, version, schema_definition, is_published) VALUES
    ('tpl-101-v1', 'init-101', 1,
     JSON_OBJECT(
       'title', 'Youth Literacy & Development Report',
       'budget_reconciliation', JSON_OBJECT('target', 'allocated_budget'),
       'sections', JSON_ARRAY(JSON_OBJECT(
         'id', 'program_metrics', 'name', 'Programmatic Metrics',
         'fields', JSON_ARRAY(
           JSON_OBJECT('id', 'participants_served', 'label', 'Youth Participants Served', 'type', 'number', 'required', TRUE),
           JSON_OBJECT('id', 'borough', 'label', 'Primary Borough', 'type', 'dropdown', 'options', JSON_ARRAY('Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'), 'required', TRUE),
           JSON_OBJECT('id', 'program_narrative', 'label', 'Narrative of Activities', 'type', 'textarea', 'required', TRUE, 'max_words', 300)
         )
       ))
     ), TRUE),
    ('tpl-102-v1', 'init-102', 1,
     JSON_OBJECT(
       'title', 'Cultural & Community Arts Report',
       'budget_reconciliation', JSON_OBJECT('target', 'allocated_budget'),
       'sections', JSON_ARRAY(JSON_OBJECT(
         'id', 'arts_metrics', 'name', 'Cultural Engagement',
         'fields', JSON_ARRAY(
           JSON_OBJECT('id', 'workshops_held', 'label', 'Public Workshops Hosted', 'type', 'number', 'required', TRUE),
           JSON_OBJECT('id', 'community_impact', 'label', 'Community Impact Narrative', 'type', 'textarea', 'required', TRUE, 'max_words', 300)
         )
       ))
     ), TRUE),
    ('tpl-103-v1', 'init-103', 1,
     JSON_OBJECT(
       'title', 'Urban Ecology & Green Jobs Report',
       'budget_reconciliation', JSON_OBJECT('target', 'allocated_budget'),
       'sections', JSON_ARRAY(JSON_OBJECT(
         'id', 'green_metrics', 'name', 'Environmental Benchmarks',
         'fields', JSON_ARRAY(
           JSON_OBJECT('id', 'trees_planted', 'label', 'Trees or Native Plants Maintained', 'type', 'number', 'required', TRUE),
           JSON_OBJECT('id', 'trainees_graduated', 'label', 'Green Job Apprentices Graduated', 'type', 'number', 'required', TRUE)
         )
       ))
     ), TRUE),
    ('tpl-101-v2', 'init-101', 2,
     JSON_OBJECT(
       'title', 'Youth Literacy & Development Report — Updated',
       'budget_reconciliation', JSON_OBJECT('target', 'allocated_budget'),
       'sections', JSON_ARRAY(JSON_OBJECT(
         'id', 'program_metrics', 'name', 'Programmatic Metrics',
         'fields', JSON_ARRAY(
           JSON_OBJECT('id', 'participants_served', 'label', 'Youth Participants Served', 'type', 'number', 'required', TRUE),
           JSON_OBJECT('id', 'borough', 'label', 'Primary Borough', 'type', 'dropdown', 'options', JSON_ARRAY('Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'), 'required', TRUE),
           JSON_OBJECT('id', 'program_narrative', 'label', 'Narrative of Activities', 'type', 'textarea', 'required', TRUE, 'max_words', 300),
           JSON_OBJECT('id', 'additional_outcomes', 'label', 'Additional Outcomes', 'type', 'textarea', 'required', FALSE, 'max_words', 150)
         )
       ))
     ), FALSE);

INSERT INTO users (id, email, password_hash, full_name, role, is_active) VALUES
    ('usr-admin', 'admin@council.nyc.gov', '$2b$12$korhaptqctLNyv0W0Iu2J.AzFova7bzqWyPcdHHSnampU5PRA2dFu', 'Council Finance Admin', 'COUNCIL_ADMIN', TRUE),
    ('usr-reviewer', 'reviewer@council.nyc.gov', '$2b$12$MBhdaPLJ0CBJZbBXza3h.Oh5i2eTZGOEnxodfZALobde0y7hP4cj6', 'Council Finance Reviewer', 'COUNCIL_REVIEWER', TRUE),
    ('usr-viewer', 'viewer@council.nyc.gov', '$2b$12$MBhdaPLJ0CBJZbBXza3h.Oh5i2eTZGOEnxodfZALobde0y7hP4cj6', 'Council Finance Viewer', 'VIEW_ONLY', TRUE),
    ('usr-sub-harlem', 'submitter.harlem@cbo.org', '$2b$12$0phRZpLJuKrqfD4NuIjsW.YjDi6Q/0DJxh2juHyyospx4GGU0WeQO', 'Harlem Submitter', 'EXTERNAL_SUBMITTER', TRUE),
    ('usr-sub-queens', 'submitter.queens@cbo.org', '$2b$12$0phRZpLJuKrqfD4NuIjsW.YjDi6Q/0DJxh2juHyyospx4GGU0WeQO', 'Queens Submitter', 'EXTERNAL_SUBMITTER', TRUE),
    ('usr-sub-agency', 'submitter.agency@nyc.gov', '$2b$12$0phRZpLJuKrqfD4NuIjsW.YjDi6Q/0DJxh2juHyyospx4GGU0WeQO', 'Agency Submitter', 'EXTERNAL_SUBMITTER', TRUE),
    ('usr-sub-bronx', 'submitter.bronx@cbo.org', '$2b$12$0phRZpLJuKrqfD4NuIjsW.YjDi6Q/0DJxh2juHyyospx4GGU0WeQO', 'Bronx Submitter', 'EXTERNAL_SUBMITTER', TRUE),
    ('usr-sub-brooklyn', 'submitter.brooklyn@cbo.org', '$2b$12$0phRZpLJuKrqfD4NuIjsW.YjDi6Q/0DJxh2juHyyospx4GGU0WeQO', 'Brooklyn Submitter', 'EXTERNAL_SUBMITTER', TRUE),
    ('usr-sub-staten-island', 'submitter.statenisland@cbo.org', '$2b$12$0phRZpLJuKrqfD4NuIjsW.YjDi6Q/0DJxh2juHyyospx4GGU0WeQO', 'Staten Island Submitter', 'EXTERNAL_SUBMITTER', TRUE);

INSERT INTO user_organizations (user_id, organization_id, is_primary) VALUES
    ('usr-sub-harlem', 'org-001', TRUE),
    ('usr-sub-queens', 'org-002', TRUE),
    ('usr-sub-agency', 'org-003', TRUE),
    ('usr-sub-bronx', 'org-004', TRUE),
    ('usr-sub-brooklyn', 'org-005', TRUE),
    ('usr-sub-staten-island', 'org-006', TRUE);

INSERT INTO submissions
    (id, initiative_id, organization_id, cycle_id, template_version, status,
     form_data, allocated_budget, total_budget, is_balanced, created_by)
VALUES
    ('sub-draft', 'init-101', 'org-001', 'cyc-101-mid', 1, 'DRAFT',
     -- Intentionally incomplete and $5,000 short; the submitter can finish it in the editor.
     JSON_OBJECT('participants_served', 80, 'borough', 'Manhattan'),
     50000.00, 45000.00, FALSE, 'usr-sub-harlem'),
    ('sub-submitted', 'init-101', 'org-002', 'cyc-101-mid', 1, 'SUBMITTED',
     JSON_OBJECT('participants_served', 145, 'borough', 'Queens', 'program_narrative', 'Delivered literacy workshops across Queens.'),
     75000.00, 75000.00, TRUE, 'usr-sub-queens'),
    ('sub-review', 'init-102', 'org-003', 'cyc-102-mid', 1, 'IN_REVIEW',
     JSON_OBJECT('workshops_held', 18, 'community_impact', 'Hosted public workshops and community showcases.'),
     60000.00, 60000.00, TRUE, 'usr-sub-agency'),
    ('sub-revision', 'init-103', 'org-004', 'cyc-103-mid', 1, 'REVISION_REQUESTED',
     JSON_OBJECT('trees_planted', 420, 'trainees_graduated', 24),
     60000.00, 60000.00, TRUE, 'usr-sub-bronx'),
    ('sub-approved', 'init-102', 'org-005', 'cyc-102-mid', 1, 'APPROVED',
     JSON_OBJECT('workshops_held', 12, 'community_impact', 'Residents attended arts workshops and a gallery showcase.'),
     25000.00, 25000.00, TRUE, 'usr-sub-brooklyn'),
    -- Second repairable case: incomplete form and $1,000 below the $45,000 award.
    ('sub-edge-draft', 'init-101', 'org-006', 'cyc-101-mid', 1, 'DRAFT',
     JSON_OBJECT('participants_served', 37, 'borough', 'Staten Island'),
     45000.00, 44000.00, FALSE, 'usr-sub-staten-island'),
    -- Seeded historical anomaly for reviewer triage; new unbalanced submissions are rejected by the API.
    ('sub-flagged', 'init-101', 'org-005', 'cyc-101-mid', 1, 'SUBMITTED',
     JSON_OBJECT('participants_served', 62, 'borough', 'Brooklyn', 'program_narrative', 'Literacy programming expanded to two neighborhood sites.'),
     40000.00, 32000.00, FALSE, 'usr-sub-brooklyn');

INSERT INTO budget_line_items
    (id, submission_id, line_number, category, description, budgeted_amount, actual_amount)
VALUES
    ('li-draft-1', 'sub-draft', 1, 'Personnel', 'Youth program coordinator', 30000.00, 12000.00),
    ('li-draft-2', 'sub-draft', 2, 'OTPS - Supplies', 'Books and literacy kits', 15000.00, 5000.00),
    ('li-draft-3', 'sub-draft', 3, 'OTPS - Other', 'Placeholder row to complete or remove', 0.00, 0.00),
    ('li-submit-1', 'sub-submitted', 1, 'Personnel', 'Lead literacy instructor', 45000.00, 45000.00),
    ('li-submit-2', 'sub-submitted', 2, 'OTPS - Supplies', 'Books and program materials', 20000.00, 19000.00),
    ('li-submit-3', 'sub-submitted', 3, 'OTPS - Space', 'Community room rental', 10000.00, 10000.00),
    ('li-review-1', 'sub-review', 1, 'Personnel', 'Agency program staff', 35000.00, 30000.00),
    ('li-review-2', 'sub-review', 2, 'OTPS - Services', 'Community services', 15000.00, 12000.00),
    ('li-review-3', 'sub-review', 3, 'OTPS - Supplies', 'Program materials', 10000.00, 9000.00),
    ('li-revision-1', 'sub-revision', 1, 'Personnel', 'Green jobs coordinator', 40000.00, 35000.00),
    ('li-revision-2', 'sub-revision', 2, 'OTPS - Equipment', 'Gardening and safety equipment', 20000.00, 18500.00),
    ('li-approved-1', 'sub-approved', 1, 'Personnel', 'Community arts instructor', 18000.00, 18000.00),
    ('li-approved-2', 'sub-approved', 2, 'OTPS - Materials', 'Art supplies and canvas', 7000.00, 7000.00),
    ('li-edge-draft-1', 'sub-edge-draft', 1, 'Personnel', 'Green programs coordinator', 30000.00, 28000.00),
    ('li-edge-draft-2', 'sub-edge-draft', 2, 'OTPS - Supplies', 'Native plant and safety supplies', 14000.00, 9000.00),
    ('li-flagged-1', 'sub-flagged', 1, 'Personnel', 'Part-time literacy instructor', 24000.00, 12000.00),
    ('li-flagged-2', 'sub-flagged', 2, 'OTPS - Supplies', 'Reading materials for participants', 8000.00, 3500.00);

INSERT INTO submission_versions
    (id, submission_id, version_number, template_version, form_snapshot, budget_snapshot, submitted_by, reviewer_notes)
VALUES
    ('ver-submitted-1', 'sub-submitted', 1, 1,
     JSON_OBJECT('participants_served', 145, 'borough', 'Queens', 'program_narrative', 'Delivered literacy workshops across Queens.'),
     JSON_OBJECT('lines', JSON_ARRAY(
       JSON_OBJECT('line_number', 1, 'category', 'Personnel', 'amount', '45000.00'),
       JSON_OBJECT('line_number', 2, 'category', 'OTPS - Supplies', 'amount', '20000.00'),
       JSON_OBJECT('line_number', 3, 'category', 'OTPS - Space', 'amount', '10000.00')
     ), 'total', '75000.00'), 'usr-sub-queens', NULL),
    ('ver-review-1', 'sub-review', 1, 1,
     JSON_OBJECT('workshops_held', 18, 'community_impact', 'Hosted public workshops and community showcases.'),
     JSON_OBJECT('lines', JSON_ARRAY(
       JSON_OBJECT('line_number', 1, 'category', 'Personnel', 'amount', '35000.00'),
       JSON_OBJECT('line_number', 2, 'category', 'OTPS - Services', 'amount', '15000.00'),
       JSON_OBJECT('line_number', 3, 'category', 'OTPS - Supplies', 'amount', '10000.00')
     ), 'total', '60000.00'), 'usr-sub-agency', 'Ready for reviewer decision.'),
    ('ver-revision-1', 'sub-revision', 1, 1,
     JSON_OBJECT('trees_planted', 420, 'trainees_graduated', 24),
     JSON_OBJECT('lines', JSON_ARRAY(
       JSON_OBJECT('line_number', 1, 'category', 'Personnel', 'amount', '40000.00'),
       JSON_OBJECT('line_number', 2, 'category', 'OTPS - Equipment', 'amount', '20000.00')
     ), 'total', '60000.00'), 'usr-sub-bronx', 'Please clarify the equipment costs before resubmitting.'),
    ('ver-approved-1', 'sub-approved', 1, 1,
     JSON_OBJECT('workshops_held', 12, 'community_impact', 'Residents attended arts workshops and a gallery showcase.'),
     JSON_OBJECT('lines', JSON_ARRAY(
       JSON_OBJECT('line_number', 1, 'category', 'Personnel', 'amount', '18000.00'),
       JSON_OBJECT('line_number', 2, 'category', 'OTPS - Materials', 'amount', '7000.00')
     ), 'total', '25000.00'), 'usr-sub-brooklyn', 'Approved by Council Finance Reviewer.'),
    ('ver-flagged-1', 'sub-flagged', 1, 1,
     JSON_OBJECT('participants_served', 62, 'borough', 'Brooklyn', 'program_narrative', 'Literacy programming expanded to two neighborhood sites.'),
     JSON_OBJECT('lines', JSON_ARRAY(
       JSON_OBJECT('line_number', 1, 'category', 'Personnel', 'amount', '24000.00'),
       JSON_OBJECT('line_number', 2, 'category', 'OTPS - Supplies', 'amount', '8000.00')
     ), 'total', '32000.00'), 'usr-sub-brooklyn', 'Seeded flagged case: $8,000 below the $40,000 allocation.');

INSERT INTO audit_logs (submission_id, action, actor_id, actor_role, state_diff) VALUES
    ('sub-draft', 'DRAFT_CREATED', 'usr-sub-harlem', 'EXTERNAL_SUBMITTER', JSON_OBJECT('status', 'DRAFT', 'is_balanced', FALSE)),
    ('sub-submitted', 'REPORT_SUBMITTED', 'usr-sub-queens', 'EXTERNAL_SUBMITTER', JSON_OBJECT('status', 'SUBMITTED', 'total_budget', 75000.00)),
    ('sub-review', 'REVIEW_STARTED', 'usr-reviewer', 'COUNCIL_REVIEWER', JSON_OBJECT('status', 'IN_REVIEW')),
    ('sub-revision', 'REVISION_REQUESTED', 'usr-reviewer', 'COUNCIL_REVIEWER', JSON_OBJECT('status', 'REVISION_REQUESTED')),
    ('sub-approved', 'REPORT_APPROVED', 'usr-admin', 'COUNCIL_ADMIN', JSON_OBJECT('status', 'APPROVED')),
    ('sub-edge-draft', 'DRAFT_CREATED', 'usr-sub-staten-island', 'EXTERNAL_SUBMITTER', JSON_OBJECT('status', 'DRAFT', 'total_budget', 44000.00, 'allocated_budget', 45000.00, 'is_balanced', FALSE)),
    ('sub-flagged', 'REPORT_SUBMITTED', 'usr-sub-brooklyn', 'EXTERNAL_SUBMITTER', JSON_OBJECT('status', 'SUBMITTED', 'total_budget', 32000.00, 'allocated_budget', 40000.00, 'is_balanced', FALSE));

COMMIT;
