# pax-studio: make an AI-hosted YouTube channel with Claude Code as the producer

The skills behind **Pax Machina** ([@MarcusPaxMachina](https://www.youtube.com/@MarcusPaxMachina),
[paxmachina.blog](https://paxmachina.blog)), where Marcus (a Roman emperor lost in 2026), Claudia (Claude Code
personified) and Commodus (the doubter) explain how to hand the little things in life to Claude Code.
Episode 1: https://youtu.be/KQhgzy2wqe8

Bring your own characters, accounts and API keys. Every sign-in, purchase, plan upgrade, upload and consent is
**your** click; the skills stop and hand the browser back to you (see `browser-handoff` in the pax-life plugin).

## Skills

| Skill | What it does | Needs |
|---|---|---|
| `episode-pipeline` | Orchestrates idea -> script -> privacy check -> art -> voices -> animation -> edit -> Shorts -> publish -> blog -> updates, with review gates | Everything below |
| `character-art` | Consistent character art from your own photos, variations, plain-language edits, one locked final per character | Gemini (browser) |
| `episode-voices` | ElevenLabs voices per character with audio tags, multiple takes, a clips JSON, a stitched preview (`tts_episode.py`) | ElevenLabs API key, Python, FFmpeg |
| `hedra-animation` | Lip-synced talking clips and silent reaction/listening clips, credit budgeting, bulk download | Hedra (browser) |
| `episode-edit` | FFmpeg assembly, screen overlays, background reactions, gags, plus an edit playbook of real critique -> fix pairs (`edit_episode.py`, `reactions.py`) | Python, FFmpeg |
| `youtube-shorts` | 9:16 blur-fill Shorts with hook titles (`make_shorts.py`) and a Shorts upload checklist | Python, FFmpeg, YouTube |
| `youtube-publish` | First-upload checklist: title, description template, chapters, thumbnail, AI disclosure, end screen, channel branding | YouTube Studio (browser) |
| `youtube-update` | Update a live video without re-uploading: links, chapters, thumbnail, captions (`make_srt.py`), pinned comment; YouTube/blog sync checklist | YouTube Studio, optional faster-whisper |
| `blog-publish` | Word/Markdown -> WordPress posts with cross-links, video embed and a privacy assert (`build_web.py`); update in place | WordPress (wp-admin), Python |

## Tools and rough costs (at time of writing, Oct 2026; check current prices)

| Tool | Used for | Rough cost |
|---|---|---|
| Claude Code (Claude Pro) | The producer: scripts, configs, browser automation, editing scripts | about $20/month |
| Gemini (web app) | Character art | free tier works; paid tiers add limits/quality |
| ElevenLabs | Voices (TTS, Voice Design) | Starter about $6/month; Creator about $22/month |
| Hedra | Talking-head lip sync (Character-3, ~7 credits/s) and image-to-video | Basic about $20/month; Pro about $50/month |
| FFmpeg via `imageio-ffmpeg` | All editing, Shorts, previews | free (`pip install imageio-ffmpeg`) |
| Python 3.10+ | Scripts (`numpy`, `pillow`, `mammoth`, `markdown`, `python-docx`, optional `faster-whisper`) | free |
| YouTube | Hosting; custom thumbnails need phone verification; clickable links need advanced-features verification | free |
| WordPress.com | Companion blog | free plan to start; Personal about $4-5/month with a custom domain |

A lean setup is about $46/month (Claude Pro + ElevenLabs Starter + Hedra Basic).

## Setup

```
pip install imageio-ffmpeg numpy pillow mammoth markdown python-docx
# optional, for captions from audio:
pip install faster-whisper
```

- API keys go in environment variables or a git-ignored `.env` in your project (e.g. `ELEVENLABS_API_KEY=...`).
  The scripts never print them. Do not paste keys into chat.
- Copy the `*.example.json` files from each skill into your project's `config/` folder and fill them in.
- Add to `.gitignore`: `.env`, `audio/`, `video/`, raw photos, `config/privacy-denylist.txt`.

## Disclosures

Realistic AI-generated people or voices must be disclosed on YouTube ("altered or synthetic content").
Only use photos and voices you own or have consent for. Not affiliated with or endorsed by Anthropic, Google,
ElevenLabs, Hedra, YouTube or WordPress. Claude and Claude Code are Anthropic products.
