# YouTube publish: templates

## Description template

```
📜 Read the full guide (exact prompts, setup, costs): <GUIDE_URL>
🏛️ Who is <HOST>? <ABOUT_URL>

<2-3 sentences in the host's voice: who they are, what this episode shows, what the viewer will be able to do.>

🧰 Free toolkit (Claude Code skills used to make this video): <TOOLKIT_URL>
🏁 New to Claude Code? Start here: <START_HERE_URL>

TRY THIS TODAY: <one concrete step and the exact prompt in quotes>

Chapters
0:00 <cold open>
0:48 <...>
1:25 <...>
...

Made with: Claude Code (planning, scripts, editing, browser automation) · <image tool> (character art) ·
<voice tool> (voices) · <animation tool> (animation) · Python + FFmpeg (editing)

<HOST>, <ASSISTANT> and <DOUBTER> are AI-animated characters. <If true: A real person is behind this channel;
the host's face began as photographs of that person and the voice began as that person's real voice, reshaped
with consent.> Not affiliated with or endorsed by Anthropic, <tool companies>. Claude and Claude Code are
Anthropic products. Prices change; check before you buy.

#ClaudeCode #AI #Productivity #<ShowTag>
```

Example (Pax Machina, Episode 1, public): https://youtu.be/KQhgzy2wqe8 with its guide on https://paxmachina.blog.

Rules:
- The first ~120 characters show in search and above the fold: make the guide link and the hook land there.
- One emoji per link line is plenty. No link shorteners (they look like spam).
- Before the guide exists, write "Guide coming soon" and update it later with `youtube-update`.

## Title formulas
- "<Character> <does surprising thing> (<what you learn>)": "A Roman emperor hands his life to Claude Code"
- "I <did X> with Claude Code. Here's how." (host voice)
- Keep the character hook and the tool name; avoid clickbait the video does not deliver.

## Thumbnail checklist
- 1280x720 (16:9), JPG/PNG, under 2 MB.
- One face with a strong expression, 2-4 words max, high contrast, brand colors.
- Test at 160x90: still readable?
- No small text, no real people other than the consenting creator, no misleading imagery.

## Chapter extraction helper

`make_srt.py --starts` (in the `youtube-update` skill) prints each clip's start time in the final cut. Map
script sections to the first clip of each section, round down to the second, and make sure the first is `0:00`.

## Upload field checklist (copy into the episode folder and tick)

- [ ] Title
- [ ] Description (guide + about links first)
- [ ] Thumbnail (phone-verified channel)
- [ ] Playlist
- [ ] Audience: not made for kids
- [ ] Altered or synthetic content: Yes (realistic AI people/voices)
- [ ] Paid promotion: checked if applicable
- [ ] Tags, language, category
- [ ] Captions (.srt)
- [ ] End screen + cards
- [ ] Private/unlisted review by the human
- [ ] Public / scheduled (human click)
- [ ] URL recorded; blog and update steps queued
