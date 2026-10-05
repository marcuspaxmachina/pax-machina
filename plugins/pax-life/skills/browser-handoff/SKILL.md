---
name: browser-handoff
description: The human-in-the-loop browser pattern for Claude Code with a browser tool (e.g. the Playwright MCP) - Claude opens the page, the human signs in, Claude does the clicking, filling and downloading, and Claude stops before anything binding (payments, checkout, legal terms, sending, deleting). Use whenever a task needs a website the user must sign in to, or the user says "you drive, I'll log in", "take over the browser", "fill this in for me", "get me to the checkout".
---

# Browser hand-off

*"I sign the decrees. Claudia carries them to the provinces." — Marcus*

Requires a browser tool. The Playwright MCP works well; ask Claude Code to "set up the Playwright MCP server" if it
isn't installed. Tool names below are Playwright MCP's; other browser tools have equivalents.

## The pattern

1. **Claude opens the page** (`browser_navigate`) and says what it is about to do.
2. **The human signs in.** Passwords, 2FA codes, CAPTCHAs, "is this you?" prompts and passkeys are **always the
   human's**. Say: "Please sign in, then tell me you're in." Alert loudly (see `attention-alert`) and wait.
3. **Claude takes over**: navigation, searching, form filling, downloads, uploads, comparing options.
4. **Claude stops before anything binding** and hands back, saying exactly what the final button says and what it
   will do. Binding means: paying, placing an order, checkout, subscribing, cancelling, accepting terms or
   consents (including biometric/voice consent), publishing, sending a message or email, deleting data or accounts.
5. **The human clicks** the binding button. Claude records the outcome (confirmation number, date) in the Envoy's notes.

## Practical tips (learned the hard way)

- **Sessions time out fast.** Have everything ready before asking the user to sign in, then work promptly.
- **File-chooser dialogs block.** Don't click "Upload" and wait for a dialog. Set the file on the
  `<input type="file">` directly (`setInputFiles`, or `browser_file_upload` right after the chooser opens).
- **Stage uploads inside the browser tool's allowed folder.** Many setups only allow files under the project folder:
  copy files into a temporary folder there, upload, then delete the copies.
- **Downloads with the same name overwrite each other.** Rename each file as soon as it lands.
- **When a site's own buttons misbehave**, you may call the site's API from inside the page with the user's
  logged-in session: watch the page's own requests (`browser_network_requests`), copy the headers it uses, and
  `fetch` the same endpoint from `browser_evaluate`. Only for reading, or for exactly the actions the user asked for;
  never to get around a limit, a paywall, or a confirmation step.
- **Huge pages:** take snapshots sparingly. Save one snapshot to a file and search that file instead of re-snapping.
- **Privacy before uploading screenshots anywhere:** blur or crop file names, email addresses, account numbers,
  faces of other people and anything else private.
- **Verify before handing back.** Re-read the cart or form against what the user actually asked for (quantities,
  sizes, dates, names, addresses, totals). Point out anything you substituted or couldn't find.
- **Don't fight anti-bot checks.** If a site blocks automation, hand the step to the user.

## Example walkthroughs

**AI creative tools (image, voice, animation sites)**
Open the tool; user signs in. Claude uploads the prepared images or audio (staged in the allowed folder), pastes the
prompt and settings, starts the generation, waits, downloads results and renames them. **Stops** at: buying credits,
upgrading plans, and any consent screen for cloning a face or voice. Test one short item before a big batch, and
tell the user the credit cost before starting it.

**Grocery order**
User signs in. Claude works through the shopping list: searches each item, picks the closest match (preferring the
user's past purchases), sets quantities, and lists substitutions and anything not found. Then it re-checks the cart
line by line against the list and the budget. **Stops** at the checkout / delivery-slot / place-order screen with a
summary: item count, total, delivery window.

**Paying a bill**
User signs in to the biller. Claude finds the current statement, downloads the PDF to the Envoy's `data/` folder,
notes amount and due date, and fills the payment form with the amount the user specified. **Stops** before the
**Pay** / **Submit payment** button and reads back amount, account (last 4 digits only) and date.

**WordPress or YouTube Studio session**
User signs in. Claude uploads media via the file input, fills title, description, tags, chapters, thumbnails and
categories from the approved draft, and saves as **draft / private / unlisted**. **Stops** before Publish, Schedule
or making anything public, and lists what is set so the user can review the preview.

## What this won't do

- It never types, stores or asks for passwords, 2FA codes, card numbers or security answers, and never solves CAPTCHAs.
- It never clicks a binding button: pay, buy, place order, subscribe, cancel, accept terms or consents, publish,
  send, or delete.
- It doesn't use the logged-in session for anything beyond what the user asked for.
- It doesn't upload screenshots or files containing private details without blurring them and asking first.
