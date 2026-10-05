---
name: youtube-shorts
description: Cuts vertical 9:16 1080x1920 YouTube Shorts from an edited episode - blur-fill background, big hook title, brand and "full episode" footer - picks 30-60 second moments with a hook in the first 2 seconds, and gives the Shorts upload checklist. Use when the user says "make Shorts", "cut a Short from the AOL bit", "vertical version", "clips for TikTok/Reels", or "what should the Shorts be".
---

# YouTube Shorts (blur-fill vertical cuts)

Script: `scripts/make_shorts.py` next to this file (Python 3.10+, `pip install imageio-ffmpeg`). It reads the
processed clips from `episode-edit` (`video/<ep>/edit/<id>.mp4`), so overlays and reactions carry over.

## Step 1: pick the moments
Read the approved script and `clips.json`, then propose 3-4 candidates in a table:

| Name | Clips | Length | Hook (first 2 s) | Why it works |
|---|---|---|---|---|

Rules:
- **30-60 seconds** (Shorts can be longer at time of writing, but short and complete performs best).
- **A hook in the first 2 seconds**: start on a question, a surprising line or a visual gag, not a greeting. If the
  best line is mid-clip, use `start` to skip in.
- One self-contained idea per Short: a joke with its payoff, or one "try this today" tip with the exact prompt.
- Prefer the doubter's jabs, running gags and the practical tip; avoid moments that need the episode's context.
- **Gate:** the human picks which Shorts to make.

## Step 2: configure
Copy `shorts.example.json` to `config/shorts-<ep>.json`:
- `clips`: ids in play order (consecutive clips concatenate with hard cuts).
- `hook`: 1-3 lines, **all caps, 2-3 words per line**, each line drawn by its own `drawtext` (multi-line
  text in one drawtext renders unreliably). Keep each line under ~14 characters at size 96.
- `brand` / `footer`: e.g. the show name and "FULL EPISODE ON THE CHANNEL".
- `font`: a bold display font file you are licensed to use; the script falls back to a system font.

## Step 3: render and review
```
python scripts/make_shorts.py config/shorts-<ep>.json            # all
python scripts/make_shorts.py config/shorts-<ep>.json --only short-02-screen-prank
```
How it works: every input is normalized with `scale`, `setsar=1`, `fps=30` and `aresample=44100` before
`concat` (mismatched SAR/fps/sample rates make concat fail or drift); the 16:9 picture is laid over a blurred,
darkened 1080x1920 copy of itself; titles are drawn on top; output is yuv420p + faststart.

Open each Short for the human. Check on a phone if possible: titles readable, nothing important hidden behind
the Shorts UI (bottom ~20% and right edge carry buttons and captions), audio starts immediately.
**Gate:** the human approves each Short.

## Step 4: upload checklist (human clicks; `browser-handoff` for sign-in)
In YouTube Studio -> Create -> Upload (vertical videos up to the Shorts length limit become Shorts automatically):
- [ ] Title: the hook plus context, under ~60 characters; optional `#Shorts`.
- [ ] Description: one line + the full episode link + the companion guide link.
- [ ] **Altered or synthetic content: Yes** if the characters or voices are realistic AI people.
- [ ] Made for kids: No (unless it truly is).
- [ ] Related video (Shorts link to a long video): set it to the full episode.
- [ ] Visibility: schedule (e.g. Mon/Wed/Fri) rather than dumping all at once.
- [ ] After publishing: pin a comment pointing to the full episode (`youtube-update`).
- [ ] Reusing on other platforms: export the same file; remove YouTube-specific wording from the footer if needed.

## What this won't do / safety
- It does not upload or schedule; the human clicks Upload/Schedule.
- It uses only clips from the user's own episode and fonts/music they are licensed to use.
- Hook titles must not mislead (no fake claims, no impersonation); YouTube's misleading-metadata rules apply.
- Keep the AI disclosure on Shorts exactly as on the full episode.
