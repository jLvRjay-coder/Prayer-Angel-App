SET LOCAL search_path TO pg_catalog;
SELECT pg_catalog.pg_advisory_xact_lock(318100014);

CREATE SCHEMA IF NOT EXISTS angel_email_private;
REVOKE ALL ON SCHEMA angel_email_private FROM PUBLIC;
CREATE TABLE IF NOT EXISTS angel_email_private.angel_email_subscribers (
    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending','active','unsubscribed')),
    timezone TEXT NOT NULL, delivery_time TIME NOT NULL,
    manage_nonce TEXT NOT NULL, confirmation_nonce TEXT,
    confirmation_expires TIMESTAMPTZ, pending_timezone TEXT, pending_time TIME,
    requested_at TIMESTAMPTZ NOT NULL, consent_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ, consent_version TEXT,
    unsubscribed_at TIMESTAMPTZ, updated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS angel_email_private.angel_email_deliveries (
    id TEXT PRIMARY KEY,
    subscriber_id TEXT NOT NULL REFERENCES angel_email_private.angel_email_subscribers(id),
    message_key TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('confirmation','daily')),
    nonce TEXT, status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL, sent_at TIMESTAMPTZ, retry_at TIMESTAMPTZ,
    UNIQUE(subscriber_id, message_key)
);
CREATE TABLE IF NOT EXISTS angel_email_private.angel_email_attempts (
    id TEXT PRIMARY KEY, delivery_id TEXT NOT NULL REFERENCES angel_email_private.angel_email_deliveries(id),
    reserved_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS angel_email_attempts_time_idx ON angel_email_private.angel_email_attempts(reserved_at);
CREATE INDEX IF NOT EXISTS angel_email_attempts_delivery_idx ON angel_email_private.angel_email_attempts(delivery_id);
CREATE INDEX IF NOT EXISTS angel_email_active_idx ON angel_email_private.angel_email_subscribers(status);

-- Server connections use the table owner. No browser/client policies exist.
-- RLS denies non-owner access even if a table grant is added accidentally.
ALTER TABLE angel_email_private.angel_email_subscribers ENABLE ROW LEVEL SECURITY;
ALTER TABLE angel_email_private.angel_email_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE angel_email_private.angel_email_attempts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ALL TABLES IN SCHEMA angel_email_private FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA angel_email_private REVOKE ALL ON TABLES FROM PUBLIC;

-- Supabase roles are optional so ordinary PostgreSQL works too.
DO $private_access$
DECLARE client_role TEXT;
BEGIN
    FOR client_role IN
        SELECT rolname FROM pg_catalog.pg_roles
        WHERE rolname IN ('anon', 'authenticated', 'service_role')
    LOOP
        EXECUTE format('REVOKE ALL ON SCHEMA angel_email_private FROM %I', client_role);
        EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA angel_email_private FROM %I', client_role);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA angel_email_private REVOKE ALL ON TABLES FROM %I', client_role);
    END LOOP;
END
$private_access$;
