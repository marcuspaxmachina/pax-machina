---
name: character-art
description: Creates consistent character art for an AI-hosted show with Gemini in the browser - likeness from the user's own photos, 6-8 variations, plain-language iteration on wardrobe and background, era-appropriate sets, real UI screenshots on in-scene screens - and locks one "final" image per character. Use when the user says "design the host", "make character art", "new look for Commodus", "put my screen on his laptop", "redo the background", or needs art for animation.
---

# Character art (Gemini in the browser)

The goal is **one locked image per character** (`brand/<name>-final.jpg`) that every episode reuses, so the
character looks the same in every clip. Animation tools lip-sync best from a 16:9 medium shot, head and shoulders
clearly visible, mouth closed, facing the camera.

## Step 1: sign in (human)
Open https://gemini.google.com with the Playwright browser. Follow the `browser-handoff` skill (pax-life plugin):
the human signs in with the show's account; you take over once the chat box is visible. Use a separate account for
the show if the creator wants to stay anonymous.

## Step 2: gather inputs
- **Likeness photos (optional):** only photos the user has the rights to and that show a person who consented
  (usually the user themself). Ask the user to pick 2-3 clear, well-lit face photos. Strip EXIF/GPS first
  (e.g. re-save with Pillow, `Image.open(p).save(out)` without `exif=`). Never use photos of other real people.
- **Style reference (optional):** a screenshot of a style the user likes (e.g. "semi-realistic graphic-novel
  illustration, bold inked outlines, painterly shading, warm moody light").
- **Screen content (optional):** real UI screenshots to place on in-scene screens (laptop, monitor, old PC).
  **Blur or crop private details first**: names, emails, file paths, account names, notifications, tabs.

## Step 3: first prompt
Upload the photos via the attach button (if the file chooser does not open, retry with Playwright
`setInputFiles` on the `input[type=file]`). Then a prompt like:

```
Using the face in these photos as the likeness, create a 16:9 illustration in <style>.
Character: <name>, <role>, <age>, <wardrobe>. Expression: <neutral-friendly, mouth closed>.
Setting: <era-appropriate background>. Medium shot, head and shoulders clearly visible,
facing the camera, single character. No text, no logos, no watermark.
```

## Step 4: variations, then iterate in plain language
1. When one result is close, say: "Give me 6-8 variations of this one, same face and style."
2. Present the options to the user (download them and open a contact sheet, or point at the browser tab).
3. Iterate with short plain-language edits, one change at a time:
   - "Same image, but swap the headphones for nothing and add a gold shoulder clasp."
   - "Keep everything, make the background an old Roman study with scrolls and a marble bust."
   - "Put this screenshot on the laptop screen, keep the perspective of the screen." (upload the blurred screenshot)
4. Keep a log in `brand/art-log.md`: prompt, what changed, file name, the user's verdict.

## Style rules that saved re-dos
- **Era-appropriate backgrounds per character.** A period character (the host) gets a period set with one modern
  object as the joke (a sleek laptop among antiques). A modern character gets a modern studio. The doubter can be
  "stuck in the past" (e.g. a beige 1990s PC showing a dial-up "connecting..." screen in a Roman chamber).
- **No neon text for period characters.** Use carved stone, bronze or painted lettering (a marble plaque in Roman
  capitals) instead of a neon sign.
- **Real UI on in-scene screens.** Ask for the actual screenshot to be placed on the screen; invented UI looks fake.
  Note the screen's four corners in the final image; the `episode-edit` skill can overlay video there later.
- **Leave room for reactions.** If a background object should react later (a bust nodding, a painting rolling its
  eyes), keep it fully visible, well lit and not overlapped by the character.
- Same art style, lighting direction and color temperature across the whole cast.
- Check hands, eyes, glasses, text and laurels/jewellery at full size; ask for a fix before locking.

## Step 5: download and lock
- Download the chosen image (the download button in the image viewer; or capture the image URL and save it).
- Save as `brand/<name>-vN.jpg` for drafts and copy the approved one to `brand/<name>-final.jpg`.
- Record in `show-bible.md`: file name, date, one-paragraph description of the look and set.
- **Gate:** the human approves each final. Never overwrite a final; make `-final-v2` and update the bible.

## Disclosure
If the art is a **realistic likeness of a real person** (including the creator), or realistic-looking synthetic
people, YouTube requires the "altered or synthetic content" disclosure on upload. Clearly stylized, obviously
animated characters may not need it; when in doubt, disclose. Mention the AI art tool in the description.

## What this won't do / safety
- No photos of people who have not consented; no celebrities or real public figures' likenesses.
- No private details on in-scene screens: blur first, then upload.
- It does not sign in, buy a plan or accept terms; the human does (`browser-handoff`).
- It does not describe or copy the user's private photos anywhere public (prompts, blog, repo).
- Check the image tool's current terms for commercial use before monetizing.
