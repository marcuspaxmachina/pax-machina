---
name: attention-alert
description: Shows a loud, flashing, always-on-top pop-up (Windows) so the user notices when Claude needs them to act, such as signing in, approving something or clicking a final button. Use whenever Claude is blocked waiting on the user, or when the user says "alert me when you need me", "flash the screen", "get my attention".
---

# Attention alert

*"A herald with a trumpet beats a scroll left on the table." — Marcus*

Claude often works while the user is in another window. When Claude needs the human, a polite line in the chat is
easy to miss and browser sessions time out. This skill throws up an impossible-to-miss pop-up.

## When to use it

Fire an alert whenever you **stop and wait for the user**, for example:
- a website needs them to sign in, enter a 2FA code or solve a CAPTCHA;
- you've reached a final Pay / Place order / Cancel / Publish / Accept button (see `browser-handoff`);
- a long job (transcription, render, download batch) has finished and needs review;
- you need a decision before you can continue.

Don't fire it for routine progress updates. One alert per wait; if the user hasn't responded, don't spam it.

## How (Windows)

`alert.ps1` sits next to this file. Launch it **hidden and detached** so it doesn't block Claude:

```powershell
Start-Process powershell -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',"<skill folder>\alert.ps1",'-Message','"Your turn: please sign in to the bank site"'
```

Or from a plain shell:

```
powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "<skill folder>\alert.ps1" -Message "Your turn: approve the cart"
```

Parameters:
- `-Message` what the user needs to do, in a few words ("Sign in to the electric company", "Cart ready: $84.12").
- `-Title` optional headline (default `CLAUDE NEEDS YOU`; e.g. `YOUR BILLS ENVOY NEEDS YOU`).
- `-Seconds` optional auto-close time (default 120).

The window flashes colours, shakes, plays the system "exclamation" sound every few seconds, stays on top, and closes
when clicked. It uses only built-in Windows PowerShell; nothing to install.

After launching it, also write the request at the **top** of your chat reply, so the user sees what to do when
they come back.

**Tip:** add a line to an Envoy's `CLAUDE.md` such as "When I need the user to act, launch the attention-alert
pop-up," so every session does it automatically.

## macOS / Linux

macOS: `osascript -e 'display notification "Your turn: sign in" with title "Claude needs you" sound name "Glass"'; say "Claude needs you"`.
Linux: `notify-send -u critical "Claude needs you" "Your turn: sign in"`.

## What this won't do

- It only notifies. It never clicks, signs in or approves anything on the user's behalf.
- It doesn't send anything off the computer (no SMS, email or push services).
- It doesn't run in the background or on a schedule; it fires only when Claude is actively waiting.
