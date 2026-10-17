# Live website email test — October 16, 2026

All times and dates in this record refer to America/Denver. This records the authorized test, not approval to start daily delivery.

## Passed

- Jamie authorized temporarily opening website signup while automatic daily delivery stays off. Jamie reported saving the two public configuration variables with signup enabled and delivery disabled.
- The live signup page at https://angel.beyondthemessage.org/?v=email showed the email, timezone, delivery-time, consent, and confirmation-request controls.
- The website sent its confirmation email. Jamie confirmed and supplied the green banner: "Your email is confirmed. You are subscribed to daily encouragement."
- When a preferences link was reported expired, the latest email's management link was checked. Its purpose and expiry were correct, it matched the confirmed subscriber's current management nonce, and its recipient matched that subscription.
- Jamie explicitly requested another link. One separate preferences-only email reused that current valid link, went only to the existing test inbox, and preserved the business footer and unsubscribe link. Hostinger returned HTTP 204; the Sent copy was verified. The send did not renew confirmation, reactivate a subscriber, or change preferences.
- Jamie completed the preference-test steps and supplied the green banner: "Your email preferences have been saved." A targeted read-only database check verified a changed delivery time was stored under America/Denver and that the subscription remained active and confirmed.
- Jamie completed unsubscribe and supplied the green banner: "You are unsubscribed from daily encouragement emails." A targeted read-only check confirmed the stored unsubscribe timestamp and cleared confirmation nonce. Aggregate counts are one unsubscribed record, zero active subscribers, and zero pending subscribers.
- Jamie restored both public email enable flags to false after testing. The live website was checked and displays "Daily email signup will open soon. You can explore the messages here in the meantime." The signup form is no longer offered. Automatic daily delivery remains disabled.

## Remaining

- Complete the Android privacy/Data safety review, approve the pilot dates/content, and merge the reviewed worker before starting scheduled delivery.

The earlier October 15 private test included one confirmation and one devotional, followed by unsubscribe. Today's test independently exercised website signup, confirmation sending, confirmation, saved preferences, and unsubscribe. The current test subscription is unsubscribed. The preferences-only resend was a separate authorized administrative email, not another devotional or a scheduled delivery.

No recipient address, business mailing address, signed link, nonce, or credential is copied into this public record. The runtime deployment and all devotional approval flags are unchanged by this documentation update.
