"""Transcribe a recording locally with faster-whisper (CPU, nothing uploaded). Writes <recording>.txt next to it,
with [h:mm:ss] timestamps. Usage: python transcribe.py [path] [start_seconds]
(default path: newest rec-*.mp3 in ~/Recordings). Works in 5-minute chunks so it runs even when RAM is tight; passing
start_seconds resumes a run that stopped and appends to the existing .txt.
Setup: pip install faster-whisper imageio-ffmpeg numpy   (the model downloads once on first run, then works offline)
Works on Windows, macOS and Linux.
"""
import sys, time, subprocess, tempfile, os
from pathlib import Path
import imageio_ffmpeg
from faster_whisper import WhisperModel

FF = imageio_ffmpeg.get_ffmpeg_exe()
CHUNK = 300
src = Path(sys.argv[1]) if len(sys.argv) > 1 else max((Path.home() / "Recordings").glob("rec-*.mp3"), key=lambda p: p.stat().st_mtime)
start = int(float(sys.argv[2])) if len(sys.argv) > 2 else 0
probe = subprocess.run([FF, "-i", str(src)], capture_output=True, text=True).stderr
h, m, s = probe.split("Duration: ")[1].split(",")[0].split(":")
duration = int(h) * 3600 + int(m) * 60 + float(s)


def free_ram():
    """Free RAM in bytes (Windows, Linux, macOS); 0 if unknown, which picks the safe small model."""
    try:
        if os.name == "nt":
            import ctypes
            class _Mem(ctypes.Structure):
                _fields_ = [("len", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in
                           ("total", "avail", "ptotal", "pavail", "vtotal", "vavail", "xavail")]
            m = _Mem(); m.len = ctypes.sizeof(_Mem); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.avail
        if Path("/proc/meminfo").exists():
            for line in Path("/proc/meminfo").read_text().splitlines():
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
        out = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout   # macOS
        page = 16384 if "16384" in out.splitlines()[0] else 4096
        pages = sum(int(l.split(":")[1].strip(" .")) for l in out.splitlines()
                    if l.startswith(("Pages free", "Pages inactive", "Pages speculative")))
        return pages * page
    except Exception:
        return 0


avail = free_ram()
# The big model needs ~1.5 GB; during calls RAM is often under 1 GB, so fall back to the small English model.
name = "distil-large-v3" if avail > 2 * 1024**3 else "small.en"
print(f"free RAM {avail / 1024**3:.1f} GB -> model {name}", flush=True)
model = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=2)
out = src.with_suffix(".txt")
t0 = time.time()
with out.open("a" if start else "w", encoding="utf-8") as f, tempfile.TemporaryDirectory() as tmp:
    for off in range(start, int(duration) + 1, CHUNK):
        wav = os.path.join(tmp, "chunk.wav")
        subprocess.run([FF, "-loglevel", "error", "-y", "-ss", str(off), "-t", str(CHUNK), "-i", str(src),
                        "-ac", "1", "-ar", "16000", wav], check=True)
        segments, _ = model.transcribe(wav, language="en", vad_filter=True, beam_size=1)
        for seg in segments:
            t = int(off + seg.start)
            f.write(f"[{t // 3600}:{t // 60 % 60:02d}:{t % 60:02d}] {seg.text.strip()}\n")
        f.flush()
        print(f"done to {min(off + CHUNK, duration) / 60:.1f} min", flush=True)
print(f"{src.name}: {duration / 60:.1f} min audio transcribed in {(time.time() - t0) / 60:.1f} min -> {out}")
