# Angel Chat home hub and The Belief Files

The home screen keeps Angel Chat as the main invitation, adds a Daily Encouragement entry and four resource cards, and links to the published Belief Files page at https://beyondthemessage.org/the-belief-files/.

The fifth bottom navigation position is now Belief Files. How it works remains available in the home header and in a Home/help utility bar on the other views. Existing `?v=about` links still open help. The five navigation destinations are Angel Chat, King's Counsel, Bible Stories, Study Hub, and Belief Files.

`home_hub.py` supplies the home markup and the navigation. Streamlit's native `st.html` renders the markup without embedded JavaScript or positioning logic. Internal links use the existing query builder; external links use their public URLs and do not receive session IDs or private email-action tokens. Signup visibility continues to follow the existing readiness and enable settings.

The public WordPress URL is the default. An optional `BELIEF_FILES_URL` environment value may replace it with an HTTPS destination without embedded credentials. An empty or invalid value falls back to the public page, keeping the resource visible.

`home_hub.py` is included in `deploy_space_preview.RUNTIME_FILES`, which is also used by the existing release publisher. The existing main-branch release workflow publishes the change after its checks pass. This update does not change the email switches, subscription logic, devotional calendar, chat prompts, or Android package.

Validation covers home/resource destinations, five-item navigation, signup visibility, escaped internal links, invalid destination overrides, existing deployment boundaries, and real app routes. Desktop and phone browser checks exercise the home, help, chat, and daily entry points. A web update reaches the published app only if its Android wrapper loads the hosted page; a new Android store package is not included.
