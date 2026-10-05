"""Cut vertical YouTube Shorts (1080x1920) from an episode's processed clips.

Usage (from the show's project root):  python make_shorts.py config/shorts-ep01.json [--only name ...]

Layout: the 16:9 shot centered, a blurred and darkened copy filling the frame behind it, a hook title on top
(one drawtext per line), a brand line and a footer near the bottom.

Config (see shorts.example.json):
  clips_dir   processed clips (video/<ep>/edit from edit_episode.py, so overlays and reactions are included)
  out_dir     where <name>.mp4 files go
  font        a .ttf/.otf file (bold display fonts read best on phones)
  brand, footer, colors
  shorts      {"short-01-name": {"clips": ["03-S2", "04-C2"], "hook": ["LINE ONE", "LINE TWO"],
                                 "start": 0.0, "max_seconds": 59}}
"""
import argparse, json, subprocess, sys
from pathlib import Path
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()


def default_font():
    for f in ["C:/Windows/Fonts/impact.ttf", "/System/Library/Fonts/Supplemental/Impact.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if Path(f).exists():
            return f
    sys.exit("Set 'font' in the config to a .ttf file.")


def esc_path(p):
    return p.replace("\\", "/").replace(":", "\\:")


def esc_text(t):
    return t.replace("\\", "\\\\").replace("'", "\u2019").replace(":", "\\:").replace("%", "\\%")


def text(font, t, y, size, color, border):
    return (f"drawtext=fontfile='{esc_path(font)}':text='{esc_text(t)}':fontsize={size}:fontcolor={color}:"
            f"borderw=6:bordercolor={border}:x=(w-text_w)/2:y={y}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text(encoding="utf8"))
    src, out = Path(cfg["clips_dir"]), Path(cfg["out_dir"])
    out.mkdir(parents=True, exist_ok=True)
    font = cfg.get("font") or default_font()
    col = {"title": "white", "brand": "0xffd666", "footer": "white", "border": "0x2b2421", **cfg.get("colors", {})}
    for name, s in cfg["shorts"].items():
        if a.only and name not in a.only:
            continue
        clips, n = s["clips"], len(s["clips"])
        args = []
        for c in clips:
            args += ["-i", str(src / f"{c}.mp4")]
        # Normalize every input (size, SAR, fps, sample rate) or concat fails on mismatched streams.
        pre = "".join(f"[{i}:v]scale=1280:720,setsar=1,fps=30[v{i}];[{i}:a]aresample=44100[s{i}];" for i in range(n))
        cat = pre + "".join(f"[v{i}][s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]"
        titles = ",".join(text(font, line, 200 + i * 112, 96, col["title"], col["border"]) for i, line in enumerate(s["hook"]))
        extras = []
        if cfg.get("brand"):
            extras.append(text(font, cfg["brand"], 1500, 54, col["brand"], col["border"]))
        if cfg.get("footer"):
            extras.append(text(font, cfg["footer"], 1590, 48, col["footer"], col["border"]))
        fc = (f"{cat};[cv]split[a1][b1];"
              f"[a1]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5,eq=brightness=-0.12[bg];"
              f"[b1]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2,{','.join([titles, *extras])},format=yuv420p[v]")
        trim = []
        if s.get("start"):
            trim += ["-ss", str(s["start"])]
        if s.get("max_seconds"):
            trim += ["-t", str(s["max_seconds"])]
        dst = out / f"{name}.mp4"
        subprocess.run([FF, "-loglevel", "error", "-y", *args, "-filter_complex", fc, "-map", "[v]", "-map", "[ca]",
                        *trim, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", "30",
                        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(dst)], check=True)
        print("wrote", dst)


if __name__ == "__main__":
    main()
