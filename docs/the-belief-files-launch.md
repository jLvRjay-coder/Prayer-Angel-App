# Angel Chat home hub and The Belief Files

The home screen keeps Angel Chat as the main invitation, adds a Daily Encouragement entry and four resource cards, and opens an in-app Belief Files library at `?v=belief`.

The fifth bottom navigation position is now Belief Files. How it works remains available in the home header and in a Home/help utility bar on the other views. Existing `?v=about` links still open help. The five navigation destinations are Angel Chat, King's Counsel, Bible Stories, Study Hub, and Belief Files.

`home_hub.py` supplies the home markup and the navigation. Streamlit's native `st.html` renders the markup without embedded JavaScript or positioning logic. Internal links use the existing query builder; external links use their public URLs and do not receive session IDs or private email-action tokens. Signup visibility continues to follow the existing readiness and enable settings.

The library links to the published First Vision study and introductory LDS comparison on WordPress. The default published collection is https://beyondthemessage.org/the-belief-files/. An optional `BELIEF_FILES_URL` environment value may replace that website destination with an HTTPS URL without embedded credentials; it does not replace the in-app library. An empty or invalid value falls back to the public page.

## Case File 002

`belief_files.py` renders the approved Book of Mormon Translation case from `belief_case_002.md`. The core text is preserved in eight sections: Overview, Evidence, Witnesses, Explanations, Scripture, Assessment, Discuss, and Sources. The manuscript's collection metadata remains in the source file rather than the reading flow.

`?v=belief&case=002` opens the overview. The optional `section` parameter selects a chapter, for example `?v=belief&case=002&section=witnesses`. Invalid chapters return the overview; unknown cases return the library. Forward/back controls, contents, and source-number links use ordinary app URLs. Source links open the source register and identify the relevant entry by fragment. External references use their original public URLs without session or email-action parameters.

Tables retain their header/row semantics and become labeled cards on phone screens. The reader uses the same navy/gold/parchment identity as the home hub, visible keyboard focus, and a single article column. The complete, approved 22-page `belief_case_002.pdf` is available through a Streamlit download button. No account or chat request is needed to read the case.

`home_hub.py`, `belief_files.py`, `belief_case_002.md`, and `belief_case_002.pdf` are included in `deploy_space_preview.RUNTIME_FILES`, which is also used by the existing release publisher. The main-branch release workflow runs for reader code and case Markdown/PDF changes and publishes after its checks pass. This update does not change the email switches, subscription logic, devotional calendar, chat prompts, or Android package.

Validation covers home/resource destinations, five-item navigation, signup visibility, escaped internal links, invalid destination overrides, existing deployment boundaries, and real app routes. Desktop and phone browser checks exercise the home, help, chat, and daily entry points. A web update reaches the published app only if its Android wrapper loads the hosted page; a new Android store package is not included.
