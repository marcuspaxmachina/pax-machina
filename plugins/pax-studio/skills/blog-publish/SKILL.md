---
name: blog-publish
description: Publishes a show's companion articles from Word (.docx) or Markdown to a WordPress.com/WordPress site - converts with mammoth, adds cross-links by post ID and the YouTube embed, fails the build if any real-identity string appears, then creates or updates posts from inside wp-admin with wp.apiFetch and block conversion (rawHandler + serialize), keeping URLs on republish; also brand colors in the theme's global styles. Use when the user says "publish the guide", "post the article", "update the blog post", "republish", "embed the video in the post", "link the posts together", or "set the blog colors".
---

# Blog publish (WordPress)

Each episode gets a how-to article with the exact prompts, embedding the video; every video description links
back (`youtube-update`). Scripts next to this file: `scripts/build_web.py` (sources -> HTML JSON),
`scripts/brand_docx.py` (brand styling for Word drafts). Upload snippets: `reference.md`.
Needs Python 3.10+ and `pip install mammoth markdown python-docx`.

## Step 1: write the article (gate)
- Draft in Word (python-docx builder using `brand_docx.py`, so the human reviews a branded .docx) or Markdown.
- Structure: hook in the host's voice -> `[[VIDEO]]` marker paragraph -> what the tool is -> exact prompts in
  code blocks -> costs (with "at time of writing") -> what can go wrong -> "try this today" -> links.
- Internal notes never go in the source file (keep them in a separate notes file).
- **Gate:** the human approves the final text. Save it as `blog/final/<key>.docx|.md`.

## Step 2: configure
Copy `blog.example.json` to `config/blog.json`:
- `site`, brand colors, each post's `key`, `source`, `title`, `id` (WordPress post ID once it exists), `live`,
  `status`, `video`, and `links` (text to find -> key of the post to link to).
- Cross-links use `<site>/?p=<ID>`: WordPress redirects to the permalink, so links survive slug or date changes.
  Links to posts that are not `live` are written as plain text plus "(coming soon)"; flip `live` and rebuild later.
- **Deny list:** create `config/privacy-denylist.txt` (one string per line: the creator's real name, family
  names, emails, employer, clients, town...). Add it to `.gitignore`. Never put those strings in the config.

## Step 3: build (privacy assert)
`python scripts/build_web.py config/blog.json`
- mammoth converts .docx to clean HTML (headings, lists, tables, links); Markdown goes through `markdown`.
- The leading H1 is removed (WordPress shows the title) and headings are demoted one level.
- The `[[VIDEO]]` paragraph becomes a YouTube embed block.
- **The build fails** if any deny-list string, `[[`, `DRAFT` or `TODO` appears. It reports which post, not
  the string. Fix the source, never the check.

## Step 4: upload from inside wp-admin (human signs in)
1. Open `<site>/wp-admin` (on WordPress.com, the site's wp-admin) with the Playwright browser; the human signs in
   (`browser-handoff`, pax-life plugin). Then open any post in the block editor so `wp.apiFetch`, `wp.blocks`
   and the REST nonce are loaded.
2. Run the upload snippet from `reference.md` with `browser_evaluate`, passing the contents of
   `build/posts.json`. It converts HTML to real blocks (`wp.blocks.rawHandler`, then `wp.blocks.serialize`) and
   calls `POST /wp/v2/posts/<id>` (or `/wp/v2/pages/<id>`) for existing posts, `POST /wp/v2/posts` for new ones.
3. New posts: record the returned `id` in `config/blog.json` and rebuild so cross-links resolve.
4. **Status:** create and update as `draft` unless the human approved publishing. Publishing (`status:
   "publish"`) or launching the site is the human's decision; you may run it only after they say so.
5. **Republish = update in place.** Updating an existing ID keeps its URL, comments and stats; never delete and
   re-create a published post.

## Step 5: verify
- Open each post's preview/live URL: video plays, headings and code blocks look right, every cross-link opens the
  right post, no "(coming soon)" left for live posts.
- View the page source or editor for stray `[[`, internal notes, or real names.
- Then run the `youtube-update` sync checklist (description links, pinned comment, channel links).

## Brand colors (theme global styles)
In the block-theme Site Editor: Appearance -> Editor -> Styles -> Colors -> Palette: add the brand colors
(primary, accent, light, text); set Background/Text/Links/Buttons/Headings. This is the human's click if the plan
or theme needs an upgrade. Alternative via REST (block themes): see `reference.md` (global-styles endpoint).
Keep colors consistent with the Word drafts (`brand` in `config/blog.json`).

## What this won't do / safety
- It does not buy plans, domains or themes, launch the site, or accept terms; the human does.
- It does not publish without the human's approval; drafts by default.
- It never prints or commits the deny list; it never echoes the matched private string.
- It only uses the logged-in session inside wp-admin (nonce handled by `wp.apiFetch`); no application passwords
  or tokens are saved to files.
- Use a separate WordPress account for an anonymous show; never the creator's professional site or analytics.
