---
name: meeting-notes
description: Records a meeting on a Windows PC (system audio plus microphone), transcribes it locally with Whisper, and turns it into minutes (Agenda / Notes / Next Steps) and a task list. Use when the user says "record this meeting", "put the recorder up", "recording done", "process the recording", or asks for minutes or notes from a call.
---

# Meeting notes: record, transcribe, minutes, tasks

*"I listened to the Senate for forty years. Now Claudia takes the notes." — Marcus*

Two scripts sit next to this file: `recorder.py` (**Windows only**) and `transcribe.py` (Windows, macOS, Linux).
Recordings go to `%USERPROFILE%\Recordings` (`~/Recordings`). Nothing is uploaded while recording or transcribing.

## 0. One-time setup

1. Install Python 3.10+ if needed, then:
   `pip install pyaudiowpatch faster-whisper imageio-ffmpeg numpy`
   (`pyaudiowpatch` is Windows only; on macOS/Linux skip it and use any recorder that saves MP3, then start at step 2.)
2. Make a desktop shortcut so the Recorder runs **outside** Claude (PowerShell, run once):
   ```powershell
   $skill = "<full path to this skill folder>"
   $pyw = (Get-Command pythonw).Source
   $s = (New-Object -ComObject WScript.Shell).CreateShortcut("$env:USERPROFILE\Desktop\Recorder.lnk")
   $s.TargetPath = $pyw; $s.Arguments = "`"$skill\recorder.py`""; $s.WorkingDirectory = $skill; $s.Save()
   ```
3. The first transcription downloads the Whisper model (a few hundred MB to ~1.5 GB) once; after that it is offline.

## 1. Record (Windows)

- **Consent first.** Many US states (e.g. Massachusetts and California) and many countries require **everyone** on
  the call to agree. Remind the user to ask: "Mind if I record this for my notes?"
- **Launch detached**, never as a child process of Claude (if Claude restarts, a child Recorder dies mid-meeting):
  `explorer.exe "$env:USERPROFILE\Desktop\Recorder.lnk"`
- Only one Recorder can run (it holds a local lock); a second launch shows "Recorder is already open".
- The user clicks **Record** and **Stop**. "Include my microphone" is on by default. It saves
  `rec-YYYY-MM-DD-HHMMSS.mp3`. Closing the window while recording or saving is safe: it finishes the MP3 first.
- To check it is really recording: the WAVs show 0 bytes in Explorer while open, so read the live size:
  `[IO.File]::Open($path,'Open','Read','ReadWrite').Length`
- **Recovery:** if the Recorder dies before saving, the audio is in `rec-*-speakers.wav` and `rec-*-mic.wav`.
  Mix them with the ffmpeg that imageio-ffmpeg installed
  (`python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"`):
  ```
  <ffmpeg> -i rec-X-speakers.wav -i rec-X-mic.wav -filter_complex "[0:a]aresample=48000[a0];[1:a]aresample=48000[a1];[a0][a1]amix=inputs=2:duration=longest:normalize=0[a]" -map "[a]" -ac 2 -b:a 128k rec-X.mp3
  ```

## 2. Transcribe (when the user says "recording done")

Run in the background: `python <skill folder>/transcribe.py <file.mp3> [start_seconds]`
(no path = newest `rec-*.mp3` in `~/Recordings`).
- CPU only, in 5-minute chunks. Uses `distil-large-v3` when more than 2 GB RAM is free, otherwise `small.en`.
- Writes `<file>.txt` with `[h:mm:ss]` lines next to the recording.
- **Resume after a crash** (e.g. `mkl_malloc` = out of memory): delete the lines from the last unfinished 5-minute
  chunk, then rerun with that chunk's start in seconds (e.g. `1500`); it appends.
- RAM is often tight during calls (browsers, meeting apps). If it keeps failing, ask the user to close apps.
- There are no speaker labels. Infer who said what from context and **flag uncertain names or attributions**.

## 3. Minutes and tasks

1. If a calendar connector is available, find the meeting by the recording's start time for its subject,
   attendees and agenda. Otherwise ask the user for those.
2. If an email connector is available, check whether someone already sent notes. If so, draft a reply-all with only
   what they missed; otherwise draft full minutes.
3. Format: **Agenda / Notes / Next Steps**, with an **owner and due date** on every next step. Ask the user how they
   sign off, the first time.
4. Email = **draft only**. Never send.
5. Give a task table (task, owner, due) ready for the user's task app (Planner, To Do, Todoist, Asana...). Add the
   tasks only if the user asks and a connector exists.
6. Leave small talk and anything personal out of the minutes.

## Privacy

- Keep personal recordings out of work systems (and work recordings out of personal ones). Ask if unsure.
- Delete recordings and transcripts when the user says they are done with them.

## What this won't do

- It won't record anyone without reminding the user to get consent.
- It won't upload audio or transcripts anywhere; transcription runs on the user's computer.
- It won't send emails or post minutes. Drafts only.
- It won't guess silently: uncertain names, numbers and attributions are flagged for the user to check.
