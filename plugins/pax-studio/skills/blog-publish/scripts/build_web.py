"""Turn article sources (Word .docx or Markdown) into WordPress-ready HTML with cross-links and a video embed.

Usage (from the show's project root):  python build_web.py config/blog.json
Writes the config's "out" file (default build/posts.json): [{"key", "id", "type", "title", "content", "status"}]
which the wp-admin upload snippet in reference.md sends to WordPress.

Privacy assert: the build FAILS if any string from the deny list appears in a post. Keep the deny list (real
names, emails, employer/client names, home town...) in a local, git-ignored file named in "denylist_file";
never put those strings in the config or in this repo.
"""
import json, re, sys
from pathlib import Path


def to_html(src):
    src = Path(src)
    if src.suffix.lower() == ".docx":
        import mammoth                                       # pip install mammoth
        with open(src, "rb") as f:
            return mammoth.convert_to_html(f).value
    import markdown                                          # pip install markdown
    return markdown.markdown(src.read_text(encoding="utf8"), extensions=["tables", "fenced_code"])


def clean(h, strip_title_prefix=None):
    h = re.sub(r"^\s*<h1>.*?</h1>", "", h, count=1, flags=re.S)           # WordPress shows the title itself
    if strip_title_prefix:
        h = re.sub(r"^\s*<p>" + re.escape(strip_title_prefix) + r".*?</p>", "", h, count=1, flags=re.S)
    # demote headings one level (h1 -> h2, h2 -> h3) so the post title stays the only h1
    h = h.replace("<h2>", "<h3>").replace("</h2>", "</h3>").replace("<h1>", "<h2>").replace("</h1>", "</h2>")
    return h


def embed(url):
    return ('<figure class="wp-block-embed is-type-video is-provider-youtube wp-block-embed-youtube">'
            f'<div class="wp-block-embed__wrapper">{url}</div></figure>')


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf8"))
    site = cfg["site"].rstrip("/")
    ids = {p["key"]: p.get("id") for p in cfg["posts"]}
    live = {p["key"]: p.get("live", False) for p in cfg["posts"]}

    def link(text, key):
        if not live.get(key) or not ids.get(key):
            return text + cfg.get("not_live_suffix", " (coming soon)")
        return f'<a href="{site}/?p={ids[key]}">{text}</a>'      # ?p=ID redirects to the permalink, survives renames

    out = []
    for p in cfg["posts"]:
        h = clean(to_html(p["source"]), p.get("strip_title_prefix"))
        for l in p.get("links", []):
            if l["find"] not in h:
                sys.exit(f"{p['key']}: link text not found: {l['find']!r}")
            h = h.replace(l["find"], link(l.get("text", l["find"]), l["key"]), 1)
        if p.get("video"):
            marker = p.get("video_marker", "<p>[[VIDEO]]</p>")
            if marker not in h:
                sys.exit(f"{p['key']}: video marker {marker!r} not found")
            h = h.replace(marker, embed(p["video"]), 1)
        out.append({"key": p["key"], "id": p.get("id"), "type": p.get("type", "posts"), "title": p["title"],
                    "content": h, "status": p.get("status", "draft")})

    # Privacy assert: fail closed.
    deny = list(cfg.get("forbidden", ["[[", "DRAFT", "TODO"]))
    dl = cfg.get("denylist_file")
    if dl:
        if not Path(dl).exists():
            sys.exit(f"deny list {dl} missing: create it locally (one string per line) and git-ignore it")
        deny += [s.strip() for s in Path(dl).read_text(encoding="utf8").splitlines() if s.strip() and not s.startswith("#")]
    bad = [(o["key"], s) for o in out for s in deny if s.lower() in (o["title"] + o["content"]).lower()]
    if bad:
        for k, _ in bad:
            print("PRIVACY/DRAFT CHECK FAILED in", k, "(a deny-list string is present)")
        sys.exit(1)

    dest = Path(cfg.get("out", "build/posts.json"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf8")
    for o in out:
        print(f"{o['key']:<12} id={o['id']} {len(o['content'])} chars, links: {o['content'].count('<a href')}")
    print("wrote", dest)


if __name__ == "__main__":
    main()
