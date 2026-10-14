# Draft privacy-policy addition: optional daily encouragement email

This wording is for review and completion before publishing. Identify the actual database host and retention period before enabling signup.

Daily encouragement email is optional. If you subscribe, Beyond the Message collects your email address, selected timezone, preferred delivery time, consent and confirmation timestamps, subscription status, and delivery records. We use these details to confirm your request, deliver the messages you chose, manage preferences, honor unsubscribe requests, prevent duplicate sends, and troubleshoot delivery.

Hostinger Mail sends these emails. Subscriber records are held in a private PostgreSQL database hosted by **[identify the selected provider]**. The scheduled worker runs through GitHub Actions. Credentials and subscriber records are not stored in the public application repository or uploaded as workflow artifacts. We use encrypted connections to the email API and hosted database.

Your email subscription details are separate from Angel Chat conversation state and are not included in prompts sent to OpenAI. When you choose to ask a question in Angel Chat, the app processes that conversation under its separate conversation privacy disclosure.

Daily emails start only after you confirm your email address. Each email includes unsubscribe and preference links. Opening a link alone does not make changes; use the confirmation or unsubscribe button on the page. You can stop daily emails without creating an account or continuing to use the app.

Unsubscribed records are currently retained to honor opt-out and preserve consent and delivery history. **[State the retention period and deletion process selected for the launch.]** To request deletion or ask about delivery, contact contact@beyondthemessage.org. We may verify control of the email address before making a deletion request effective.

The current sender does not add tracking pixels or per-subscriber identifiers to links that open daily teachings. Subscriber-specific signed links are used only for confirmation, unsubscribe, and delivery preferences.
