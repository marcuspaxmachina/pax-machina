---
name: episode-edit
description: Assembles an episode from animated clips with FFmpeg (imageio-ffmpeg) - dissolves between characters, near-hard cuts with punch-ins for the same character, a silent listening loop on an in-scene screen, background reactions and flash gags, colour consistency, YouTube/Windows-safe output - and turns each review critique into a fix using a playbook of real critique -> fix pairs. Use when the user says "edit the episode", "assemble the cut", "the transition is jarring", "she's talking on the laptop", "make the statue nod", "the video won't play", or gives notes on a cut.
---

# Episode edit (FFmpeg)

Scripts next to this file (Python 3.10+, `pip install imageio-ffmpeg numpy pillow`):
- `scripts/reactions.py <config>`: composites background reactions and flash gags into a **copy** of the clips.
- `scripts/edit_episode.py <config>`: processes each clip and assembles the timestamped final cut.
- `edit.example.json`, `reactions.example.json`: annotated configs. `reference.md`: the **edit playbook**.

Inputs: `video/<ep>/<id>.mp4` from `hedra-animation`, `episodes/<ep>/clips.json` from `episode-voices`.

## Step 1: set up the configs
1. Copy `edit.example.json` to `config/edit-<ep>.json`. Set `clips_dir`, `clips_json`, frame size (match the
   renders, usually 1280x720 or 1920x1080) and the clip order. Clips that are not in `clips.json` (cutaways,
   gags) go in `clips` as `{"id": ..., "character": ...}`.
2. **Screen overlay (optional):** when a character appears on a screen in another character's shot (the assistant on
   the host's laptop), measure the screen's four corners on a frame:
   `ffmpeg -ss 1 -i video/<ep>/01-S1.mp4 -frames:v 1 frame.png`, open it, and read the pixel corners
   (top-left, top-right, bottom-left, bottom-right). Use a **silent listening loop** as `loop_source`, never the
   talking clips. A mask is generated from the corners unless you supply one (supply one if a hand or object covers
   part of the screen).
3. **Reactions (optional):** copy `reactions.example.json`; set the region box of the reacting object, each
   reaction's clip and start time (seconds into that clip), and any flash gags. Point the edit's `clips_dir` at
   the reactions `out_dir`.

## Step 2: build
```
python scripts/reactions.py config/reactions-<ep>.json      # only if you have reactions
python scripts/edit_episode.py config/edit-<ep>.json        # add --reuse to skip unchanged clips
```
- Heavy renders hold every clip in one filter graph: close browsers and other heavy apps first and make sure
  several GB of RAM are free; if FFmpeg is killed or crawls, assemble in halves and join with the concat demuxer.
- Output: `<out_dir>/<NAME>-EDIT-<mmdd-hhmm>.mp4`. A new file each build, so a copy open in a media player can
  never silently block the save. Delete old cuts when the human is done comparing.

## Step 3: review (gate, every cut)
1. Open the new cut for the human (Windows `Start-Process <file>`, macOS `open`, Linux `xdg-open`).
2. Ask for notes with timestamps. For each note, find the matching entry in `reference.md` and apply that fix;
   if there is no match, propose a fix, apply it, and add the new critique -> fix pair to the playbook.
3. Self-check before handing over: `ffmpeg -i <cut>` shows `yuv420p`, H.264 high, AAC; duration is what you
   expect; spot-check each transition and each reaction moment by extracting frames.
4. **Gate:** the human approves the cut. Keep the approved file name in `episodes/<ep>/production-plan.md`.

## Step 4: finishing touches (optional)
- Title card / end card: a still image clip (`-loop 1 -t 4 -i card.png` plus silent audio) added to `clips`.
  End card text: "<characters> are AI-animated characters" and any "not affiliated with" disclaimers.
- Music bed: mix at about -24 dB under dialogue with `amix`/`sidechaincompress`; only music you have rights to.
- Leave the last ~20 s visually calm if you plan YouTube end-screen elements.

## What this won't do / safety
- It does not use footage, music or images the user has no rights to.
- It never overwrites the original renders; reactions write to a separate folder; finals are timestamped.
- It does not upload anything; publishing is the `youtube-publish` skill and the human's click.
- Screen recordings and overlays pass the privacy check (no names, emails, paths, notifications) before use.
