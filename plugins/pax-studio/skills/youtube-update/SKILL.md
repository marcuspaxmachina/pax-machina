---
name: youtube-update
description: Updates an EXISTING YouTube video without re-uploading - title, description and links (e.g. add the blog guide or toolkit link at the top), chapters, thumbnail, tags, end screen, cards, playlists, pinned comment and captions/subtitles (an .srt built from the clips JSON or a Whisper transcript) - explains what Studio's editor can change in place versus what needs a new upload, and keeps YouTube and the blog in sync. Use when the user says "add the blog link to the video", "update the description", "fix the chapters", "upload captions", "make subtitles", "change the thumbnail", "pin a comment", or "the article is live, update YouTube".
---

# YouTube update (no re-upload)

Everything here edits a live video in YouTube Studio with the human signed in (`browser-handoff` skill in the
pax-life plugin). You prepare the new text/files, fill the fields, and the human clicks **Save**.
Script: `scripts/make_srt.py` next to this file.

## What can change in place vs what needs a new upload

| Change | In place? | Where |
|---|---|---|
| Title, description, links, tags, category | Yes | Studio -> Content -> video -> Details |
| Chapters | Yes (edit the timestamps in the description) | Details |
| Thumbnail | Yes (phone-verified channel) | Details |
| Playlists, audience, altered-content setting, visibility | Yes | Details |
| Captions/subtitles | Yes | Studio -> Subtitles |
| End screen, cards | Yes | Details -> Video elements |
| Trim the start/end, **cut out sections** | Yes, Studio **Editor** (re-processes; URL, views, comments kept) | Editor -> Trim & cut |
| Blur faces or a custom area | Yes, Editor -> Blur | Editor |
| Add music from the YouTube Audio Library | Yes, Editor -> Audio | Editor |
| New footage, re-voiced lines, re-animated clips, new reactions, color changes | **No: new upload** | `youtube-publish` |

Notes: Editor changes can take a while to process and, at time of writing, saving Editor changes could be
blocked on videos with very many views unless the channel is in the Partner Program. A new upload gets a new
URL; update the blog embed and links (`blog-publish`) and consider setting the old video to Unlisted with a card
or pinned comment pointing to the new one.

## Description and links
1. Read the current description (Studio Details, or `episodes/<ep>/youtube-description.txt` if it is current).
2. Edit `youtube-description.txt` first (source of truth), keeping the template order from `youtube-publish`:
   guide link and "who is the host" link on the first lines, then the summary, toolkit/download link, chapters,
   tools used, disclosures.
3. Show the diff to the human; after approval paste it into Studio and the human clicks Save.
4. Links may not be clickable until the channel's one-time "advanced features" verification is done.

## Chapters
`python scripts/make_srt.py clips --clips-json episodes/<ep>/clips.json --media-dir <processed clips> --edit-config config/edit-<ep>.json --starts`
prints each clip's start time in the final cut. Rules: first at 0:00, at least 3, each at least 10 s.
If the video was trimmed in the Editor, shift every later timestamp by the removed duration.

## Captions (.srt)
Two ways to get correct timings for the **final** edit:
- **From the script (exact wording):**
  `python scripts/make_srt.py clips --clips-json episodes/<ep>/clips.json --media-dir video/<ep>/edit --edit-config config/edit-<ep>.json --speakers host=MARCUS doubter=COMMODUS -o episodes/<ep>/<ep>.en.srt`
  It rebuilds the edit timeline (clip durations probed with FFmpeg, minus each dissolve/hard-cut overlap), strips
  audio tags, and spreads each line's text across the clip in caption-sized chunks. `--offset` adds a title card.
- **From the audio (accurate timing):** `pip install faster-whisper`, then
  `python scripts/make_srt.py whisper <final cut>.mp4 --model small -o episodes/<ep>/<ep>.en.srt`.
  Fix names and invented words against the script.
- Check: open the .srt next to the video (VLC/most players load a same-name .srt) and scrub 4-5 spots,
  including the end. Drift at the end means a clip list or transition mismatch.
- Upload: Studio -> Subtitles -> the video -> Add language (English) -> Subtitles -> Add -> **Upload file ->
  With timing** -> choose the .srt -> Publish (human click).
- **Review auto-captions** too: Studio shows auto-generated captions per language; fix character names or
  unpublish them if your uploaded track is better.

## Thumbnail, tags, playlists, end screen, cards
- Thumbnail: 1280x720 under 2 MB; Details -> Thumbnail -> Upload file. Keep the previous file (`thumbnail-v1.jpg`).
- End screen: Details -> Video elements -> End screen; last 5-20 s; subscribe + newest episode/playlist.
- Cards: at the moments the script mentions the guide, the toolkit, or another episode.
- Playlists: one per series; add the video and its Shorts' long-form counterpart.

## Pinned comment
Post a comment as the channel (e.g. "📜 Full guide with every prompt: <link>"), then pin it (comment menu ->
Pin). The human posts and pins, or approves your text and you click with them watching.

## Keep YouTube and the blog in sync (run whenever a blog article or download is published or updated)
- [ ] The matching video description's first line links the article (not the blog home page).
- [ ] Toolkit/download link in descriptions points at the current release.
- [ ] Every older video that mentions the topic gets the new link (search the channel's descriptions).
- [ ] Pinned comment updated.
- [ ] Channel links (Customization -> Basic info -> Links) include blog, About and toolkit.
- [ ] The article embeds the right video URL; cross-links use post IDs (`blog-publish`).
- [ ] If a video was re-uploaded, the old URL is replaced everywhere (blog, descriptions, cards, README).
- [ ] Log the change in `episodes/<ep>/production-plan.md` with the date.

## What this won't do / safety
- It does not click Save, Publish, Delete or any verification; the human does.
- It never deletes a video or comments without an explicit request.
- It keeps real-identity details out of descriptions, captions and comments; captions pass the privacy check
  (Whisper can transcribe a name the script never contained).
- Changing title/thumbnail often can confuse viewers; batch changes and record them.
