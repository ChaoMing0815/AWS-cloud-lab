CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rooms (
    id text PRIMARY KEY,
    room_code text NOT NULL UNIQUE,
    status text NOT NULL,
    version integer NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS rooms_status_idx ON rooms (status);

INSERT INTO schema_migrations (version)
VALUES ('001_create_rooms')
ON CONFLICT (version) DO NOTHING;
