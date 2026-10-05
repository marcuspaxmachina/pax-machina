"""Build an .srt caption file for the final edit, or print each clip's start time (for chapters).

From the script (exact wording, timing estimated within each clip):
  python make_srt.py clips --clips-json episodes/ep01/clips.json --media-dir video/ep01r/edit \
         [--edit-config config/edit-ep01.json] [--speakers host=MARCUS assistant=CLAUDIA] -o episodes/ep01/ep01.en.srt
  python make_srt.py clips ... --starts          # print "M:SS  clip-id  first words" for chapters

From the audio (accurate timing, check spelling of names):  pip install faster-whisper
  python make_srt.py whisper video/ep01/EP01-EDIT-1005-1412.mp4 --model small -o episodes/ep01/ep01.en.srt

Clip mode rebuilds the edit timeline the same way edit_episode.py does: clips in order, each overlapping the
previous one by the dissolve (different character) or hard-cut (same character) duration. Durations are probed
from the processed clips with FFmpeg (imageio-ffmpeg). Audio tags like [pause] are stripped from the text.
"""
import argparse, json, re, subprocess, sys, textwrap
from pathlib import Path


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def duration(f):
    err = subprocess.run([ffmpeg(), "-i", str(f)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def ts(t):
    ms = int(round(max(t, 0) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def wrap(text, width=42):
    return "\n".join(textwrap.wrap(text, width)) if len(text) > width else text


def chunks(text, limit=84):
    """Split into caption-sized pieces (max 2 lines of 42), preferring sentence and comma breaks."""
    out, cur = [], ""
    for part in re.split(r"(?<=[.!?…])\s+|(?<=[,;:])\s+", text):
        if cur and len(cur) + 1 + len(part) > limit:
            out.append(cur); cur = part
        else:
            cur = f"{cur} {part}".strip()
        while len(cur) > limit:                       # very long sentence: hard split on a space
            cut = cur.rfind(" ", 0, limit)
            out.append(cur[:cut]); cur = cur[cut + 1:]
    return out + ([cur] if cur else [])


def timeline(a):
    lines = {c["id"]: c for c in json.loads(Path(a.clips_json).read_text(encoding="utf8"))}
    order = [(cid, c["voice"]) for cid, c in lines.items()]
    tr = {"dissolve": a.dissolve, "hardcut": a.hardcut}
    if a.edit_config:
        cfg = json.loads(Path(a.edit_config).read_text(encoding="utf8"))
        tr.update({k: v for k, v in cfg.get("transitions", {}).items() if k in tr})
        if cfg.get("clips"):
            order = [(i, lines[i]["voice"]) if isinstance(i, str) else (i["id"], i.get("character", lines.get(i["id"], {}).get("voice")))
                     for i in cfg["clips"]]
    t, prev, rows = a.offset, None, []
    for n, (cid, char) in enumerate(order):
        media = next((Path(a.media_dir) / f"{cid}{ext}" for ext in (".mp4", ".mp3", ".wav")
                      if (Path(a.media_dir) / f"{cid}{ext}").exists()), None)
        if media is None:
            sys.exit(f"no media for clip {cid} in {a.media_dir}")
        if n:
            t -= tr["dissolve"] if char != prev else tr["hardcut"]
        d = duration(media)
        rows.append((cid, char, t, d, lines.get(cid, {}).get("text", "")))
        t += d
        prev = char
    return rows


def from_clips(a):
    rows = timeline(a)
    if a.starts:
        for cid, _, start, _, text in rows:
            words = " ".join(re.sub(r"\[[^\]]*\]", "", text).split()[:8])
            print(f"{int(start // 60)}:{int(start % 60):02d}  {cid:<8} {words}")
        return []
    speakers = dict(s.split("=", 1) for s in a.speakers or [])
    cues = []
    for cid, char, start, dur, text in rows:
        clean = " ".join(re.sub(r"\[[^\]]*\]", " ", text).split())
        if not clean:
            continue                                  # silent cutaway
        parts = chunks(clean)
        span = max(dur - 0.15, 0.5)                   # speaking span inside the clip
        total = sum(len(p) for p in parts)
        t = start + 0.05
        for i, p in enumerate(parts):
            length = span * len(p) / total
            label = f"{speakers[char]}: " if char in speakers and i == 0 else ""
            cues.append((t, t + length, label + p))
            t += length
    return cues


def from_whisper(a):
    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, compute_type="int8")
    segs, _ = model.transcribe(a.media, vad_filter=True, language=a.language)
    cues = []
    for s in segs:
        for p in chunks(s.text.strip()):
            cues.append((s.start + a.offset, s.end + a.offset, p))
    return cues


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    c = sub.add_parser("clips")
    c.add_argument("--clips-json", required=True)
    c.add_argument("--media-dir", required=True)
    c.add_argument("--edit-config")
    c.add_argument("--dissolve", type=float, default=0.25)
    c.add_argument("--hardcut", type=float, default=0.04)
    c.add_argument("--speakers", nargs="*")
    c.add_argument("--starts", action="store_true")
    w = sub.add_parser("whisper")
    w.add_argument("media")
    w.add_argument("--model", default="small")
    w.add_argument("--language", default="en")
    for p in (c, w):
        p.add_argument("--offset", type=float, default=0.0, help="seconds to add (e.g. an intro card)")
        p.add_argument("-o", "--out")
    a = ap.parse_args()
    cues = from_clips(a) if a.mode == "clips" else from_whisper(a)
    if not cues:
        return
    # No overlapping cues (clips overlap by the transition length): end each cue just before the next starts.
    cues = [(s, min(e, cues[i + 1][0] - 0.02) if i + 1 < len(cues) else e, t) for i, (s, e, t) in enumerate(cues)]
    srt = "\n".join(f"{i}\n{ts(s)} --> {ts(e)}\n{wrap(t)}\n" for i, (s, e, t) in enumerate(cues, 1))
    if a.out:
        Path(a.out).write_text(srt, encoding="utf8")
        print("wrote", a.out, f"{len(cues)} cues, ends {ts(cues[-1][1])}")
    else:
        print(srt)


if __name__ == "__main__":
    main()
