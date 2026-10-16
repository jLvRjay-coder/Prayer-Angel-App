# Daily encouragement email — proposed privacy-policy addition

**Owner review note — omit this note when publishing.** This is a concrete draft for the pilot, not a published policy update. It describes the current retention behavior: records remain stored after unsubscribe and are removed manually following a verified deletion request or a retention review. No automatic deletion period is implemented. Jamie must approve that retention approach before public signup; adopting a fixed deletion deadline would require implementing and testing the corresponding cleanup process. Keep the existing website's conversation/OpenAI disclosures alongside this email section. See `PILOT_LAUNCH.md` for the proposed calendar and remaining checks.

---

## Optional daily encouragement email

Daily encouragement email is optional. If you subscribe, Beyond the Message collects your email address, selected timezone, preferred delivery time, consent and confirmation timestamps, subscription status, and delivery records. We use these details to confirm your request, deliver the messages you chose, manage preferences, honor unsubscribe requests, prevent duplicate sends, and troubleshoot delivery.

We use **Hostinger Mail** to send the emails, **Supabase** to hold subscription and delivery records, **Hugging Face** to host Angel Chat, and **GitHub Actions** to run scheduled delivery. Subscription records and credentials are not placed in the public application repository or public workflow artifacts. Connections to the email service and hosted subscription database are encrypted in transit.

Your email subscription details are separate from Angel Chat conversation state and are not included in prompts sent to OpenAI. When you choose to ask a question in Angel Chat, the app processes that conversation under its separate conversation privacy disclosure.

Daily emails start only after you confirm your email address. Each email includes unsubscribe and preference links. Opening a link alone does not make changes; use the confirmation or unsubscribe button on the page. You can stop daily emails without creating an account or continuing to use the app.

## Retention and deletion requests

We keep your subscription record while you are subscribed so we can deliver and manage the emails you requested. Unsubscribing stops future scheduled delivery; it does not automatically delete your record. We retain the subscription, consent, opt-out, and delivery history to respect your choice, prevent duplicate or unintended sends, and investigate delivery problems. Pending and unsubscribed records currently remain stored until manually removed following a verified deletion request or a retention review. There is no automatic deletion window for this service.

To request deletion of your subscription data or ask about delivery, email **contact@beyondthemessage.org**. We may ask you to verify control of the affected email address. Requests are handled manually: we stop the subscription, review the related records, and remove subscription and delivery records that no longer need to be retained. We will explain any information that must remain and why. Deleting subscription data does not recall emails already delivered to your inbox or automatically delete copies held by email providers under their own retention practices.

## Images and links

We do not add email-open tracking pixels or subscriber identifiers to links that open daily teachings. Branded emails may load a shared logo image hosted with Angel Chat on Hugging Face. That image URL does not contain your email address or subscription identifier. The written devotional remains available when images are blocked.

Subscriber-specific signed links are used for confirmation, unsubscribe, and delivery preferences. Links to the Google Play Store or a future YouTube recording open those services, whose own privacy practices apply. Your email subscription details are not included in those public links.
