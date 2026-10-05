"""Assemble an episode from its animated clips with FFmpeg (via imageio-ffmpeg).

Usage (from the show's project root):  python edit_episode.py config/edit-ep01.json [--reuse]

Config (see edit.example.json):
  clips_dir      folder with <id>.mp4 per clip (e.g. video/ep01, or video/ep01r after reactions.py)
  clips_json     episodes/<ep>/clips.json; gives the clip order and each clip's character ("voice")
  clips          optional explicit list: ["01-S1", {"id": "13-K9", "character": "doubter"}, ...]
  transitions    {"dissolve": 0.25, "hardcut": 0.04, "punch_in": 1.1, "punch_in_y": 0.3}
  color          optional per-character ffmpeg filters for consistency, e.g. {"doubter": "eq=brightness=0.03"}
  screen_overlay optional: put a silent "listening" loop on a screen in some characters' shots
  loudnorm       optional true: normalize the final mix to about -14 LUFS
  out_dir, name  where the timestamped final goes

Rules baked in (see reference.md, the edit playbook):
- different characters: xfade dissolve; same character back to back: near-hard cut, and every other
  same-character cut gets a punch-in crop so the jump looks intentional;
- the on-screen character uses a listening loop played forward then reversed, never talking clips;
- final is H.264 high profile, yuv420p, +faststart (plays in Windows Media Player and on YouTube);
- each build writes a new timestamped file, so a copy open in a player never blocks the save.
"""
import argparse, json, re, subprocess, sys, time
from pathlib import Path
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()


def run(args):
    subprocess.run([FF, "-loglevel", "error", "-y", *args], check=True)


def probe(f):
    return subprocess.run([FF, "-i", str(f)], capture_output=True, text=True).stderr


def duration(f):
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", probe(f)).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def has_audio(f):
    return "Audio:" in probe(f)


def clip_list(cfg):
    voices = {}
    if cfg.get("clips_json"):
        voices = {c["id"]: c["voice"] for c in json.loads(Path(cfg["clips_json"]).read_text(encoding="utf8"))}
    items = cfg.get("clips") or list(voices)
    out = []
    for it in items:
        cid, char = (it, voices.get(it)) if isinstance(it, str) else (it["id"], it.get("character", voices.get(it["id"])))
        if char is None:
            sys.exit(f"clip {cid}: unknown character (add it to clips_json or give 'character')")
        out.append((cid, char, Path(cfg["clips_dir"]) / f"{cid}.mp4"))
    missing = [str(p) for _, _, p in out if not p.exists()]
    if missing:
        sys.exit("missing clips:\n  " + "\n  ".join(missing))
    return out


def corners_arg(c):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = c["tl"], c["tr"], c["bl"], c["br"]
    return f"x0={x0}:y0={y0}:x1={x1}:y1={y1}:x2={x2}:y2={y2}:x3={x3}:y3={y3}"


def make_mask(c, w, h, dest):
    """White quad on black at the screen's corners, slightly softened."""
    from PIL import Image, ImageDraw, ImageFilter
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([tuple(c["tl"]), tuple(c["tr"]), tuple(c["br"]), tuple(c["bl"])], fill=255)
    m.filter(ImageFilter.GaussianBlur(1)).save(dest)
    return dest


def build_loop(so, norm, w, h, dest):
    """Silent listening loop: optional crop to the character, then forward + reversed so it never jumps."""
    crop = f",crop={so['crop']},scale={w}:{h}" if so.get("crop") else ""
    pp = "split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0" if so.get("pingpong", True) else "null"
    run(["-i", so["loop_source"], "-an", "-filter_complex", f"[0:v]{norm}{crop},{pp}[v]",
         "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(dest)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--reuse", action="store_true", help="reuse processed clips in edit/ if present")
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text(encoding="utf8"))
    w, h, fps = cfg.get("width", 1280), cfg.get("height", 720), cfg.get("fps", 30)
    tr = {"dissolve": 0.25, "hardcut": 0.04, "punch_in": 1.1, "punch_in_y": 0.3, **cfg.get("transitions", {})}
    norm = f"scale={w}:{h},fps={fps},format=yuv420p,setsar=1"
    clips = clip_list(cfg)
    edir = Path(cfg["clips_dir"]) / "edit"
    edir.mkdir(exist_ok=True)

    so = cfg.get("screen_overlay")
    if so:
        loop = edir / "_screen-loop.mp4"
        build_loop(so, norm, w, h, loop)
        mask = Path(so["mask"]) if so.get("mask") else make_mask(so["corners"], w, h, edir / "_screen-mask.png")

    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-ar", "44100", "-ac", "2"]
    processed, prev, zoomed = [], None, False
    for cid, char, src in clips:
        zoom = (not zoomed) if char == prev else False       # every other same-character cut
        zoomed, prev = zoom, char
        out = edir / f"{cid}.mp4"
        processed.append((out, char))
        if a.reuse and out.exists():
            continue
        z = f",crop=iw/{tr['punch_in']}:ih/{tr['punch_in']}:(iw-ow)/2:(ih-oh)*{tr['punch_in_y']},scale={w}:{h}" if zoom else ""
        col = "," + cfg["color"][char] if cfg.get("color", {}).get(char) else ""
        audio_in = [] if has_audio(src) else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        if so and char in so.get("on", []):
            ai = "0:a" if not audio_in else "3:a"
            fc = (f"[0:v]{norm}{col}[bg];[1:v]{norm},format=rgba,perspective={corners_arg(so['corners'])}:sense=destination[w];"
                  f"[2:v]scale={w}:{h},format=gray[m];[w][m]alphamerge[s];[bg][s]overlay=shortest=1{z},format=yuv420p[v]")
            run(["-i", str(src), "-stream_loop", "-1", "-i", str(loop), "-loop", "1", "-i", str(mask), *audio_in,
                 "-filter_complex", fc, "-map", "[v]", "-map", ai, "-shortest", *enc, str(out)])
        else:
            ai = "0:a" if not audio_in else "1:a"
            run(["-i", str(src), *audio_in, "-vf", norm + col + z, "-map", "0:v", "-map", ai, "-shortest", *enc, str(out)])
        print("clip", cid, char, "punch-in" if zoom else "")

    # Assemble: one xfade/acrossfade chain. Memory grows with clip count; close other apps for long episodes.
    args, fc = [], []
    for f, _ in processed:
        args += ["-i", str(f)]
    vlast, alast = "[0:v]", "[0:a]"
    t = duration(processed[0][0])
    for i in range(1, len(processed)):
        d = tr["dissolve"] if processed[i][1] != processed[i - 1][1] else tr["hardcut"]
        off = t - d
        fc.append(f"{vlast}[{i}:v]xfade=transition=fade:duration={d}:offset={off:.3f}[v{i}]")
        fc.append(f"{alast}[{i}:a]acrossfade=d={d}[a{i}]")
        vlast, alast = f"[v{i}]", f"[a{i}]"
        t = off + duration(processed[i][0])
    if cfg.get("loudnorm"):
        fc.append(f"{alast}loudnorm=I=-14:TP=-1.5:LRA=11[an]")
        alast = "[an]"
    if not fc:
        fc = ["[0:v]null[vo];[0:a]anull[ao]"]; vlast, alast = "[vo]", "[ao]"
    out_dir = Path(cfg.get("out_dir", cfg["clips_dir"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / f"{cfg.get('name', 'EPISODE')}-EDIT-{time.strftime('%m%d-%H%M')}.mp4"
    run([*args, "-filter_complex", ";".join(fc), "-map", vlast, "-map", alast,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
         "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(final)])
    print("wrote", final, f"{t / 60:.1f} min")


if __name__ == "__main__":
    main()
