# Hedra animation: code snippets

These are patterns for the Playwright MCP tools. Selectors and endpoint paths change; inspect the page first
(`browser_snapshot`, `browser_network_requests`) and adapt. Use project-relative or absolute paths that exist on
the user's machine; never hard-code a username.

## 1. Upload with a retry loop (`browser_run_code_unsafe`)

```js
async (page) => {
  const files = ['brand/host-final.jpg'];          // or the clip's mp3
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const chooser = page.waitForEvent('filechooser', { timeout: 5000 });
      await page.getByRole('button', { name: /upload|add image|add audio/i }).first().click();
      await (await chooser).setFiles(files);
    } catch {
      // No chooser appeared (modal swallowed the click): set the files on the hidden input directly.
      const input = page.locator('input[type=file]').first();
      await input.setInputFiles(files);
    }
    // Confirm the upload landed (a thumbnail, waveform or file name shows up).
    try {
      await page.getByText(/\.(jpg|png|mp3|wav)$/i).first().waitFor({ timeout: 8000 });
      return `uploaded on attempt ${attempt}`;
    } catch { await page.keyboard.press('Escape'); }
  }
  throw new Error('upload failed 3 times');
}
```

## 2. Find the asset-list request (no secrets leave the page)

1. `browser_navigate` to the library/assets page, then reload it.
2. `browser_network_requests` and look for a JSON GET to the app's API host that returns the generations/assets
   (names like `.../assets`, `.../generations`, `.../projects/<id>/...`).
3. Use `browser_network_request` on it only to read the URL shape and response fields (video URL, title, created
   time, duration). Do **not** copy the Authorization header into chat or files.

## 3. Bulk download inside the page (`browser_run_code_unsafe`)

Capture the header from the page's own next request instead of reading it out:

```js
async (page) => {
  const LIST_URL_PART = '/assets';                 // adapt to the request you found
  const req = page.waitForRequest(r => r.url().includes(LIST_URL_PART) && r.headers()['authorization']);
  await page.reload();
  const r = await req;
  const listUrl = r.url();
  const auth = r.headers()['authorization'];       // stays in this function; never returned or logged
  const items = await page.evaluate(async ({ listUrl, auth }) => {
    const res = await fetch(listUrl, { headers: { authorization: auth } });
    const data = await res.json();
    const arr = data.data || data.items || data;   // adapt to the response shape
    // Keep the (often short-lived, signed) video URLs inside the page for the download step.
    window.__assetUrls = Object.fromEntries(arr.map(a => [a.id, a.url || a.video_url]));
    return arr.map(a => ({ id: a.id, name: a.name || a.title, created: a.created_at, url: a.url || a.video_url }))
              .filter(a => a.url);
  }, { listUrl, auth });
  return items.map(({ id, name, created }) => ({ id, name, created }));   // URLs and auth not returned
}
```

Then download each one, named by clip id from your `hedra-log.md` mapping, one at a time:

```js
async (page) => {
  const mapping = { 'GENERATION_ID': '01-S1' };    // fill from the listing + hedra-log.md
  for (const [genId, clipId] of Object.entries(mapping)) {
    const dl = page.waitForEvent('download');
    await page.evaluate(async ({ genId, clipId }) => {
      const url = window.__assetUrls?.[genId];     // set by the listing step; re-run it if the URLs expired
      const blob = await (await fetch(url)).blob();
      const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: `${clipId}.mp4` });
      document.body.appendChild(a); a.click(); a.remove();
    }, { genId, clipId });
    const d = await dl;
    await d.saveAs(`video/ep01/${clipId}.mp4`);   // project-relative target
  }
  return 'done';
}
```

## 4. Verify downloads against the audio

```python
import imageio_ffmpeg, re, subprocess
from pathlib import Path
ff = imageio_ffmpeg.get_ffmpeg_exe()
def dur(f):
    e = subprocess.run([ff, "-i", str(f)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", e).groups(); return int(h)*3600 + int(m)*60 + float(s)
for v in sorted(Path("video/ep01").glob("[0-9][0-9]-*.mp4")):
    a = Path("audio/ep01") / f"{v.stem}.mp3"
    if a.exists() and abs(dur(v) - dur(a)) > 0.5:
        print("MISMATCH", v.name, round(dur(v), 2), round(dur(a), 2))
```

## 5. Credit estimate

```python
total = sum(dur(a) for a in Path("audio/ep01").glob("[0-9][0-9]-*.mp3") if "-take" not in a.stem)
print(f"{total:.0f} s of talking -> ~{total * 7 * 1.3:.0f} credits incl. 30% retries (7 credits/s at time of writing)")
```
