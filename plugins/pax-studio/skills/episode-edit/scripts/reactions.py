"""Composite background reactions and "flash" gags into a copy of an episode's clips.

Usage (from the show's project root):  python reactions.py config/reactions-ep01.json
Then point edit_episode.py's clips_dir at the out_dir.

Config (see reactions.example.json):
  src_dir, out_dir      originals stay untouched; out_dir gets copies with reactions composited
  width, height, fps    the episode frame (reaction boxes are in these pixel coordinates)
  regions               named boxes in the frame, e.g. a marble bust on a shelf:
                        {"bust": {"box": [x, y, w, h], "ellipse": [l, t, r, b], "feather": 9}}
                        ellipse is the visible part of the reaction, as fractions of the box
  reactions             [{"clip": "01-S1", "region": "bust", "video": ".../bust-nod.mp4", "start": 10.6, "length": 2.6}]
                        start = seconds into the clip; length = keep only this much of the reaction,
                        then hold its last frame (e.g. one nod, not three)
  flash_gags            [{"out": "13-K9", "base": ".../doubter-turn.mp4", "insert": ".../assistant-listening.mp4",
                          "insert_crop": "520:460:380:20", "box": [x, y, w, h], "flashes": [[0.35, 0.65], ...],
                          "duration": 7.0}]
                        box is in the base clip's own pixel size; the result is scaled to width x height

How it works:
- The reaction clip (from an image-to-video model) is color-matched frame by frame to the region of the original
  shot (the model drifts the lighting), then laid back over the region through a feathered ellipse mask
  (alphamerge), starting at `start`, so only the object moves and its edges blend in.
- A flash gag overlays the insert on a screen in quick on/off bursts using enable='between(t,a,b)+...'.
"""
import json, shutil, subprocess, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter

FF = imageio_ffmpeg.get_ffmpeg_exe()


def run(args):
    subprocess.run([FF, "-loglevel", "error", "-y", *args], check=True)


def region_reference(clip, t, box, size, dest):
    """Grab the region from the original clip at time t: the colors the reaction must match."""
    w, h = size
    x, y, bw, bh = box
    run(["-ss", f"{t}", "-i", str(clip), "-frames:v", "1", "-vf", f"scale={w}:{h},crop={bw}:{bh}:{x}:{y}", str(dest)])
    return dest


def color_match(src, ref_png, dest):
    """Per-frame mean/std transfer to the reference region's colors."""
    if dest.exists():
        return dest
    ref = np.asarray(Image.open(ref_png).convert("RGB")).astype(np.float32).reshape(-1, 3)
    rm, rs = ref.mean(0), ref.std(0)
    reader = imageio_ffmpeg.read_frames(str(src))
    meta = next(reader)
    w, h = meta["size"]
    writer = imageio_ffmpeg.write_frames(str(dest), (w, h), fps=meta["fps"], quality=9, macro_block_size=1)
    writer.send(None)
    for fr in reader:
        a = np.frombuffer(fr, np.uint8).reshape(h, w, 3).astype(np.float32)
        m, s = a.reshape(-1, 3).mean(0), a.reshape(-1, 3).std(0) + 1e-3
        writer.send(np.clip((a - m) / s * rs + rm, 0, 255).astype(np.uint8))
    writer.close()
    return dest


def ellipse_mask(region, dest):
    _, _, w, h = region["box"]
    l, t, r, b = region.get("ellipse", [0.1, 0.1, 0.9, 0.9])
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse((w * l, h * t, w * r, h * b), fill=255)
    m.filter(ImageFilter.GaussianBlur(region.get("feather", 9))).save(dest)
    return dest


def composite(clip, items, out, fps):
    """items: [(reaction_video, mask_png, box, start, length)]; chains one overlay per reaction."""
    args, fc, last = ["-i", str(clip)], [f"[0:v]fps={fps}[b0]"], "[b0]"
    for i, (vid, mask, (x, y, w, h), start, length) in enumerate(items):
        vi, mi = 1 + 2 * i, 2 + 2 * i
        args += ["-i", str(vid), "-loop", "1", "-i", str(mask)]
        trim = f"trim=0:{length},setpts=PTS-STARTPTS," if length else ""
        fc.append(f"[{vi}:v]{trim}scale={w}:{h},fps={fps},format=rgba,tpad=stop_mode=clone:stop_duration=600,"
                  f"setpts=PTS-STARTPTS+{start}/TB[r{i}]")
        fc.append(f"[{mi}:v]scale={w}:{h},format=gray[m{i}]")
        fc.append(f"[r{i}][m{i}]alphamerge[rm{i}]")
        fc.append(f"{last}[rm{i}]overlay={x}:{y}:shortest=1:eof_action=pass[b{i + 1}]")
        last = f"[b{i + 1}]"
    fc.append(f"{last}format=yuv420p[v]")
    run([*args, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "0:a?", "-shortest",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "copy", str(out)])


def flash_gag(g, size, fps, out_dir):
    w, h = size
    x, y, bw, bh = g["box"]
    en = "+".join(f"between(t,{a},{b})" for a, b in g["flashes"])
    crop = f"crop={g['insert_crop']}," if g.get("insert_crop") else ""
    fc = (f"[1:v]{crop}scale={bw}:{bh},eq=brightness=0.06:saturation=1.2[c];"
          f"[0:v][c]overlay={x}:{y}:enable='{en}',scale={w}:{h},fps={fps},format=yuv420p[v]")
    dur = g.get("duration", 7.0)
    run(["-i", g["base"], "-stream_loop", "-1", "-i", g["insert"],
         "-f", "lavfi", "-t", f"{dur + 1}", "-i", "anullsrc=r=44100:cl=stereo",
         "-filter_complex", fc, "-map", "[v]", "-map", "2:a", "-t", f"{dur}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", str(out_dir / f"{g['out']}.mp4")])


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf8"))
    src, out = Path(cfg["src_dir"]), Path(cfg["out_dir"])
    size, fps = (cfg.get("width", 1280), cfg.get("height", 720)), cfg.get("fps", 30)
    work = out / "_reactions"
    work.mkdir(parents=True, exist_ok=True)
    regions = cfg.get("regions", {})
    masks = {n: ellipse_mask(r, work / f"{n}-mask.png") for n, r in regions.items()}

    plan = defaultdict(list)
    for r in cfg.get("reactions", []):
        reg = regions[r["region"]]
        clip = src / f"{r['clip']}.mp4"
        ref = region_reference(clip, r["start"], reg["box"], size, work / f"{r['clip']}-{r['region']}-ref.png")
        matched = color_match(Path(r["video"]), ref, work / f"{Path(r['video']).stem}-{r['clip']}-matched.mp4")
        plan[r["clip"]].append((matched, masks[r["region"]], reg["box"], r["start"], r.get("length")))

    gag_ids = {g["out"] for g in cfg.get("flash_gags", [])}
    for p in sorted(src.glob("*.mp4")):
        if p.stem in plan:
            composite(p, plan[p.stem], out / p.name, fps); print("reaction", p.stem, len(plan[p.stem]))
        elif p.stem not in gag_ids:
            shutil.copy(p, out / p.name); print("copy    ", p.stem)
    for g in cfg.get("flash_gags", []):
        flash_gag(g, size, fps, out); print("flash   ", g["out"])
    for extra in cfg.get("copy_files", []):          # e.g. the listening loop the edit needs
        shutil.copy(extra, out / Path(extra).name)


if __name__ == "__main__":
    main()
