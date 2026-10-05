---
name: youtube-publish
description: Prepares and walks through the first upload of an episode in YouTube Studio via the browser - title, description from a template (guide link and "who is the host" link first, then chapters, tools used and AI disclosures), chapters, custom thumbnail, "altered or synthetic content", audience, visibility/schedule, end screen and cards - plus one-time channel branding. Use when the user says "upload the episode", "publish to YouTube", "write the description", "make chapters", "set up the channel banner", or "prepare the upload".
---

# YouTube publish (first upload)

You prepare every field as files, then fill YouTube Studio with the human watching. **The human signs in and
clicks Upload, Publish/Schedule and any verification or consent.** Use the `browser-handoff` skill (pax-life
plugin) for sign-in. Templates are in `reference.md`.

## Step 1: prepare the files (in `episodes/<ep>/`)
1. `youtube-title.txt`: under ~70 characters, the promise + the character hook. Offer 3 options; the human picks.
2. `youtube-chapters.txt`: from the final cut's timeline (see below).
3. `youtube-description.txt`: from the template in `reference.md`. **First lines:** the companion guide link and a
   "who is the host" link (an About page). Then a 2-3 sentence summary, "try this today", chapters, tools used,
   AI disclosures and disclaimers, 3-5 hashtags.
4. `thumbnail.jpg`: 1280x720, under 2 MB, JPG/PNG; big face + 2-4 words; readable at phone size.
5. Run the privacy check on all of it (no real names, emails, paths, client or employer names).
**Gate:** the human approves title, description, chapters and thumbnail.

### Chapters
- First chapter at **0:00**; at least **3** chapters; each at least **10 seconds** long; ascending order;
  format `M:SS Title` one per line in the description.
- Compute times from the edit: sum clip durations minus each transition overlap (`make_srt.py` in the
  `youtube-update` skill prints clip start times), then confirm by scrubbing the final cut.

## Step 2: upload (Studio, human present)
1. The human signs in at https://studio.youtube.com (`browser-handoff`). Create -> Upload videos -> pick the
   final cut (the human can drag it in, or you use `setInputFiles` on the upload input).
2. **Details:** paste title and description; upload the thumbnail (custom thumbnails require the channel's phone
   verification, a one-time human step); add to a playlist (one per series).
3. **Audience:** "No, it's not made for kids" (unless it truly is).
4. **Show more:**
   - **Altered or synthetic content: Yes** when the video shows realistic AI-generated or altered people, voices or
     events (e.g. a host whose face began as a real person's photos, or a cloned/remixed voice). Clearly
     cartoonish characters may not require it; when unsure, disclose.
   - Paid promotion: tick if anything is sponsored or affiliate.
   - Tags: a few (the show name, main tool names); they matter little.
   - Language and caption language; category (Education or Science & Technology); comments on.
5. **Video elements:** captions (upload the .srt from `youtube-update` if ready); **end screen** (last 5-20 s:
   subscribe + best next video/playlist); **cards** at the moments the script mentions the guide or another episode.
6. **Checks:** wait for copyright and ad-suitability checks.
7. **Visibility:** upload as **Private** or **Unlisted** first; the human watches it on YouTube; then Public or
   Schedule. The human clicks.

## Step 3: after publishing
- Record the video URL in `episodes/<ep>/production-plan.md` and the blog config.
- Hand over to `blog-publish` (embed the video) and then `youtube-update` (add the live guide link, captions,
  pinned comment).
- **Links in descriptions** may not be clickable until the channel completes YouTube's one-time "advanced
  features" verification (Studio -> Settings -> Channel -> Feature eligibility). The human does that step.

## One-time channel branding (Studio -> Customization)
- **Profile picture:** 800x800 PNG/JPG, the host's face, readable when tiny (circle crop).
- **Banner:** 2560x1440, under 6 MB; keep text and faces inside the central **1546x423** safe area.
- **Watermark** (optional): 150x150 subscribe badge.
- **Description:** who the host is, what the channel teaches, how often, "AI-animated characters" disclosure,
  and the blog link.
- **Links:** blog, About page, free toolkit/download, newsletter.
- **Handle:** matches the show name across platforms where possible.
- Channel trailer / featured video for returning subscribers.

## What this won't do / safety
- It never clicks Upload, Publish, Schedule, verification, monetization or legal consent; the human does.
- It never sets "altered or synthetic content" to No for realistic AI people or voices.
- It never fills the description with real-identity details or private links.
- It does not buy promotion. Sponsors and affiliate links get an on-screen and description disclosure.
