# Angel Chat Android privacy review — October 16, 2026

Status: **prepared for review; no Google Play declaration or Android policy update has been submitted.** Website signup and automatic delivery are both paused after the completed live email test.

## Public listing findings

The listing for package `org.beyondthemessage.angel`, **Angel Chat – Faith & Scripture**, currently reports no collection and no third-party sharing. Its privacy-policy link resolves to https://beyondthemessage.org/privacy-policy-angel-chat/. That separate January 2026 page describes a service that keeps no user data and does not retain conversation text. The approved email addition was published to https://beyondthemessage.org/privacy-policy/; updating that page did not update the Android-specific page.

Sources inspected: [Google Play listing](https://play.google.com/store/apps/details?id=org.beyondthemessage.angel), [Android policy](https://beyondthemessage.org/privacy-policy-angel-chat/), and [Google's Data safety guidance](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en).

## Verified application behavior

- The optional email feature stores addresses, timezone/time preferences, consent, confirmation, opt-out, and delivery records. It is not ephemeral. Email records are separate from conversation state and are not included in OpenAI prompts.
- The live test passed website signup, confirmation sending, confirmation, saved preferences, and unsubscribe. The final test record is unsubscribed. Both public enable flags have been restored to false.
- Existing `app.py` saves conversation history, a short topic/reflection note, share-card state, and session settings to the server to restore a session after reload. `safe_model_response` sends the current message and recent conversation context to OpenAI. The in-app privacy acknowledgement already describes saved conversation state and OpenAI processing. The older Android policy conflicts with this behavior even apart from the new email feature.
- Earlier project notes identify an Android Studio/Kotlin WebView wrapper for this exact package, with INTERNET permission and JavaScript/DOM storage enabled. The prior PWABuilder experiment used a different package ID and does not establish the current app's behavior. Current Android source and the distributed bundle have not been inspected here, so no claim is made that these are the wrapper's complete present permissions or SDKs. Preserve the previously selected teenager/adult audience; an Everyone content rating is not an audience declaration.

## Prepared email-feature answers

These are recommendations for the email feature, not a completed whole-app form.

| Form item | Prepared answer / action |
|---|---|
| Personal info → Email address | Collected when a reader opts in; optional for ordinary app use. |
| Ephemeral processing | No; subscription and delivery records persist. |
| Purpose | App functionality: deliver and manage the requested devotional service. Add other purposes only if actual uses support them. |
| Provider transfers | Assess the service-provider exception against the actual processing arrangements; do not equate every vendor transfer with reportable sharing or promise no sharing without review. |
| Deletion requests | The approved email notice provides a manual contact process. Unsubscribe alone is not deletion. |
| Existing chat feature | Review Other in-app messages and related identifiers/content against the saved conversation and AI-processing behavior. |
| Android wrapper | Inspect current manifest, MainActivity, dependencies, and any SDKs before finalizing the whole-app answers. |

Google's guidance includes developer-controlled WebView collection. An email feature available through this controlled app therefore cannot be reviewed as if it were unrelated open-web browsing. Its service-provider exception, optional-collection definitions, and data-type definitions should be applied to the actual current implementation.

## Prepared policy correction

`docs/angel-chat-privacy-draft.html` contains proposed public wording. It describes the existing conversation persistence and AI processing, then includes the approved email section unchanged. It removes the older blanket claims of no storage or external processing. It does not invent a fixed deletion period, new analytics SDK, account requirement, or additional Android permission.

Before publication, review the draft against the current Android project. Publish the corrected policy at the URL actually linked by Google Play, or explicitly update that listing URL to a reviewed policy. Prepare the Data safety form in Play Console → App content and review the complete preview before submitting it. Keep signup and scheduled delivery off until that review and pilot approval are complete.
