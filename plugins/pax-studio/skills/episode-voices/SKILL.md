---
name: episode-voices
description: Turns an episode script into voice clips with the ElevenLabs API - one voice per character, expressive audio tags, several takes per line to pick from - keeps a clips JSON as the source of truth, then stitches a full-episode preview and opens it for review. Use when the user says "voice the episode", "re-voice line 5", "make 3 takes", "the sigh is too long", "preview the episode audio", or "cast a voice for Commodus".
---

# Episode voices (ElevenLabs)

Script -> `episodes/<ep>/clips.json` -> numbered mp3 clips in `audio/<ep>/` -> one stitched preview the human
listens to. The script is `scripts/tts_episode.py` next to this file (needs Python 3.10+ and
`pip install imageio-ffmpeg` for the preview).

## Setup (once)
1. The human creates an ElevenLabs account and picks a plan (a paid tier is needed for commercial use; Starter was
   about $6/month at time of writing, Oct 2026). Plan choice and payment are the human's clicks.
2. API key: ElevenLabs -> Developers -> API Keys -> create a key limited to Text to Speech + Voices, with a monthly
   credit cap. The human puts it in the environment as `ELEVENLABS_API_KEY`, or in a `.env` file in the project
   root (`ELEVENLABS_API_KEY=...`) that is listed in `.gitignore`. **Ask them to save it themselves; never ask
   them to paste it into chat. Never print, log, echo or commit it.**
3. Cast: copy `cast.example.json` to `config/cast.json`. Fill each character's `voice_id`
   (`python tts_episode.py --cast config/cast.json --list-voices`). Check the model id against
   `GET /v1/models`; use the newest model that supports audio tags.
4. Designing voices (the human's clicks in the ElevenLabs UI): Voice Design from a text description, or, for a
   host who should sound like the creator but not be recognizable, a **private** instant clone of the creator's own
   voice (with their consent) that is then remixed (older, deeper, different texture). Never clone anyone else's
   voice. Never publish a raw clone.

## Workflow
1. **Split the script into clips** in `episodes/<ep>/clips.json`:
   `[{"id": "01-S1", "voice": "host", "text": "..."}]`
   - Ids in playback order (`01-`, `02-`...) so stitching and editing sort correctly. A letter per character
     helps the edit (e.g. S host, C assistant, K doubter).
   - One clip per speaking turn. Long monologues can stay one clip.
   - **This JSON is the source of truth.** Edit lines here, never only in the mp3s; the edit and the captions
     (`youtube-update` -> `make_srt.py`) are built from it.
2. **Audio tags**, sparingly: `[pause]`, `[beat]`, `[chuckles]`, `[sighs]`, `[scoffs]`, plus tone tags such as
   `[dryly]`, `[warmly]`, `[calmly]`, `[suspicious]`.
   - **Known pitfall: unsupported tags are spoken aloud** (e.g. "lightly"). Keep the proven list in
     `allowed_tags` in cast.json; the script warns about anything else. Listen for spoken tags in every preview.
   - `[pause]` is a short silence; `[beat]` a comedic micro-pause before a punchline. Use them instead of
     `[sighs]` when a sigh comes out too long.
   - Respell hard names phonetically in the text if they are mispronounced.
3. **Check credits** before big runs: `--credits`.
4. **Generate takes**:
   `python tts_episode.py episodes/<ep>/clips.json --cast config/cast.json --out audio/<ep> --takes 3`
   Existing files are skipped. To redo one line: delete its mp3(s) and run with `--only <id>`.
5. **Pick takes**: listen (open each take), then `--pick 05-S3=2 07-K1=1` copies the chosen take to `<id>.mp3`.
   With `--takes 1` the file is already `<id>.mp3`.
6. **Stitch and open the preview**: `--preview --open` writes `audio/<ep>/<EP>-FULL-PREVIEW-<mmdd-hhmm>.mp3`
   (timestamped so a copy open in a media player never blocks the save) and opens it.
7. Ask for notes; fix specific clips; repeat 4-6. **Gate:** the human approves the full preview before animation.

## Review checklist
- Each character sounds distinct and matches the bible (age, energy, accent).
- No spoken tags, no mispronounced names, no clipped endings.
- Pacing: the host is not rushed; sighs and laughs are short; tags are not overused.
- Every clip id in `clips.json` has an `<id>.mp3`; no leftover takes in the stitched preview.

## What this won't do / safety
- It does not create accounts, choose plans, buy credits or accept voice-cloning terms; the human does.
- It never prints or stores the API key anywhere except where the human put it.
- It does not clone a voice without the speaker's consent, and never a public figure's.
- Voice ids are account-specific; keep `config/cast.json` out of public repos if you prefer (they are not
  secrets, but they identify the account).
- Realistic synthetic voices must be disclosed on YouTube upload (`youtube-publish`).
