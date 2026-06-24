# Toyhouse Gallery Backup

A small Python script that downloads every full-resolution image from a Toyhouse
character gallery. Intended for backing up / exporting galleries you own.

> Be considerate: large galleries have caused server-load issues on Toyhouse in
> the past. The default `--delay` is intentionally polite - raise it, don't lower it.

## Requirements

- Python 3.8+
- Two packages:

```
pip install requests beautifulsoup4
```

## Usage

```
python toyhouse_gallery_dl.py "GALLERY_URL" --out FOLDER --cookie "COOKIE_STRING" --delay 1.5
```

Example (the URL is the character's gallery page):

```
python toyhouse_gallery_dl.py "https://toyhou.se/12345.character-name/gallery" --out my-character --cookie "laravel_session=...; remember_web_...=..."
```

Files are saved as `001_<id>_<hash>.png`, `002_...`, etc. The numeric prefix keeps
them in gallery order; the original name keeps each file unique.

### Options

| Option | Default | What it does |
|---|---|---|
| `--out` | `toyhouse_gallery` | Folder to save images into (created if missing) |
| `--cookie` | _(none)_ | Your logged-in session cookie (see below) |
| `--delay` | `1.5` | Seconds to wait between requests |
| `--max-pages` | `200` | Safety cap on how many gallery pages to walk |
| `--thumbs` | off | Download small thumbnails instead of full-size files |
| `--debug` | off | Save page-1 HTML + print what was parsed (for troubleshooting) |

## Getting your cookie (the important part)

Most galleries - including your own private or restricted ones - only show their
images when you're **logged in**. The script logs in by reusing a session your
browser already has, so you need to copy your cookie out of the browser.

You never type your password into the script; you're just handing it a session
that's already authenticated.

### Steps (Chrome / Edge / Brave)

1. Log into **toyhou.se** in your browser as normal.
2. Open your character's gallery page.
3. Press **F12** to open DevTools, then click the **Network** tab.
4. **Reload the page** (F5) so requests appear in the list.
5. Click the **very first request** in the list - it's the gallery page itself
   (its name will be `gallery` or the page URL, type `document`).
6. In the panel that opens, scroll to **Request Headers** and find the line that
   starts with **`cookie:`**.
7. Copy the **entire value** after `cookie:` - it's one long string with several
   `name=value` pairs separated by `; `.
8. Paste it into the command wrapped in **double quotes**, after `--cookie`.

### Steps (Firefox)

Same idea: **F12 → Network → reload → click the document request → Request
Headers → copy the `Cookie` value**. (Right-click the request → *Copy Value →
Copy Request Headers* also works; just pull out the cookie line.)

### Which cookies actually matter

You can paste the whole `cookie:` string - extra values are harmless. The ones
that authenticate you are:

- **`laravel_session`** - your active session (Toyhouse runs on Laravel).
- **`remember_web_<long hash>`** - the "remember me" token; keeps the session
  valid longer.

If you only grab `laravel_session` it'll usually work, but it can expire sooner.
Including the `remember_web_...` token is more reliable.

### Keep it private

Your cookie string is **as sensitive as your password** while it's valid -
anyone with it can act as you on Toyhouse. Don't paste it into chats, share it,
or commit it to a repo. If you think it leaked, log out of Toyhouse (or change
your password) to invalidate the session.

## Troubleshooting

**"no gallery images found" / nothing downloads**
- Your cookie is probably missing or expired. Re-grab it (steps above).
- Re-run with `--debug`. It saves `debug_page1.html` into your output folder.
  Open it - if you can see your owner toolbar (Upload / Manage / Sort) and the
  thumbnails, auth is working and the issue is elsewhere; if it looks logged-out,
  the cookie didn't take.

**Some files fail with 403 partway through**
- The session likely expired mid-run. Grab a fresh cookie and run again.

**`python` is not recognized (Windows)**
- Try `py` instead of `python`, or install Python from python.org and check
  "Add Python to PATH" during setup.

**Cookie has spaces and breaks the command**
- Make sure the whole cookie string is inside double quotes: `--cookie "..."`.

## Note on what you download

This grabs the image files as Toyhouse serves them. If you've enabled
watermarking on your account, the stored files may include the watermark. The
script doesn't add or remove anything - it downloads the original uploads as-is.
This generally shouldn't happen, though, and images should be watermark-free if you
are the character owner.
