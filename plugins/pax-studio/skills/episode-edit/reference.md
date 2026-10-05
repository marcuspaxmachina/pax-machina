# Edit playbook: real critiques and the fixes that worked

Each entry: what the reviewer said -> why it happens -> the fix (and where it lives in the scripts).
Add new pairs at the bottom as you learn them.

## Audio

### "The sigh is way too long" / "he sighs forever"
- Why: expressive TTS models stretch `[sighs]` (and sometimes `[laughs]`) unpredictably.
- Fix: in `clips.json` remove the tag or replace it with `[pause]` (or `[beat]` before a punchline), delete that
  clip's mp3, regenerate 2-3 takes (`episode-voices`), pick one, then re-animate **only that clip** in Hedra.
  Do not trim the sigh in the edit: the lip sync would drift from the audio.

### "He says the word 'lightly' out loud"
- Why: the model did not recognize the tag and read it as text.
- Fix: remove it, add only proven tags to `allowed_tags` in `cast.json`, regenerate. Listen for this in every preview.

### "Levels jump between characters"
- Fix: `"loudnorm": true` in the edit config (about -14 LUFS, YouTube's reference). If one voice is still hot,
  add `volume=-2dB` for that character via a per-character audio pass, or regenerate with lower `style`.

## On-screen characters

### "She's mouthing words on the laptop while he talks"
- Why: the overlay used the assistant's talking clips as the loop.
- Fix: render a **silent listening clip** (image-to-video: "listening, nods, blinks, mouth closed, no talking"),
  set it as `screen_overlay.loop_source`. `pingpong: true` plays it forward then reversed so the loop never jumps.
  Never fall back to talking clips.

### "The overlay doesn't sit on the screen" / "it spills over the bezel"
- Fix: re-measure the four corners on a frame from that exact render (the model can shift framing slightly
  between clips); feather the mask by 1-2 px; if a hand crosses the screen, paint a custom mask and set `mask`.

## Transitions

### "The cuts are jarring"
- Fix (built into `edit_episode.py`):
  - **different characters:** `xfade` dissolve of about **0.25 s** (`transitions.dissolve`);
  - **same character back to back:** near-hard cut of **0.04 s** (`transitions.hardcut`), which hides the tiny
    pose jump between renders without reading as a dissolve;
  - **punch-in on every other same-character cut:** crop to `iw/1.1 x ih/1.1`, biased toward the top
    (`(ih-oh)*0.3`) so the face stays centered, then scale back. A jump cut with a size change reads as intentional.

### "The punch-in cuts off his laurel / the top of her head"
- Fix: lower `punch_in` to 1.06-1.08 or lower `punch_in_y` (0.3 -> 0.15).

## Background reactions (`reactions.py`)

How they are made: crop the object (e.g. a marble bust on the shelf) from the host's frame, animate the crop with
an image-to-video model ("the bust slowly nods once"), color-match each frame to the original region, then
composite back through a **feathered ellipse mask with alphamerge** at a given second of a given clip.

### "The statue nods too much"
- Fix: nod **once, on one key line** of the episode (e.g. when the host states who he is). If the generated clip
  nods three times, set `length` to the first nod (e.g. 2.6 s); the last frame is held after that.

### "The bust should be skeptical when the doubter talks"
- Fix: a **side-eye** reaction placed at `start: 0` on the host's reply right after the doubter's dig (the bust
  is in the host's shot, so it reacts in the host's next clip).

### "Give the bust a double take on the reveal"
- Fix: a double-take reaction timed so the snap lands just **after** the reveal line's key words, not on them.

### "The bust flickers / is a different color from the room"
- Why: image-to-video models drift exposure and white balance.
- Fix: per-frame color matching (mean/std transfer to the original region) is built in; widen the feather
  (`feather` 9 -> 14) or shrink the ellipse so the composite edge falls on a uniform area.

### "The reaction steps on the joke"
- Rule: keep reaction timing **off the dialogue's key words**. Land reactions in the pause after a punchline or
  just before the next sentence. Check timing by extracting frames around `start` and listening at the same spot.

## Gags

### "Have her prank him on his old computer"
- Recipe (`flash_gags` in `reactions.py`): the assistant's listening clip, cropped to her face, flashes onto the
  doubter's old CRT screen in quick bursts (`flashes: [[0.35,0.65],[0.80,0.98],[1.10,1.32]]` = on, off, on, off),
  on a non-speaking clip of him slowly turning toward the screen. She is gone before he finishes turning: he
  turns too late. A slight `eq=brightness=0.06:saturation=1.2` makes her read as a glowing screen.

## Picture consistency

### "One character is darker / warmer than the others"
- Fix: a per-character `color` filter in the edit config, e.g. `eq=brightness=0.03:saturation=0.95`, or
  `colorbalance=rs=-0.03:bs=0.03`. Match against the host's shot on a frame grab; keep changes small.

### "It looks soft after the punch-in"
- Fix: render the source at 1080p if the plan allows; otherwise keep `punch_in` at or below 1.1.

## Delivery

### "It won't play in Windows Media Player" / "black screen with sound"
- Why: 4:4:4 or 10-bit pixel format, or moov atom at the end of the file.
- Fix (built in): `-pix_fmt yuv420p -profile:v high -movflags +faststart`, AAC audio.

### "I re-ran it but the video didn't change"
- Why: the old file was open in a player, so the save silently failed or the player kept the old copy.
- Fix (built in): every build writes `<NAME>-EDIT-<mmdd-hhmm>.mp4`. Always open the newest file.

### "FFmpeg died halfway" / "the PC froze"
- Why: one huge filter graph with dozens of inputs.
- Fix: close other apps and check free RAM first; use `--reuse` so only changed clips are re-processed; for very
  long episodes assemble in two halves and join with `-f concat -c copy`.

## Filter recipes (copy/paste)

```
# punch-in 10%, biased up
crop=iw/1.1:ih/1.1:(iw-ow)/2:(ih-oh)*0.3,scale=1280:720
# dissolve two clips (A is 12.0 s long)
[0:v][1:v]xfade=transition=fade:duration=0.25:offset=11.75[v];[0:a][1:a]acrossfade=d=0.25[a]
# feathered composite of a reaction at 10.6 s
[1:v]scale=180:320,format=rgba,setpts=PTS-STARTPTS+10.6/TB[r];[2:v]format=gray[m];[r][m]alphamerge[rm];[0:v][rm]overlay=170:10:eof_action=pass
# ping-pong loop
split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0
# flash on/off
overlay=1020:267:enable='between(t,0.35,0.65)+between(t,0.80,0.98)'
```
