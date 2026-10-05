---
name: envoy-starter
description: Sets up a new Envoy, a Claude Code project dedicated to one part of your life (bills, birthdays, a hobby, a side business), with standing orders, a backlog and notes. Use when the user says "make me an Envoy", "start a new Envoy", "set up a project for my bills/birthdays/...", or "create a CLAUDE.md for this part of my life".
---

# Envoy starter

*"Every province needs a governor with written orders." — Marcus*

An **Envoy** is simply a folder on the user's own computer that Claude Code opens: standing orders in `CLAUDE.md`,
reusable recipes in `.claude/skills/`, and working notes that act as its memory. Claude Code calls it a project;
Pax Machina calls it an Envoy. This skill builds one in about ten minutes.

## Step 1: Interview the user (short, friendly, one message)

Ask these together, offer sensible defaults, and accept "skip" for any of them:

1. **Name and province.** What part of life will this Envoy handle? (e.g. "Bills Envoy: household bills and
   subscriptions".) Suggest a folder name like `Bills-Envoy`.
2. **Where should the folder live?** Default: an `Envoys` folder in the user's home or Documents folder. Avoid
   folders synced to an employer's cloud if the Envoy is personal.
3. **Who are you, and how should I address you?** First name or nickname is plenty.
4. **What does it handle, and what is out of scope?** Three to five bullets each.
5. **Accounts and tools it may use.** e.g. a calendar connector, a browser tool, exported CSVs. Note *how* (file
   export, connector, browser with the user signing in). Never collect passwords.
6. **Privacy walls.** Anything this Envoy must never see or share (health, family, money, work data)? Should it be
   kept out of git/GitHub? (Default for personal Envoys: yes, no git remote.)
7. **Other Envoys.** Does the user already have Envoys it should talk to? (If so, offer the `envoy-inbox` skill.)

Do not over-interview. If the user gives a one-line answer ("bills, keep it simple"), fill in reasonable defaults and
show them in the draft for approval.

## Step 2: Draft and confirm

Fill `templates/CLAUDE.md` (next to this file) with the answers. Replace every `{{PLACEHOLDER}}`; delete sections
that don't apply rather than leaving them empty. Show the draft to the user and ask: "Anything to change before I
create the folder?" Keep the safety rules unless the user explicitly removes them, and if they do, say once why they
exist.

## Step 3: Create the folder

Create this layout (adjust names to the province):

```
<Name>-Envoy/
  CLAUDE.md            standing orders (from the template)
  backlog.md           ideas and tasks waiting for approval
  notes.md             running notes, decisions, what it has learned
  data/                exports, downloads, working files
  .claude/skills/      recipes this Envoy learns (empty to start)
```

`backlog.md` starter content:

```markdown
# Backlog: <Name> Envoy
Nothing here is executed until <user> approves it. Status: idea / approved / doing / done / dropped.

| # | Item | Why | Status | Added |
|---|------|-----|--------|-------|
| 1 | First job: <suggest one, e.g. "subscription audit"> | Quick win | idea | <today> |
```

`notes.md` starter content: a title, today's date, and "Created with the Pax Machina envoy-starter skill."

If the user wants a VS Code accent color so they can tell Envoys apart, offer to add
`.vscode/settings.json` with `workbench.colorCustomizations` (title bar and status bar). Optional.

## Step 4: Hand over

Tell the user, in three lines:
- Open Claude Code **in the new folder** (VS Code: File > Open Folder; terminal: `cd` there and run `claude`).
- Give it its first job from the backlog, then approve it.
- When it does something well, say **"Turn that into a skill."** That is how an Envoy gets better every week.

## Tips for good standing orders

- Short beats long. Rules the user wrote in their own words get followed best.
- Put **rules about money, passwords and sending** near the top.
- Keep a **Files** table current so a future session knows where everything is.
- One province per Envoy. If the scope keeps growing, suggest a second Envoy instead.

## What this won't do

- It won't connect accounts, sign in anywhere, or store passwords, card numbers or account numbers.
- It won't create a git repository or push anything online unless the user asks, and it warns before putting a
  personal Envoy in a public or employer-owned location.
- It won't overwrite an existing `CLAUDE.md`; if one exists, it shows a merged draft and asks first.
- It won't make the Envoy run in the background. Envoys work when the user opens them.
