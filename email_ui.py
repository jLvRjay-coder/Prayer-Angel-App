"""Streamlit subscription screens; tokens never enter chat state or prompts."""

from datetime import time
from zoneinfo import available_timezones

import streamlit as st

from email_subscription import (
    CONSENT_TEXT, EmailService, EmailSettings, SubscriptionError, subscription_store,
)
from hostinger_email import MailUnavailable


TIMEZONES = sorted(available_timezones())


def email_settings():
    try:
        return EmailSettings.from_env()
    except (ValueError, TypeError):
        return EmailSettings()


def render_email_signup(key="daily_signup"):
    settings = email_settings()
    st.subheader("Daily encouragement in your inbox")
    if not settings.ready or not settings.signups_enabled:
        st.info("Daily email signup will open soon. You can explore the messages here in the meantime.")
        return
    st.write("One Scripture-rooted encouragement each day, with a question to carry and a link to explore it in Angel Chat.")
    st.caption("We store your email address, delivery preferences, consent, and delivery records separately from conversations. Hostinger sends these emails. Your email subscription details are not sent to OpenAI.")
    st.markdown('[Read our privacy policy](https://beyondthemessage.org/privacy-policy/)')
    with st.form(key):
        email = st.text_input("Email address", max_chars=254)
        tz = st.selectbox("Your timezone", TIMEZONES, index=TIMEZONES.index("America/Denver"))
        clock = st.time_input("Preferred delivery time", value=time(8, 0), step=1800)
        st.caption("Messages arrive in a scheduled run after your chosen time. Delivery can be delayed.")
        consent = st.checkbox(CONSENT_TEXT, value=False)
        # Honeypot: no normal user needs to complete this optional field.
        st.markdown(f'<style>.st-key-{key}_website {{ display:none !important; }}</style>', unsafe_allow_html=True)
        trap = st.text_input("Website", key=f"{key}_website")
        submitted = st.form_submit_button("Email me a confirmation link", use_container_width=True)
    if submitted:
        if trap:
            st.info("Please check your email for the next step.")
            return
        try:
            with st.spinner("Preparing your confirmation email…"):
                result = EmailService(settings).signup(email, tz, clock, consent)
            if result == "recent_request":
                st.info("If you requested a confirmation recently, please use that email. You can request another after an hour.")
            else:
                st.success("Check your inbox for the confirmation link. Daily emails start only after you confirm.")
        except SubscriptionError as error:
            st.error(str(error))
        except MailUnavailable:
            st.error("The email service is temporarily unavailable. Please try again later.")
        except Exception:
            st.error("Email signup is temporarily unavailable. Please try again later.")


def render_email_action(goto):
    st.title("Daily email encouragement")
    if st.session_state.get("email_action_result"):
        st.success(st.session_state.pop("email_action_result"))
    token = st.query_params.get("token", "")
    action = st.query_params.get("action", "")
    if not token or not action:
        render_email_signup("email_page_signup")
    elif action not in {"confirm", "unsubscribe", "manage"}:
        st.error("This email link could not be found.")
    else:
        settings = email_settings()
        if not settings.storage_ready:
            st.error("Email preferences are temporarily unavailable. Please try again later or contact contact@beyondthemessage.org.")
        else:
            try:
                store = subscription_store(settings)
                row = store.token_subscriber(token, action)
                if action == "manage":
                    with st.form("email_preferences"):
                        tz = st.selectbox("Your timezone", TIMEZONES, index=TIMEZONES.index(row["timezone"]))
                        clock = st.time_input("Preferred delivery time", value=row["delivery_time"], step=1800)
                        submitted = st.form_submit_button("Save email preferences", use_container_width=True)
                else:
                    tz, clock = None, None
                    st.write("Confirm your email address to start daily encouragement." if action == "confirm" else "Unsubscribe from daily encouragement emails.")
                    submitted = st.button("Confirm my email" if action == "confirm" else "Unsubscribe", key="email_confirm_action", use_container_width=True)
                # Viewing a link never activates or cancels a subscription.
                # This explicit click also prevents email scanners from doing so.
                if submitted:
                    store.apply_action(token, action, tz, clock)
                    st.session_state.email_action_result = {
                        "confirm": "Your email is confirmed. You are subscribed to daily encouragement.",
                        "unsubscribe": "You are unsubscribed from daily encouragement emails.",
                        "manage": "Your email preferences have been saved.",
                    }[action]
                    st.query_params.pop("token", None)
                    st.query_params.pop("action", None)
                    st.rerun()
            except SubscriptionError as error:
                st.error(str(error))
            except Exception:
                st.error("Email preferences are temporarily unavailable. Please try again later or contact contact@beyondthemessage.org.")
    if st.button("Back to Home", key="email_back_home", use_container_width=True):
        goto("home")
