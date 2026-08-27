CREATE TABLE story_jobs (
    job_id text PRIMARY KEY,
    idempotency_key text NOT NULL UNIQUE,
    operation text NOT NULL CHECK (operation IN ('resolve-round')),
    room_id text NOT NULL,
    round_number integer NOT NULL CHECK (round_number > 0),
    room_version integer NOT NULL CHECK (room_version >= 0),
    payload jsonb NOT NULL,
    status text NOT NULL CHECK (
        status IN ('pending', 'claimed', 'completed', 'dead-lettered')
    ),
    claimed_by text,
    ownership_token text,
    lease_expires_at timestamptz,
    attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    result jsonb,
    terminal_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    dead_lettered_at timestamptz,
    CONSTRAINT story_jobs_state_shape CHECK (
        (
            status = 'pending'
            AND claimed_by IS NULL
            AND ownership_token IS NULL
            AND lease_expires_at IS NULL
            AND result IS NULL
            AND terminal_error IS NULL
            AND completed_at IS NULL
            AND dead_lettered_at IS NULL
        )
        OR (
            status = 'claimed'
            AND claimed_by IS NOT NULL
            AND ownership_token IS NOT NULL
            AND lease_expires_at IS NOT NULL
            AND result IS NULL
            AND terminal_error IS NULL
            AND completed_at IS NULL
            AND dead_lettered_at IS NULL
        )
        OR (
            status = 'completed'
            AND claimed_by IS NOT NULL
            AND ownership_token IS NOT NULL
            AND lease_expires_at IS NULL
            AND result IS NOT NULL
            AND terminal_error IS NULL
            AND completed_at IS NOT NULL
            AND dead_lettered_at IS NULL
        )
        OR (
            status = 'dead-lettered'
            AND claimed_by IS NULL
            AND ownership_token IS NULL
            AND lease_expires_at IS NULL
            AND result IS NULL
            AND terminal_error IS NOT NULL
            AND completed_at IS NULL
            AND dead_lettered_at IS NOT NULL
        )
    )
);

CREATE UNIQUE INDEX story_jobs_ownership_token_unique
    ON story_jobs (ownership_token)
    WHERE ownership_token IS NOT NULL;

CREATE INDEX story_jobs_claimable_idx
    ON story_jobs (status, lease_expires_at, created_at);

CREATE INDEX story_jobs_room_round_idx
    ON story_jobs (room_id, round_number, room_version);
