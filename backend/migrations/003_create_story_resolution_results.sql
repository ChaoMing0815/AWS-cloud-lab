CREATE TABLE story_result_inbox (
    job_id text PRIMARY KEY REFERENCES story_jobs (job_id) ON DELETE CASCADE,
    room_id text NOT NULL,
    round_number integer NOT NULL CHECK (round_number > 0),
    room_version integer NOT NULL CHECK (room_version >= 0),
    result_fingerprint text NOT NULL
        CHECK (result_fingerprint ~ '^[0-9a-f]{64}$'),
    result jsonb NOT NULL,
    outcome text NOT NULL CHECK (outcome IN ('applied', 'stale', 'failed')),
    room_version_after integer CHECK (room_version_after >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT story_result_inbox_state_shape CHECK (
        (outcome = 'stale' AND room_version_after IS NULL)
        OR (outcome IN ('applied', 'failed') AND room_version_after IS NOT NULL)
    )
);

CREATE TABLE story_completion_outbox (
    job_id text PRIMARY KEY REFERENCES story_result_inbox (job_id) ON DELETE CASCADE,
    ownership_token text NOT NULL,
    completion_payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    dispatched_at timestamptz
);

CREATE INDEX story_completion_outbox_pending_idx
    ON story_completion_outbox (created_at)
    WHERE dispatched_at IS NULL;
