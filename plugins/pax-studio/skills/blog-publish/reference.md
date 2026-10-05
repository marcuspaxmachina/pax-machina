# Blog publish: wp-admin snippets

Run these with the Playwright `browser_evaluate` tool on a wp-admin block-editor page (e.g.
`<site>/wp-admin/post-new.php` or `post.php?post=<id>&action=edit`), where `wp.apiFetch` and `wp.blocks` exist.
Paste the JSON from `build/posts.json` in place of `POSTS` (read the file and inline it; it is public content
that passed the privacy assert).

## Create or update posts (as blocks)

```js
async () => {
  const POSTS = /* contents of build/posts.json */ [];
  const results = [];
  for (const p of POSTS) {
    // HTML -> real Gutenberg blocks (paragraphs, headings, lists, tables, embeds), then block markup.
    const blocks = wp.blocks.rawHandler({ HTML: p.content });
    const content = wp.blocks.serialize(blocks);
    const type = p.type || 'posts';                        // 'posts' or 'pages'
    const data = { title: p.title, content };
    if (p.status) data.status = p.status;                  // keep 'draft' unless the human approved publishing
    const path = p.id ? `/wp/v2/${type}/${p.id}` : `/wp/v2/${type}`;
    const r = await wp.apiFetch({ path, method: 'POST', data });
    results.push({ key: p.key, id: r.id, status: r.status, link: r.link });
  }
  return results;                                          // record new ids in config/blog.json
}
```

Notes:
- Updating by ID keeps the URL (republish). Changing `status` from `publish` to `draft` unpublishes: avoid.
- If the embed block does not render, make sure the YouTube URL sits alone inside the
  `wp-block-embed__wrapper` div (build_web.py does this) and that the site allows embeds.
- `rawHandler` turns unknown HTML into Classic/HTML blocks; check the editor for any "Classic" blocks and fix the
  source formatting if needed.

## Read current posts (to find IDs)

```js
async () => (await wp.apiFetch({ path: '/wp/v2/posts?per_page=50&status=publish,draft&_fields=id,title,status,link' }))
  .map(p => ({ id: p.id, title: p.title.rendered, status: p.status, link: p.link }))
```

## Brand colors via global styles (block themes)

```js
async () => {
  const theme = (await wp.apiFetch({ path: '/wp/v2/themes?status=active' }))[0];
  const gsId = theme?._links?.['wp:user-global-styles']?.[0]?.href.split('/').pop();
  const gs = await wp.apiFetch({ path: `/wp/v2/global-styles/${gsId}?context=edit` });
  const settings = gs.settings || {};
  settings.color = settings.color || {};
  settings.color.palette = { custom: [
    { slug: 'brand-primary', name: 'Brand primary', color: '#77372E' },
    { slug: 'brand-accent',  name: 'Brand accent',  color: '#7F417D' },
    { slug: 'brand-light',   name: 'Brand light',   color: '#E9E7E7' },
    { slug: 'brand-text',    name: 'Brand text',    color: '#2B2421' },
  ]};
  const styles = gs.styles || {};
  styles.elements = { ...(styles.elements || {}), link: { color: { text: 'var(--wp--preset--color--brand-accent)' } } };
  return wp.apiFetch({ path: `/wp/v2/global-styles/${gsId}`, method: 'POST', data: { settings, styles } });
}
```
On WordPress.com, custom styles may require a paid plan; if the editor shows an upgrade prompt, stop and tell
the human (the upgrade is their click). The Site Editor UI (Styles -> Colors) is the safe fallback.

## Word article builder pattern

```python
from docx import Document
from docx.shared import Pt
import brand_docx                                   # from this skill's scripts/
colors = brand_docx.load("config/blog.json")
doc = Document(); brand_docx.apply(doc, colors)
doc.styles["Normal"].font.size = Pt(11)
doc.add_heading("Article title", 0)
doc.add_paragraph("Hook paragraph in the host's voice.")
doc.add_paragraph("[[VIDEO]]")                      # replaced by the YouTube embed at build time
doc.add_heading("Try this today", 1)
t = doc.add_table(rows=2, cols=2); t.cell(0, 0).text = "Plan"; t.cell(0, 1).text = "Cost (at time of writing)"
brand_docx.style_table(t, colors)
doc.save("blog/final/ep01.docx")
```

## Article checklist
- [ ] Exact prompts in code blocks; costs dated "at time of writing".
- [ ] The video embed near the top; a link to the About page and the free toolkit.
- [ ] AI disclosure line (characters are AI-animated; voices synthetic) and "not affiliated with" disclaimers.
- [ ] Cross-links by post ID; "coming soon" only for posts that are not live.
- [ ] Privacy assert passed; images stripped of EXIF; screenshots blurred.
- [ ] After publishing: `youtube-update` sync checklist.
