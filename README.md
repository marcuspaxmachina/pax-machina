# Pax Machina Toolkit

Free Claude Code skills from **Marcus**, the Roman emperor lost in 2026, and **Claudia** (Claude Code, personified).

- 📺 Channel: [youtube.com/@MarcusPaxMachina](https://www.youtube.com/@MarcusPaxMachina)
- 📜 Guides: [paxmachina.blog](https://paxmachina.blog), starting with *How to get Claude Code*
- 🧰 The full walk-through of this toolkit: *The Pax Machina Toolkit* on the blog

Two bundles ("plugins"). Install one or both.

| Plugin | For | Skills |
|---|---|---|
| **pax-life** | Running parts of your life with Envoys | envoy-starter, envoy-inbox, subscription-audit, meeting-notes, browser-handoff, attention-alert |
| **pax-studio** | Making an AI-hosted YouTube channel | episode-pipeline, character-art, episode-voices, hedra-animation, episode-edit, youtube-shorts, youtube-publish, youtube-update, blog-publish |

## Install (recommended): Claude Code plugin marketplace

In Claude Code (terminal, VS Code or desktop), type:

```
/plugin marketplace add https://github.com/MarcusPaxMachina/pax-machina.git
/plugin install pax-life@pax-machina
/plugin install pax-studio@pax-machina
```

Updates: `/plugin marketplace update pax-machina`. Remove: `/plugin uninstall pax-life@pax-machina`.

Skills load automatically. Just ask in plain words, e.g. *"set up a new Envoy for my bills"*, *"audit my subscriptions
from this bank export"*, *"record my next meeting"*, *"add captions to my last video"*.

## Install (manual): download the ZIP

1. Download the ZIP from the repository's **Releases** page (or *Code → Download ZIP*).
2. Copy the skill folders you want from `plugins/<plugin>/skills/` into your personal skills folder:
   - **Windows:** `%USERPROFILE%\.claude\skills\`
   - **Mac / Linux:** `~/.claude/skills/`
3. Restart Claude Code. Each folder with a `SKILL.md` is now a skill in every project.

## Where things live

```
~/.claude/skills/            your personal skills (manual install)
~/Projects/                  one folder per Envoy (any location works)
  Bills-Envoy/
    CLAUDE.md                the Envoy's standing orders
    backlog.md               ideas waiting for your approval
    .claude/skills/          skills only this Envoy uses
  Birthdays-Envoy/
  _inbox/                    Envoy-to-Envoy requests (envoy-inbox skill)
    Bills-Envoy/
    Birthdays-Envoy/
~/Recordings/                meeting recordings + transcripts (meeting-notes skill; never synced)
```

`~` means your home folder: `C:\Users\<you>` on Windows, `/Users/<you>` on Mac.

## Mac vs Windows

| | Windows | Mac |
|---|---|---|
| Claude Code, Envoys, envoy-inbox, subscription-audit, browser-handoff | ✅ | ✅ |
| pax-studio skills (Python 3.10+, FFmpeg via `imageio-ffmpeg`) | ✅ | ✅ |
| meeting-notes **recording** (captures speaker audio) | ✅ built in (WASAPI loopback) | Needs a free loopback driver such as BlackHole, or use your meeting app's own recording; transcription works the same |
| attention-alert pop-up | ✅ PowerShell | Use `osascript -e 'display notification "…"'` or `say` |
| Paths | `C:\Users\<you>\…`, backslashes | `/Users/<you>/…`, forward slashes |
| Shell Claude uses | PowerShell / Git Bash | zsh |

## Ground rules baked into every skill

- **You sign in. You click buy, pay, send, accept or delete.** Claude does the rest and stops at those buttons.
- **Emails are drafts.** Nothing is sent without you.
- **Keys stay local:** API keys come from environment variables or a git-ignored `.env`, never written into files.
- **Recording needs consent:** many places (e.g. Massachusetts, California) require everyone on a call to agree.
- **AI disclosure:** realistic AI people or voices on YouTube must be marked as altered or synthetic content.

## License

MIT. Use it, change it, share it. A mention of the channel is appreciated, not required.
