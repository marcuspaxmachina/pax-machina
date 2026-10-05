---
name: hedra-animation
description: Animates character images in the Hedra web app through the browser - lip-synced talking clips (Character-3) from the final character image plus each line's audio, and silent image-to-video reaction or "listening" clips - with upload retries, credit budgeting, bulk download via the app's own asset API, and lip-sync review. Use when the user says "animate the episode", "send the lines to Hedra", "make a listening loop", "make the statue nod", "download the Hedra renders", or "how many credits will this cost".
---

# Hedra animation (browser)

Inputs: `brand/<character>-final.jpg` (from `character-art`) and the approved `audio/<ep>/<id>.mp3` clips (from
`episode-voices`). Output: `video/<ep>/<id>.mp4`, one per clip, plus extra silent clips (listening loops,
reactions). Code snippets are in `reference.md`.

## Step 1: budget (before anything)
- Total the audio seconds: sum the mp3 durations (ffprobe/imageio-ffmpeg) for the clips to animate.
- At time of writing (Oct 2026) Character-3 cost roughly **7 credits per second** of output; image-to-video
  models cost a flat amount per short clip that varies by model. Read the current price in the app's generation
  panel and the plan page; they change.
- Add ~30% for retries. Tell the human the estimate and their remaining credits. **Buying credits or upgrading
  the plan is the human's click.** Paid tiers were needed for commercial use and longer clips at time of writing.

## Step 2: sign in (human)
Open the Hedra web app with the Playwright browser. Use the `browser-handoff` skill (pax-life plugin): the human
signs in; you take over when the app's create page is visible. Sessions can expire mid-batch; if a request
returns 401 or the page shows a login screen, hand back to the human.

## Step 3: talking clips (Character-3, lip sync)
For each clip, in id order:
1. Select the Character-3 (talking head / lip-sync) model.
2. Upload the character image and the clip's audio. File-chooser modals are flaky: use the retry loop in
   `reference.md` (click the upload control, wait for the file chooser, `setInputFiles`; if no chooser appears in
   5 s, set the files directly on the `input[type=file]`; retry up to 3 times; confirm a thumbnail/waveform appears).
3. Motion prompt, short and consistent per character, e.g.
   `relaxed, dry delivery, natural blinks, slight head movement, locked medium shot, single character, mouth closed between phrases`.
4. Aspect ratio 16:9, the resolution the plan allows. Generate.
5. Record the clip id -> generation title/time in `video/<ep>/hedra-log.md` so downloads can be matched later.

Queue several generations, but do not exceed the human's credit budget.

## Step 4: silent clips (image-to-video)
For anything that moves but does not talk, use an image-to-video model with no audio:
- **Listening loop** for a character shown on a screen behind the host: the character's final image,
  prompt `listening attentively, subtle nods, blinks, mouth closed, no talking, static camera`, 5-10 s.
  The edit plays it forward then reversed so it loops without a jump.
- **Background reactions**: crop the object from the host's frame (e.g. a marble bust on a shelf) and animate it:
  `the marble bust slowly nods once`, `the bust glances sideways skeptically`, `the bust does a double take`.
  Keep the crop's exact pixel box; the `episode-edit` reactions step composites it back.
- **Cutaways**: e.g. the doubter turning his head toward his old computer screen.

## Step 5: bulk download
Downloading one by one from the UI is slow and names collide. Use the app's own asset API from inside the page,
with the auth header the page itself uses (see `reference.md`):
1. Reload the library page and list the network requests (`browser_network_requests`); find the request that
   lists the user's assets/generations and note its URL and `Authorization` header **inside the browser only**.
2. In `browser_evaluate`, fetch that list with the same header, then download each video URL via a blob and an
   `<a download>` click, named `<clip-id>.mp4` using your `hedra-log.md` mapping.
3. Never print, save or echo the auth header or tokens into files, logs or chat. They stay in the page context.
4. Move files from the browser's download folder to `video/<ep>/`.

**File-name collisions:** the app often names every download after the project or the image, so files overwrite
or get ` (1)` suffixes. Rename to the clip id immediately, one at a time, and verify durations against the audio
(a mismatch means the wrong file).

## Step 6: review (gate)
Open each clip (or a contact sheet of first frames) and check:
- lip sync matches the audio, especially plosives (p, b, m) and the start and end of the clip;
- no face drift, extra fingers, warped glasses or jewellery, or background objects melting;
- the character stays in frame; no unwanted camera moves.
Re-render only the failing clips. **Gate:** the human approves before the edit.

## What this won't do / safety
- It does not sign in, buy credits, change plans or accept terms; the human does.
- Auth headers and tokens are used only inside the page; never logged, saved, printed or committed.
- It does not upload photos of people who have not consented; only the approved final character art.
- Bulk download uses only the user's own assets through the app's own endpoints, at a polite pace (one request at
  a time). If the app's terms forbid automation, stop and download manually.
- Prices and model names are "at time of writing (Oct 2026)"; check the app before quoting costs.
