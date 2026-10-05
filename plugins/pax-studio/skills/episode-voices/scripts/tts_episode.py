"""Voice an episode with the ElevenLabs text-to-speech API, pick takes, and stitch a full preview.

Usage (run from the show's project root):
  python tts_episode.py episodes/ep01/clips.json --cast config/cast.json --out audio/ep01
  python tts_episode.py ... --takes 3                 # 3 takes per line: <id>-take1.mp3 ...
  python tts_episode.py ... --only 05-S3 10-S7        # just these clips
  python tts_episode.py ... --pick 05-S3=2            # copy take 2 to 05-S3.mp3 (the chosen take)
  python tts_episode.py ... --preview --open          # stitch <id>.mp3 files in id order and open the result
  python tts_episode.py --cast config/cast.json --list-voices | --credits

clips.json: [{"id": "01-S1", "voice": "host", "text": "[dryly] I have commanded legions. [beat] ..."}]
cast.json:  {"model": "...", "allowed_tags": [...], "voices": {"host": {"voice_id": "...", "settings": {...}}}}

The API key comes from the ELEVENLABS_API_KEY environment variable or a git-ignored .env file in the current
folder. It is never printed or logged. Existing mp3 files are skipped: delete one to regenerate it.
"""
import argparse, json, os, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

API = "https://api.elevenlabs.io/v1"


def api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    env = Path(".env")
    if not key and env.exists():
        for line in env.read_text(encoding="utf8").splitlines():
            if line.strip().startswith("ELEVENLABS_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("Set ELEVENLABS_API_KEY (environment or .env). Do not paste the key into chat.")
    return key


def call(key, path, body=None, accept="application/json"):
    req = urllib.request.Request(f"{API}{path}", data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": accept})
    return urllib.request.urlopen(req, timeout=300).read()


def check_tags(clips, allowed):
    """Warn about audio tags the model may read aloud instead of performing."""
    allowed = {t.lower() for t in allowed}
    for c in clips:
        for tag in re.findall(r"\[([^\]]+)\]", c["text"]):
            if allowed and tag.lower() not in allowed:
                print(f"warn {c['id']}: tag [{tag}] is not in allowed_tags; it may be spoken aloud")


def generate(args, cast, key):
    clips = json.loads(Path(args.clips).read_text(encoding="utf8"))
    check_tags(clips, cast.get("allowed_tags", []))
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    model = args.model or cast.get("model")
    fmt = cast.get("output_format", "mp3_44100_128")
    for c in clips:
        if args.only and c["id"] not in args.only:
            continue
        v = cast["voices"][c["voice"]]
        for t in range(1, args.takes + 1):
            dest = out / (f"{c['id']}.mp3" if args.takes == 1 else f"{c['id']}-take{t}.mp3")
            if dest.exists():
                print("skip", dest.name); continue
            body = {"text": c["text"], "model_id": model, "voice_settings": v.get("settings", {})}
            dest.write_bytes(call(key, f"/text-to-speech/{v['voice_id']}?output_format={fmt}", body, "audio/mpeg"))
            print("ok  ", dest.name, f"{dest.stat().st_size // 1024} KB")


def pick(args):
    out = Path(args.out)
    for p in args.pick:
        cid, take = p.split("=")
        shutil.copy(out / f"{cid}-take{take}.mp3", out / f"{cid}.mp3")
        print("picked", cid, "take", take)


def preview(args):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = Path(args.out)
    files = sorted(p for p in out.glob("*.mp3") if "-take" not in p.stem and "PREVIEW" not in p.stem)
    if not files:
        sys.exit("No <id>.mp3 files to stitch (pick takes first).")
    lst = out / "_preview.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in files), encoding="utf8")
    dest = out / f"{out.name.upper()}-FULL-PREVIEW-{time.strftime('%m%d-%H%M')}.mp3"   # timestamped: never blocked by a player
    subprocess.run([ff, "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:a", "libmp3lame", "-b:a", "160k", str(dest)], check=True)
    print("wrote", dest, f"({len(files)} clips)")
    if args.open:
        if sys.platform == "win32":
            os.startfile(dest)  # noqa: opens in the default player
        else:
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", str(dest)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="?")
    ap.add_argument("--cast", required=True)
    ap.add_argument("--out")
    ap.add_argument("--model")
    ap.add_argument("--takes", type=int, default=1)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--pick", nargs="*")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--list-voices", action="store_true")
    ap.add_argument("--credits", action="store_true")
    args = ap.parse_args()
    cast = json.loads(Path(args.cast).read_text(encoding="utf8"))
    if args.list_voices:
        for v in json.loads(call(api_key(), "/voices"))["voices"]:
            print(f"{v['name']:<30} {v['voice_id']}")
        return
    if args.credits:
        s = json.loads(call(api_key(), "/user/subscription"))
        print(f"used {s.get('character_count')} of {s.get('character_limit')} characters")
        return
    if args.pick:
        pick(args)
    elif args.clips:
        generate(args, cast, api_key())
    if args.preview:
        preview(args)


if __name__ == "__main__":
    main()
