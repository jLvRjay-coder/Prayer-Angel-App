-- Narrow backend API over HTTPS. There is no SQL execution endpoint.
-- SECURITY INVOKER preserves the caller's privileges; only service_role may
-- execute this function. Subscriber tables remain in the private schema.
GRANT USAGE ON SCHEMA angel_email_private TO service_role;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA angel_email_private TO service_role;

CREATE OR REPLACE FUNCTION public.angel_email_backend(p_action TEXT, p_data JSONB DEFAULT '{}'::JSONB)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = pg_catalog, angel_email_private
AS $backend$
DECLARE
    v_now TIMESTAMPTZ := COALESCE((p_data->>'now')::TIMESTAMPTZ, statement_timestamp());
    v_sub angel_email_private.angel_email_subscribers%ROWTYPE;
    v_delivery angel_email_private.angel_email_deliveries%ROWTYPE;
    v_count BIGINT;
    v_limit INTEGER;
    v_delivery_id TEXT;
    v_allowed BOOLEAN;
    v_rows INTEGER;
BEGIN
    IF jsonb_typeof(p_data) <> 'object' THEN
        RETURN jsonb_build_object('error','invalid_request');
    END IF;
    CASE p_action
    WHEN 'health' THEN
        PERFORM 1 FROM angel_email_private.angel_email_subscribers LIMIT 1;
        RETURN jsonb_build_object('version',1);
    WHEN 'read_subscriber' THEN
        SELECT * INTO v_sub FROM angel_email_private.angel_email_subscribers WHERE id=p_data->>'id';
        RETURN CASE WHEN FOUND THEN to_jsonb(v_sub) ELSE NULL END;
    WHEN 'active_subscribers' THEN
        RETURN (SELECT COALESCE(jsonb_agg(to_jsonb(s) ORDER BY s.id),'[]'::JSONB)
            FROM angel_email_private.angel_email_subscribers s WHERE s.status='active');
    WHEN 'request' THEN
        v_limit := (p_data->>'max_subscribers')::INTEGER;
        IF v_limit IS NULL OR v_limit < 1 OR p_data->>'email' IS NULL
           OR p_data->>'new_id' IS NULL OR p_data->>'manage_nonce' IS NULL
           OR p_data->>'confirmation_nonce' IS NULL
           OR p_data->>'delivery_time' IS NULL
           OR NOT EXISTS(SELECT 1 FROM pg_timezone_names WHERE name=p_data->>'timezone') THEN
            RETURN jsonb_build_object('error','invalid_request');
        END IF;
        PERFORM pg_advisory_xact_lock(318100014);
        SELECT * INTO v_sub FROM angel_email_private.angel_email_subscribers
            WHERE email=p_data->>'email' FOR UPDATE;
        IF FOUND AND v_sub.requested_at > v_now - INTERVAL '1 hour' THEN
            RETURN NULL;
        END IF;
        SELECT count(*) INTO v_count FROM angel_email_private.angel_email_subscribers
            WHERE status='active' OR (status='pending' AND confirmation_expires > v_now);
        v_allowed := v_sub.id IS NOT NULL AND
            (v_sub.status='active' OR (v_sub.status='pending' AND v_sub.confirmation_expires > v_now));
        IF NOT v_allowed AND v_count >= v_limit THEN
            RETURN jsonb_build_object('error','pilot_full');
        END IF;
        IF v_sub.id IS NULL THEN
            INSERT INTO angel_email_private.angel_email_subscribers
                (id,email,status,timezone,delivery_time,manage_nonce,confirmation_nonce,
                 confirmation_expires,pending_timezone,pending_time,requested_at,updated_at)
            VALUES (p_data->>'new_id',p_data->>'email','pending',p_data->>'timezone',
                (p_data->>'delivery_time')::TIME,p_data->>'manage_nonce',p_data->>'confirmation_nonce',
                v_now+INTERVAL '24 hours',p_data->>'timezone',(p_data->>'delivery_time')::TIME,v_now,v_now)
            RETURNING * INTO v_sub;
        ELSE
            UPDATE angel_email_private.angel_email_subscribers SET
                confirmation_nonce=p_data->>'confirmation_nonce', confirmation_expires=v_now+INTERVAL '24 hours',
                pending_timezone=p_data->>'timezone', pending_time=(p_data->>'delivery_time')::TIME,
                requested_at=v_now,updated_at=v_now,
                status=CASE WHEN status='unsubscribed' THEN 'pending' ELSE status END,
                manage_nonce=CASE WHEN status='unsubscribed' THEN p_data->>'manage_nonce' ELSE manage_nonce END
            WHERE id=v_sub.id RETURNING * INTO v_sub;
        END IF;
        RETURN to_jsonb(v_sub);
    WHEN 'apply_action' THEN
        SELECT * INTO v_sub FROM angel_email_private.angel_email_subscribers
            WHERE id=p_data->>'id' FOR UPDATE;
        IF NOT FOUND OR p_data->>'nonce' IS NULL
           OR (CASE WHEN p_data->>'purpose'='confirm' THEN v_sub.confirmation_nonce ELSE v_sub.manage_nonce END)
              IS DISTINCT FROM (p_data->>'nonce') THEN
            RETURN jsonb_build_object('error','invalid_link');
        END IF;
        CASE p_data->>'purpose'
        WHEN 'confirm' THEN
            IF v_sub.confirmation_expires IS NULL OR v_sub.confirmation_expires <= v_now THEN
                RETURN jsonb_build_object('error','expired_confirmation');
            END IF;
            UPDATE angel_email_private.angel_email_subscribers SET
                status='active',timezone=pending_timezone,delivery_time=pending_time,
                consent_at=requested_at,consent_version=p_data->>'consent_version',confirmed_at=v_now,
                confirmation_nonce=NULL,confirmation_expires=NULL,unsubscribed_at=NULL,updated_at=v_now
            WHERE id=v_sub.id;
        WHEN 'unsubscribe' THEN
            UPDATE angel_email_private.angel_email_subscribers SET
                status='unsubscribed',confirmation_nonce=NULL,confirmation_expires=NULL,
                unsubscribed_at=v_now,updated_at=v_now WHERE id=v_sub.id;
        WHEN 'manage' THEN
            IF v_sub.status <> 'active' THEN
                RETURN jsonb_build_object('error','not_active');
            END IF;
            IF p_data->>'delivery_time' IS NULL
               OR NOT EXISTS(SELECT 1 FROM pg_timezone_names WHERE name=p_data->>'timezone') THEN
                RETURN jsonb_build_object('error','invalid_request');
            END IF;
            UPDATE angel_email_private.angel_email_subscribers SET
                timezone=p_data->>'timezone',delivery_time=(p_data->>'delivery_time')::TIME,updated_at=v_now
            WHERE id=v_sub.id;
        ELSE
            RETURN jsonb_build_object('error','invalid_request');
        END CASE;
        RETURN 'true'::JSONB;
    WHEN 'reserve' THEN
        v_limit := (p_data->>'budget_24h')::INTEGER;
        IF v_limit IS NULL OR v_limit < 1 OR v_limit > 900
           OR p_data->>'kind' IS NULL OR p_data->>'kind' NOT IN ('daily','confirmation')
           OR p_data->>'message_key' IS NULL OR p_data->>'delivery_id' IS NULL
           OR p_data->>'attempt_id' IS NULL THEN
            RETURN jsonb_build_object('error','invalid_request');
        END IF;
        PERFORM pg_advisory_xact_lock(318100014);
        SELECT * INTO v_sub FROM angel_email_private.angel_email_subscribers
            WHERE id=p_data->>'id' FOR UPDATE;
        IF NOT FOUND OR (p_data->>'kind'='daily' AND v_sub.status <> 'active')
           OR (p_data->>'kind'='confirmation' AND
               (v_sub.confirmation_nonce IS NULL OR v_sub.confirmation_nonce IS DISTINCT FROM (p_data->>'nonce'))) THEN
            RETURN NULL;
        END IF;
        SELECT * INTO v_delivery FROM angel_email_private.angel_email_deliveries
            WHERE subscriber_id=v_sub.id AND message_key=p_data->>'message_key';
        IF FOUND AND (v_delivery.status <> 'deferred' OR v_delivery.retry_at IS NULL OR v_delivery.retry_at > v_now) THEN
            RETURN NULL;
        END IF;
        SELECT count(*) INTO v_count FROM angel_email_private.angel_email_attempts
            WHERE reserved_at > v_now - INTERVAL '24 hours';
        IF v_count >= v_limit THEN
            RETURN jsonb_build_object('error','budget_full');
        END IF;
        v_delivery_id := COALESCE(v_delivery.id,p_data->>'delivery_id');
        IF v_delivery.id IS NULL THEN
            INSERT INTO angel_email_private.angel_email_deliveries
                (id,subscriber_id,message_key,kind,nonce,status,created_at)
            VALUES (v_delivery_id,v_sub.id,p_data->>'message_key',p_data->>'kind',p_data->>'nonce','reserved',v_now);
        ELSE
            UPDATE angel_email_private.angel_email_deliveries SET status='reserved',retry_at=NULL WHERE id=v_delivery_id;
        END IF;
        INSERT INTO angel_email_private.angel_email_attempts(id,delivery_id,reserved_at)
            VALUES (p_data->>'attempt_id',v_delivery_id,v_now);
        RETURN to_jsonb(v_delivery_id);
    WHEN 'claim' THEN
        -- Lock subscriber before delivery, the same order as other mutations.
        SELECT * INTO v_delivery FROM angel_email_private.angel_email_deliveries WHERE id=p_data->>'delivery_id';
        IF NOT FOUND THEN RETURN NULL; END IF;
        SELECT * INTO v_sub FROM angel_email_private.angel_email_subscribers WHERE id=v_delivery.subscriber_id FOR UPDATE;
        SELECT * INTO v_delivery FROM angel_email_private.angel_email_deliveries WHERE id=p_data->>'delivery_id' FOR UPDATE;
        IF v_delivery.status <> 'reserved' THEN RETURN NULL; END IF;
        v_allowed := CASE WHEN v_delivery.kind='daily' THEN v_sub.status='active'
            ELSE v_sub.confirmation_nonce IS NOT NULL AND v_sub.confirmation_nonce=v_delivery.nonce
                AND v_sub.confirmation_expires > v_now END;
        IF v_allowed IS NOT TRUE THEN
            UPDATE angel_email_private.angel_email_deliveries SET status='skipped' WHERE id=v_delivery.id;
            RETURN NULL;
        END IF;
        UPDATE angel_email_private.angel_email_deliveries SET status='sending' WHERE id=v_delivery.id;
        RETURN to_jsonb(v_sub);
    WHEN 'complete' THEN
        IF p_data->>'state' IS NULL OR p_data->>'state' NOT IN ('sent','unknown','rejected','deferred','skipped') THEN
            RETURN jsonb_build_object('error','invalid_request');
        END IF;
        UPDATE angel_email_private.angel_email_deliveries SET
            status=p_data->>'state',sent_at=CASE WHEN p_data->>'state'='sent' THEN v_now ELSE NULL END,
            retry_at=CASE WHEN p_data->>'state'='deferred'
                THEN v_now+make_interval(secs=>GREATEST(60,LEAST(86400,COALESCE((p_data->>'retry_after')::INTEGER,60)))) ELSE NULL END
        WHERE id=p_data->>'delivery_id' AND status='sending';
        GET DIAGNOSTICS v_rows = ROW_COUNT;
        RETURN to_jsonb(v_rows=1);
    ELSE
        RETURN jsonb_build_object('error','invalid_request');
    END CASE;
END
$backend$;

-- Do not inherit public/default function access, including signed-in clients.
REVOKE ALL ON FUNCTION public.angel_email_backend(TEXT,JSONB) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.angel_email_backend(TEXT,JSONB) TO service_role;
NOTIFY pgrst, 'reload schema';
