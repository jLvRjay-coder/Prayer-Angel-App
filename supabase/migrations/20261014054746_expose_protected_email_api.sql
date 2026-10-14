-- Expose the backend RPC schema, not the subscriber schema.
-- Database role configuration takes precedence over Dashboard exposed-schema settings.
ALTER ROLE authenticator SET pgrst.db_schemas = 'public';
NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';
