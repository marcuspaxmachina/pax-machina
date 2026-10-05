---
name: episode-pipeline
description: Orchestrates an AI-hosted YouTube episode end to end with Claude Code as the producer - idea, script, privacy check, character art, voices, animation, edit, Shorts, publish, companion blog post and YouTube updates - and says which pax-studio skill handles each step and where the human must approve. Use when the user says "make an episode", "plan episode 2", "continue the episode", "where are we on the episode", "what's next for the video", or starts a new AI-hosted show.
---

# Episode pipeline (Claude Code as the producer)

You run every step; the human approves at each gate. Nothing is uploaded, published, purchased or signed into
without the human's own click (see the `browser-handoff` skill in the pax-life plugin for the sign-in pattern).

## Project layout (create it if missing)

```
<show>/
  show-bible.md            characters, voices, looks, tone, naming rules, running gags
  brand/                   final character art (<name>-final.jpg), colors, thumbnails, banner
  episodes/<ep>/           script-vX.Y.md, clips.json, privacy-check.md, youtube-description.txt, chapters.txt
  audio/<ep>/              voice clips + full preview
  video/<ep>/              animation renders, edit/, shorts/, final cuts
  blog/                    article sources and build config
  config/                  cast.json, edit.json, shorts.json, blog.json (no secrets)
  .env                     API keys (git-ignored, never printed)
```

Make sure `.gitignore` contains `.env`, `audio/`, `video/` and any folder with raw photos before anything is committed.

## Step 0: read the bible
Read `show-bible.md` and the previous episode's notes before writing anything. If there is no bible, draft one
with the user: each character's role, voice, look, era, background, catchphrases, and what they never do.
Typical cast: a **host** (e.g. Marcus, a Roman emperor lost in 2026), an **assistant character** (e.g. Claudia,
Claude Code personified, calm and precise) and a **doubter** (e.g. Commodus, whose "it cannot be done" sets up
each episode's proof).

## Step 1: script
- Structure: cold-open hook (first 10 seconds) -> story -> **teaching beat** ("try this today" with the exact
  prompt) -> the doubter objects -> payoff -> tease the next episode.
- Name tools precisely ("Claude Code", "ElevenLabs"), never "the AI".
- Save as `episodes/<ep>/script-vX.Y.md`; bump the version on each revision and keep old versions.
- **Gate 1:** the human approves the script.

## Step 2: privacy check (before any audio, art or screen capture)
Write `episodes/<ep>/privacy-check.md` and tick each item:
- No real names, family names, employers, clients, addresses, emails, phone numbers or account numbers.
- No absolute file paths with a username, no tenant or organization names in screenshots.
- Screenshots blurred where needed; photo metadata (EXIF/GPS) stripped from anything uploaded.
- Nothing confidential the creator has promised to keep private.
Fail closed: if unsure, ask.

## Step 3: character art -> `character-art` skill
One locked "final" image per character, reused every episode. **Gate 2:** the human approves each image.

## Step 4: voices -> `episode-voices` skill
Script -> `clips.json` -> ElevenLabs takes -> full preview opened for the human.
**Gate 3:** the human approves the full preview (listen for spoken tags, mispronunciations, pacing).

## Step 5: animation -> `hedra-animation` skill
Lip-synced talking clips per line, plus silent reaction/listening clips. Check credits first.
**Gate 4:** the human spot-checks lip sync on every clip.

## Step 6: edit -> `episode-edit` skill
Assemble, overlays, reactions, transitions. Write timestamped cuts and open each for review.
**Gate 5:** every cut is approved; turn each critique into a fix using the edit playbook.

## Step 7: Shorts -> `youtube-shorts` skill
2-4 vertical Shorts per episode. **Gate 6:** the human approves each Short.

## Step 8: publish -> `youtube-publish` skill
Upload checklist in YouTube Studio (title, description, chapters, thumbnail, AI disclosure, audience, end screen).
The human clicks Upload and Publish.

## Step 9: companion blog post -> `blog-publish` skill
Exact prompts, setup steps and costs; embeds the video; privacy assert passes before upload.

## Step 10: keep things in sync -> `youtube-update` skill
After the blog post (or a toolkit download) goes live, add its link to the top of the video description,
upload captions (.srt), add the pinned comment and update channel links.

## Status tracking
Keep a table at the top of `episodes/<ep>/production-plan.md`:

| # | Step | Skill | Status | Gate approved |
|---|---|---|---|---|
| 1 | Script v0.x | - | in progress | |

When the user asks "where are we", read that table and the newest files in `audio/<ep>` and `video/<ep>`, then
report the next action and who owns it.

## What this won't do / safety
- It does not upload, publish, buy credits, upgrade plans, accept terms or sign in. Those are the human's clicks.
- It does not skip a gate because a step "looks fine"; it asks.
- It never puts real-identity details into scripts, art prompts, descriptions, blog posts or file names.
- API keys come from environment variables or a git-ignored `.env`; they are never printed, logged or committed.
- Realistic AI people or voices must be disclosed on upload (YouTube's "altered or synthetic content" setting).
