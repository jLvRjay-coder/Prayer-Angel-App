# Daily Encouragement pilot — review draft

Proposed first week: **October 19–25, 2026**, beginning Monday. These dates are prepared in the preview catalog; they are not authorization to send. Every entry remains `approved_for_delivery=False`, both public email enable flags remain off, and the pull request remains a draft. Canonical message-ID links are unchanged. Date-based preview links now refer to this proposed calendar.

Invite **5–10 people who choose to opt in** for the first week. The existing software cap remains 50 subscribers. The form starts with 8:00 a.m. America/Denver and allows the subscriber to choose a timezone and time. The worker runs after the chosen time; an exact delivery minute is not promised. Do not import a contact list or subscribe people on their behalf.

| Proposed day | Devotional | Reading |
|---|---|---|
| Monday, October 19 | God Sends the Reluctant | Exodus 3:7–12 |
| Tuesday, October 20 | Before You See the Whole Picture | Exodus 3:10–12 |
| Wednesday, October 21 | God's Presence in the Hard Place | Exodus 3:12 |
| Thursday, October 22 | When the Words Feel Difficult | Exodus 4:10–12 |
| Friday, October 23 | Bring Your Hesitation to God | Exodus 4:13–17 |
| Saturday, October 24 | You Can Begin with What You Have | Exodus 4:1–5 |
| Sunday, October 25 | Make Room to Be Still | Psalm 46:1–11 |

The calendar ends after Sunday. The worker does not repeat old messages or generate new teachings when the week ends. Prepare and review the next week before extending delivery.

## Design prepared for review

The app and HTML email share the existing Beyond the Message crest, navy/gold/parchment palette, a prominent Scripture excerpt, and two carefully selected emphasized sentences per reflection. The complete KJV reading and approved devotional wording remain available. The personal question and prayer have their own visual treatments. Browser and Android calls to action retain their verified destinations. Plain-text email remains complete, and the brand name and teaching remain readable when email images are blocked.

The crest is a shared public image hosted with the existing Hugging Face app assets. Its URL contains no recipient identifier. No open-tracking pixel or subscriber token is added to public devotional links. Confirmation emails use the same visual identity; unsubscribe, preferences, and business mailing details remain in every real email footer.

## Privacy wording for owner review

`EMAIL_PRIVACY_NOTICE.md` now contains proposed publishable text with a separate owner-only review note. The retention language describes the current implementation: subscription/consent/delivery records remain stored after unsubscribe, there is no automatic purge, and deletion is handled manually after verifying the request. It does not promise an automatic 30-day or 90-day purge that the code does not implement. Jamie must approve this retention approach before publication; a fixed deletion timetable would require additional implementation and testing.

The existing website privacy policy has not been changed. Add the reviewed email section there before public signup, keeping its existing conversation/OpenAI disclosures consistent. Review the Android privacy/Data safety declarations before collecting public subscription details through the app. The subscription service's delivery contact is contact@beyondthemessage.org; the current website policy lists support@beyondthemessage.org for general privacy questions.

## Checks before activation

- Private confirmation, receipt of the complete devotional, browser/Android link destinations, and persisted unsubscribe have passed. The test subscriber is unsubscribed.
- Explicitly verify that a changed delivery preference saves. Privately verify confirmation sending from the deployed Space's web signup path; prior private sends originated in GitHub.
- Review the branded preview and privacy wording. No additional design-test email has been authorized or sent by this update.
- Approve the final dates and delivery content, publish the privacy addition, and review the Android declarations.
- Only after those steps, merge the reviewed worker onto the default branch, enable signup for the agreed pilot, and enable scheduled delivery. The existing home-page invitation appears when signup is ready and enabled. Add the corresponding WordPress home-page link at that point.

The YouTube **Listen instead** option remains phase two, attached to each devotional's stable ID only when its recording is ready.
