-- Fixed health metadata only. No email address, token, or chat text is stored here.
CREATE TABLE IF NOT EXISTS public.angel_email_scheduler_health (
    singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
    checked_at TIMESTAMPTZ NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('ok','failed','disabled','not_configured')),
    counters JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_commit TEXT NOT NULL DEFAULT ''
);
ALTER TABLE public.angel_email_scheduler_health ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.angel_email_scheduler_health FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.angel_email_scheduler_health TO service_role;

CREATE OR REPLACE FUNCTION public.angel_email_scheduler_heartbeat(
    p_state TEXT, p_counters JSONB DEFAULT '{}'::jsonb, p_source TEXT DEFAULT ''
) RETURNS VOID LANGUAGE SQL SECURITY INVOKER SET search_path = '' AS $$
    INSERT INTO public.angel_email_scheduler_health(singleton,checked_at,state,counters,source_commit)
    VALUES(TRUE,pg_catalog.now(),p_state,
        pg_catalog.jsonb_build_object(
            'sent', COALESCE((p_counters->>'sent')::int,0),
            'already_handled', COALESCE((p_counters->>'already_handled')::int,0),
            'not_due', COALESCE((p_counters->>'not_due')::int,0),
            'disabled', COALESCE((p_counters->>'disabled')::int,0),
            'budget_full', COALESCE((p_counters->>'budget_full')::int,0),
            'unknown', COALESCE((p_counters->>'unknown')::int,0),
            'rejected', COALESCE((p_counters->>'rejected')::int,0),
            'deferred', COALESCE((p_counters->>'deferred')::int,0)
        ),
        CASE WHEN p_source ~ '^[0-9a-f]{40}$' THEN p_source ELSE '' END)
    ON CONFLICT(singleton) DO UPDATE SET checked_at=EXCLUDED.checked_at,
        state=EXCLUDED.state,counters=EXCLUDED.counters,source_commit=EXCLUDED.source_commit;
$$;
REVOKE ALL ON FUNCTION public.angel_email_scheduler_heartbeat(TEXT,JSONB,TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.angel_email_scheduler_heartbeat(TEXT,JSONB,TEXT) TO service_role;

CREATE EXTENSION IF NOT EXISTS pg_cron WITH SCHEMA pg_catalog;
CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;
-- Network functions are used only by the database job owner.
REVOKE ALL ON SCHEMA net FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA net FROM PUBLIC, anon, authenticated;

-- This public health check carries no token, subscriber data, or send action.
SELECT cron.schedule('angel-app-health-check','*/5 * * * *',
    $job$SELECT net.http_get(url:='https://angel.beyondthemessage.org/_stcore/health',timeout_milliseconds:=10000);$job$);
