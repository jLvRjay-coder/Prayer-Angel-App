# Daily Encouragement pilot — review draft

Proposed first week: **October 19–25, 2026**, beginning Monday. These dates are prepared in the preview catalog; they are not authorization to send. Every entry remains `approved_for_delivery=False`, automatic daily delivery remains off, and the pull request remains a draft. Website signup is temporarily enabled for Jamie's authorized live test on October 16; this does not activate the pilot schedule. Canonical message-ID links are unchanged. Date-based preview links now refer to this proposed calendar.

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

## Approved design

The app and HTML email share the existing Beyond the Message crest, navy/gold/parchment palette, a prominent Scripture excerpt, and two carefully selected emphasized sentences per reflection. The complete KJV reading and approved devotional wording remain available. The personal question and prayer have their own visual treatments. Browser and Android calls to action retain their verified destinations. Plain-text email remains complete, and the brand name and teaching remain readable when email images are blocked.

The crest is a shared public image hosted with the existing Hugging Face app assets. Its URL contains no recipient identifier. No open-tracking pixel or subscriber token is added to public devotional links. Confirmation emails use the same visual identity; unsubscribe, preferences, and business mailing details remain in every real email footer.

## Approved privacy wording — published

Jamie approved the branded design and, on October 15, 2026 (America/Denver), the privacy wording and manual retention/deletion approach in `EMAIL_PRIVACY_NOTICE.md`. The retention language describes the current implementation: subscription/consent/delivery records remain stored after unsubscribe, there is no automatic purge, and deletion is handled manually after verifying the request. It does not promise an automatic 30-day or 90-day purge that the code does not implement. A fixed deletion timetable would require additional implementation and testing. `docs/daily-encouragement-privacy.html` contains only the approved public section, ready for a WordPress Custom HTML block.

The approved section is published at https://beyondthemessage.org/privacy-policy/, with an October 15, 2026 policy date. WordPress's save confirmation and the public page were verified. The saved source contains the approved email section exactly; the previous policy source is preserved in `docs/privacy-policy-original-2026-10-15.html`. The account-free-use paragraph now distinguishes ordinary Angel Chat use from optional email signup; the existing conversation/OpenAI disclosures and general privacy contact remain. The WordPress home page has not changed. Review the Android privacy/Data safety declarations before collecting public subscription details through the app. The subscription service's delivery contact is contact@beyondthemessage.org; the website policy retains support@beyondthemessage.org for general privacy questions.

## Checks before activation

- The October 15 private test passed confirmation, receipt of the complete devotional, browser/Android link destinations, and persisted unsubscribe.
- On October 16, Jamie enabled website signup with automatic delivery still disabled. The live form was verified, its confirmation email arrived, and Jamie confirmed through the website and supplied the green success banner. This separately verifies the deployed web signup and sending path.
- Jamie completed the live preference test and supplied the green saved-preferences banner. A read-only check confirmed the changed delivery preference was persisted while the subscription was active and confirmed. Automated screen-to-database checks also cover reopening saved preferences and preventing an unsubscribed reader from reactivating through that form.
- At Jamie's request, one preferences-only email was sent to the same test inbox using the current valid management link. Hostinger accepted the single-recipient send and its Sent copy was verified. No subscription status or preference was changed by sending this recovery email.
- The final live unsubscribe check passed: Jamie supplied the green unsubscribed banner, and a read-only database check confirmed the opt-out. Aggregate counts are one unsubscribed record, zero active subscribers, and zero pending subscribers. Closing temporary website signup remains. See `docs/live-email-test-2026-10-16.md` for the live test record.
- Close temporary signup, approve the final dates and delivery content, and review the Android declarations before expanding public collection through the app.
- Only after those steps, merge the reviewed worker onto the default branch and enable the agreed pilot schedule. The existing app home-page invitation appears when signup is ready and enabled. Add the corresponding WordPress home-page link at launch.

The YouTube **Listen instead** option remains phase two, attached to each devotional's stable ID only when its recording is ready.
