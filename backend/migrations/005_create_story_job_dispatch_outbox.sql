CREATE TABLE story_job_dispatch_outbox (
    job_id text PRIMARY KEY REFERENCES story_jobs (job_id) ON DELETE CASCADE,
    message_payload jsonb NOT NULL,
    status text NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'publishing', 'dispatched')
    ),
    lease_token text,
    lease_expires_at timestamptz,
    attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    dispatched_at timestamptz,
    CONSTRAINT story_job_dispatch_outbox_payload_shape CHECK (
        jsonb_typeof(message_payload) = 'object'
        AND jsonb_object_length(message_payload) = 2
        AND message_payload ->> 'schema_version' = '1'
        AND message_payload ->> 'job_id' = job_id
    ),
    CONSTRAINT story_job_dispatch_outbox_state_shape CHECK (
        (
            status = 'pending'
            AND lease_token IS NULL
            AND lease_expires_at IS NULL
            AND dispatched_at IS NULL
        )
        OR (
            status = 'publishing'
            AND lease_token IS NOT NULL
            AND lease_expires_at IS NOT NULL
            AND dispatched_at IS NULL
        )
        OR (
            status = 'dispatched'
            AND lease_token IS NULL
            AND lease_expires_at IS NULL
            AND dispatched_at IS NOT NULL
        )
    )
);

CREATE INDEX story_job_dispatch_outbox_claimable_idx
    ON story_job_dispatch_outbox (status, lease_expires_at, created_at);

INSERT INTO story_job_dispatch_outbox (job_id, message_payload)
SELECT
    job_id,
    jsonb_build_object('schema_version', 1, 'job_id', job_id)
FROM story_jobs
WHERE status = 'pending'
ON CONFLICT (job_id) DO NOTHING;
