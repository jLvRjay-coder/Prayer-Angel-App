# Published Android APK review — October 16, 2026

Status: **production version code 3 and Open testing version code 4 inspected statically; whole-app declaration not finalized or submitted.** The Android privacy-policy replacement remains a draft. Signup and automatic email delivery remain disabled.

Public sharing of this prepared report and the revised privacy-policy draft in the existing GitHub draft pull request was explicitly authorized on October 16, 2026 (America/Denver). This documentation update does not publish the policy to WordPress or submit a Google Play declaration.

## Artifact and method

Jamie downloaded **Signed, universal APK** from Play Console's Downloads tab for `3.aab (1.0.2)` and supplied the resulting `3.apk` for this review. The Production release screenshot identifies version code 3 as fully rolled out; the bundle Details screenshot shows three releases.

| Item | Observed value |
|---|---|
| Package | `org.beyondthemessage.angel` |
| Version code / name | `3` / `1.0.2` |
| Size | 6,502,634 bytes |
| SHA-256 | `0cbb4c18a474e8a1a98ad154de8764d7b9f47f420d58f99493e8704bee73149f` |
| Minimum / target SDK | 26 / 36 |
| Code inspected | Both DEX files; 12,074 classes; application activity and network-related references |

Androguard 4.1.4 decoded the binary manifest and disassembled application and relevant library code. The APK was not executed or modified. The original APK, extracted binary assets, and third-party library disassemblies are not uploaded to this repository.

## Open testing version 4 follow-up

The expanded bundle Details screenshot confirms that version code 4 (`1.0.2`) has one active Open testing release and uses the Google Play installer check. Jamie supplied its Signed, universal APK as `4.apk` for comparison.

Version 4 has the same package, size, minimum and target SDKs, permissions, WebView startup code, and network-security settings as version 3. Of the 160 ZIP entries, 157 are byte-for-byte identical. The changed entries are the manifest (version code only), the baseline profile, and the first DEX file. No classes or methods were added or removed; the sole changed method handles a Google Play licensing response. No additional native SDK, application data connection, or TLS bypass was identified. Version 4 was inspected statically and was not executed or modified.

These findings extend the network assessment below to the current Open testing release. The reviewed collection paths support answering **Yes** to encryption in transit. This assessment is based on the reviewed binaries, hosted source, and HTTPS checks; it is not an Android traffic capture or a completed declaration of every data type.

## Network findings

`MainActivity.onCreate` creates a standard `android.webkit.WebView`, enables JavaScript and DOM storage, installs an unmodified `WebViewClient`, and loads `https://angel.beyondthemessage.org`. No app-specific SSL-error override, permissive trust manager, JavaScript bridge, custom network client, or `setMixedContentMode` call was identified.

The manifest sets **`android:usesCleartextTraffic="true"`** and specifies no custom network-security configuration. This differs from earlier historical packaging notes. It allows HTTP at the application-policy level; it does **not** establish that user data was transmitted over HTTP. The current target SDK and absence of a mixed-content override leave the WebView's modern default of blocking insecure subresources from secure pages. Top-level navigation remains unrestricted by this minimal wrapper.

The reviewed app's explicit service/navigation destinations use HTTPS. The `http://www.w3.org/2000/svg` strings are SVG namespace identifiers, not network endpoints. A read-only request verified that the public HTTPS page and health endpoint return 200 with normal certificate verification; an HTTP request to the bare app origin redirects to HTTPS. This is not an Android packet capture or proof covering every possible external link.

Reviewed backend code uses the default OpenAI HTTPS client, the Hostinger HTTPS API, and the Supabase HTTPS RPC. No certificate-verification disable was found in those reviewed paths. HTTPS protects transport; it does not mean that conversation content is unreadable to the providers processing it.

Recommended next Android release: explicitly disable cleartext traffic, retain secure mixed-content defaults, and handle external navigation deliberately. The current permissive manifest flag alone is not a reason to report a confirmed plaintext leak, or to answer the encryption question without considering actual collection flows.

## Permissions and libraries

Declared permissions are INTERNET, ACCESS_NETWORK_STATE, the app's signature-level dynamic-receiver permission, and Google Play CHECK_LICENSE. The reviewed manifest requests no camera, microphone, location, contacts, SMS, or advertising-ID permission.

The class inventory contains AndroidX/Compose, Kotlin/coroutines, and Google Play `com.pairip.licensecheck` components. No Firebase Analytics, Crashlytics, Google Mobile Ads, Facebook, AppsFlyer, Mixpanel, or Amplitude SDK was identified in either DEX file. This is a finding about this native package, not a claim that the hosted website or every provider has no telemetry.

The Play licensing component binds to the installed Google Play service. Its reviewed request parcels contain the app package name and Binder callback/control fields. It does not create an Angel Chat user account. Version 4's Console Details identify installer-check protection; do not infer that other Google Play protection modes are enabled from these classes alone.

The website imports typography from Google Fonts over HTTPS. Android WebView's local website storage is enabled. The revised policy draft describes these existing behaviors and includes prominent manual deletion instructions. The public Android-specific policy page remains unchanged until the reviewed notice is published there.

## Framework telemetry change

The existing Docker startup did not explicitly set `browser.gatherUsageStats`; Streamlit documents its default as true. The prior live effective configuration was not read, so this review does not assert that a particular visitor telemetry event occurred. The runtime change adds `--browser.gatherUsageStats=false` to the Docker entrypoint and adds Dockerfile to the existing guarded preview workflow's watched paths.

[Workflow 38986156627](https://github.com/jLvRjay-coder/Prayer-Angel-App/actions/runs/38986156627) passed all 90 checks in 7.428 seconds against a disposable PostgreSQL 17 service and deployed source `2edd6c3d86801b0613daf92b6d84a3e540a05687`. Hugging Face reports RUNNING on commit `aec35db8dfa6930d3b2d5c1f6df480399ba58c46`. The deployed source metadata matches, the deployed Docker command contains the explicit telemetry-off flag, and public health returns ok. The workflow verified signup and delivery disabled and sent no email. The APK itself was not rebuilt or changed.

## Remaining submission checks

1. Publish the reviewed Android-specific privacy notice, including prominent manual deletion instructions. Do not use a new deletion-section anchor before it actually exists on the public page.
2. Review the complete Console form, including chat content, subscription email, identifiers, provider-transfer exceptions, optionality, purposes, and the final preview. The screenshots supplied so far establish initial security/account/deletion questions, not a verified completed set of data-type declarations.

No signed subscription links, recipient addresses, private credentials, or signing keys are included in this report. This is a focused source/binary review, not an independent MASA security certification.

## Local validation

The four existing preview-deployment boundary tests passed. A synthetic local Streamlit startup accepted the telemetry-off command-line flag and returned a healthy response. The Docker entrypoint and workflow parsed correctly. The revised policy draft preserves the approved email section exactly and parses as valid HTML. The report and revised policy draft are saved in a documentation update separate from the verified runtime change. No email was sent by these checks.

## Primary references

- [Google Play Data safety definitions and declaration scope](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en)
- [Android network-security configuration](https://developer.android.com/privacy-and-security/security-config)
- [Android WebView mixed-content defaults](https://developer.android.com/reference/android/webkit/WebSettings#setMixedContentMode(int))
- [Google Play automatic protection](https://support.google.com/googleplay/android-developer/answer/10183279?hl=en)
- [Streamlit configuration reference](https://docs.streamlit.io/develop/api-reference/configuration/config.toml)
