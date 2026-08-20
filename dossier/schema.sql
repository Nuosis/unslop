-- One route ships in the image; dossiers are rows, so a new one needs no deploy.
CREATE TABLE IF NOT EXISTS dossiers (
    id          VARCHAR(32) PRIMARY KEY,
    session_id  VARCHAR(128) NOT NULL,
    title       TEXT NOT NULL,
    html        TEXT NOT NULL,
    meta        JSONB NOT NULL DEFAULT '{}'::jsonb,
    pinned      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_dossiers_session ON dossiers (session_id);
CREATE INDEX IF NOT EXISTS ix_dossiers_expiry  ON dossiers (expires_at) WHERE NOT pinned;
