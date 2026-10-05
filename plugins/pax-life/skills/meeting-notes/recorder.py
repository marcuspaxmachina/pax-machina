"""Meeting recorder (Windows only): captures everything playing through an output device (WASAPI loopback),
optionally mixed with the microphone, and saves an MP3 to %USERPROFILE%\\Recordings. Local only; nothing is uploaded.
Setup: pip install pyaudiowpatch imageio-ffmpeg
Run:   pythonw recorder.py   (no console window; launch it from a desktop shortcut, not from inside Claude)
Consent: many places (e.g. Massachusetts and California) require EVERYONE on a call to agree to be recorded. Ask first.
"""
import threading, time, wave, subprocess, os, sys
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import pyaudiowpatch as pa
import imageio_ffmpeg

OUT = Path.home() / "Recordings"
FF = imageio_ffmpeg.get_ffmpeg_exe()
CHUNK = 1024


class Track:
    """Reads one input device into a WAV file on a background thread."""
    def __init__(self, p, dev, path):
        self.ch = min(int(dev["maxInputChannels"]), 2) or 1
        self.rate = int(dev["defaultSampleRate"])
        self.wav = wave.open(str(path), "wb")
        self.wav.setnchannels(self.ch); self.wav.setsampwidth(2); self.wav.setframerate(self.rate)
        self.stream = p.open(format=pa.paInt16, channels=self.ch, rate=self.rate, input=True,
                             input_device_index=dev["index"], frames_per_buffer=CHUNK,
                             stream_callback=self.cb)

    def cb(self, data, frames, info, status):
        self.wav.writeframes(data)
        return (None, pa.paContinue)

    def close(self):
        self.stream.stop_stream(); self.stream.close(); self.wav.close()


class App:
    def __init__(self, root):
        self.p = pa.PyAudio()
        self.loops = list(self.p.get_loopback_device_info_generator())
        default = self.p.get_default_wasapi_loopback()["name"]
        self.root = root; root.title("Recorder"); root.attributes("-topmost", True); root.resizable(False, False)
        f = ttk.Frame(root, padding=12); f.pack()
        ttk.Label(f, text="Record from:").grid(row=0, column=0, sticky="w")
        self.dev = ttk.Combobox(f, width=48, state="readonly", values=[d["name"] for d in self.loops])
        self.dev.set(default); self.dev.grid(row=1, column=0, columnspan=2, pady=(0, 6))
        self.mic = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Include my microphone (for meetings)", variable=self.mic).grid(row=2, column=0, columnspan=2, sticky="w")
        self.btn = tk.Button(f, text="●  Record", width=16, font=("Segoe UI", 12, "bold"), bg="#2E7D32", fg="white", command=self.toggle)
        self.btn.grid(row=3, column=0, pady=10)
        tk.Button(f, text="Open folder", command=lambda: os.startfile(OUT)).grid(row=3, column=1)
        self.status = ttk.Label(f, text=f"Saves to {OUT}"); self.status.grid(row=4, column=0, columnspan=2, sticky="w")
        self.tracks = None
        root.protocol("WM_DELETE_WINDOW", self.quit)

    def toggle(self):
        if self.tracks: self.stop()
        else: self.start()

    def start(self):
        OUT.mkdir(exist_ok=True)
        self.base = OUT / datetime.now().strftime("rec-%Y-%m-%d-%H%M%S")
        loop = next(d for d in self.loops if d["name"] == self.dev.get())
        self.tracks = [Track(self.p, loop, f"{self.base}-speakers.wav")]
        # Loopback only delivers audio while something plays; play silence so the track never has gaps.
        self.silence = self.p.open(format=pa.paInt16, channels=self.tracks[0].ch, rate=self.tracks[0].rate, output=True,
                                   output_device_index=self.output_for(loop),
                                   stream_callback=lambda d, n, i, s: (b"\0" * n * 2 * self.tracks[0].ch, pa.paContinue))
        if self.mic.get():
            self.tracks.append(Track(self.p, self.p.get_default_input_device_info(), f"{self.base}-mic.wav"))
        self.t0 = time.time()
        self.btn.config(text="■  Stop", bg="#b3261e"); self.dev.config(state="disabled"); self.tick()

    def output_for(self, loop):
        name = loop["name"].replace(" [Loopback]", "")
        api = self.p.get_host_api_info_by_type(pa.paWASAPI)["index"]
        for i in range(self.p.get_device_count()):
            d = self.p.get_device_info_by_index(i)
            if d["hostApi"] == api and d["maxOutputChannels"] > 0 and d["name"] == name:
                return i
        return None

    def tick(self):
        if self.tracks:
            s = int(time.time() - self.t0)
            self.status.config(text=f"Recording  {s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}")
            self.root.after(500, self.tick)

    def stop(self):
        tracks, self.tracks = self.tracks, None
        self.silence.stop_stream(); self.silence.close()
        for t in tracks: t.close()
        self.btn.config(text="●  Record", bg="#2E7D32", state="disabled"); self.dev.config(state="readonly")
        self.status.config(text="Saving MP3…")
        self.encoder = threading.Thread(target=self.encode, args=(len(tracks), self.base))
        self.encoder.start()

    def encode(self, n, base):
        wavs = [f"{base}-speakers.wav"] + ([f"{base}-mic.wav"] if n > 1 else [])
        args = [FF, "-loglevel", "error", "-y"]
        for w in wavs: args += ["-i", w]
        if n > 1:
            args += ["-filter_complex", "[0:a]aresample=48000[a0];[1:a]aresample=48000[a1];[a0][a1]amix=inputs=2:duration=longest:normalize=0[a]", "-map", "[a]"]
        mp3 = f"{base}.mp3"
        ok = subprocess.run(args + ["-ac", "2", "-b:a", "128k", mp3], creationflags=0x08000000).returncode == 0
        if ok:
            for w in wavs: os.remove(w)
        self.root.after(0, lambda: (self.status.config(text=f"Saved {Path(mp3).name}" if ok else "MP3 failed; WAVs kept"),
                                    self.btn.config(state="normal")))

    def quit(self):
        # Never close mid-save: closing while recording used to kill the MP3 step and leave only the WAVs.
        if self.tracks: self.stop()
        if getattr(self, "encoder", None) and self.encoder.is_alive():
            self.root.after(500, self.quit); return
        self.p.terminate(); self.root.destroy()


if __name__ == "__main__":
    import socket
    lock = socket.socket()
    try: lock.bind(("127.0.0.1", 47913))  # one Recorder at a time
    except OSError:
        import ctypes; ctypes.windll.user32.MessageBoxW(0, "Recorder is already open.", "Recorder", 0x40); sys.exit()
    root = tk.Tk(); App(root); root.mainloop()
