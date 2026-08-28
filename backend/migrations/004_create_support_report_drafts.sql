CREATE TABLE support_report_drafts (
    report_id text PRIMARY KEY,
    payload_version smallint NOT NULL CHECK (payload_version = 1),
    reporter_identity_hash text NOT NULL CHECK (reporter_identity_hash ~ '^[0-9a-f]{64}$'),
    content_fingerprint text NOT NULL CHECK (content_fingerprint ~ '^[0-9a-f]{64}$'),
    idempotency_key text NOT NULL UNIQUE CHECK (idempotency_key ~ '^[0-9a-f]{64}$'),
    category text NOT NULL,
    summary text NOT NULL,
    reproduction_steps text[] NOT NULL,
    expected_behavior text NOT NULL,
    actual_behavior text NOT NULL,
    requires_human_confirmation boolean NOT NULL CHECK (requires_human_confirmation IS TRUE),
    submission_status text NOT NULL CHECK (submission_status = 'local_draft_only'),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT support_report_identity_shape CHECK (
        report_id ~ '^draft-[0-9a-f]{16}$'
        AND report_id = 'draft-' || left(idempotency_key, 16)
    ),
    CONSTRAINT support_report_payload_shape CHECK (
        category <> ''
        AND summary <> ''
        AND expected_behavior <> ''
        AND actual_behavior <> ''
        AND cardinality(reproduction_steps) >= 1
        AND array_position(reproduction_steps, NULL) IS NULL
        AND array_position(reproduction_steps, '') IS NULL
    )
);

CREATE INDEX support_report_drafts_lookup_idx
    ON support_report_drafts (idempotency_key);
