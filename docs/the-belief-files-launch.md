# The Belief Files entry point

The home screen can show **Explore The Belief Files** alongside King's Counsel. Its destination is the optional `BELIEF_FILES_URL` environment variable.

- Leave `BELIEF_FILES_URL` unset or empty until the collection has a public, reachable destination.
- Set it to the public landing-page URL after launch; the planned WordPress page is `/belief-files/`.
- The value must be an HTTPS URL with a host and no embedded credentials.
- The existing five bottom navigation tabs are preserved.
- No email switches, subscription records, or devotional schedules are changed.
- The new research library currently has an owner-private review version. Do not send public app users to that private preview.

Validation: the modified app compiles with Python. The separate research library has browser checks for mobile navigation, search, and First Vision account switching. A full Android-wrapper release has not been tested or submitted by this change.
