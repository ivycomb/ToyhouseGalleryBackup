#!/usr/bin/env python3
"""

Quick start (Windows: use `python`, not `python3`):
    pip install requests beautifulsoup4

    python toyhouse_gallery_dl.py "https://toyhou.se/12345.character-name/gallery" ^
        --out my-character ^
        --cookie "laravel_session=...; remember_web_...=..." ^
        --delay 1.5

Auth: your own galleries require being logged in. See README.md for how to copy
your session cookie out of the browser.

How it works: each gallery thumbnail is an <a class="img-thumbnail"> whose href
is the full-resolution file on f2.toyhou.se. We page through ?page=N, collect
those hrefs, and download them directly. Use --thumbs to grab the small
thumbnail versions instead of full size.
"""

from __future__ import annotations

import argparse
import os
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (toyhouse-gallery-backup; personal use)"
IMG_EXT = re.compile(r"\.(png|jpe?g|gif|webp)(\?|$)", re.I)
LAZY_ATTRS = ("src", "data-src", "data-original", "data-lazy-src", "data-lazy")


def make_session(cookie):
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"})
    if cookie:
        s.headers["Cookie"] = cookie.strip()
    return s


def normalize_gallery_url(url):
    url = url.strip().split("?")[0].rstrip("/")
    if not url.endswith("/gallery"):
        url += "/gallery"
    return url


def get_soup(session, url):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser"), r.text


def img_url(img, base_url):
    """Pull a URL from an <img>, accounting for lazy-loading attributes."""
    for attr in LAZY_ATTRS:
        val = img.get(attr)
        if val and val.strip():
            return urljoin(base_url, val.strip())
    return None


def collect_images(soup, base_url):
    """
    Return list of (full_url, thumb_url) for each gallery item.
    The gallery thumbnail anchor's href IS the full-resolution file.
    """
    out, seen = [], set()
    for a in soup.select("a.img-thumbnail[href], a.magnific-item[href]"):
        href = urljoin(base_url, a["href"])
        if "/file/" not in href and not IMG_EXT.search(href):
            continue  # skip non-image anchors (toolbar, etc.)
        if href in seen:
            continue
        seen.add(href)
        img = a.find("img")
        thumb = img_url(img, base_url) if img else None
        out.append((href, thumb))
    return out


def filename_for(url, index):
    name = os.path.basename(urlparse(url).path) or f"image_{index}"
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if not IMG_EXT.search(name):
        name += ".png"
    return f"{index:03d}_{name}"


def download(session, url, dest, delay):
    r = session.get(url, timeout=60, stream=True)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    time.sleep(delay)


def dump_debug(out_dir, page, html, soup):
    path = os.path.join(out_dir, f"debug_page{page}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    anchors = soup.select("a.img-thumbnail[href], a.magnific-item[href]")
    print(f"  [debug] saved raw HTML -> {path}")
    print(f"  [debug] {len(anchors)} gallery anchors; first few hrefs:")
    for a in anchors[:5]:
        print(f"    {a.get('href')}")


def collect_all(session, base, delay, max_pages, debug, out_dir):
    items, seen = [], set()
    page = 0
    for page in range(1, max_pages + 1):
        page_url = f"{base}?page={page}"
        print(f"[page {page}] {page_url}")
        try:
            soup, html = get_soup(session, page_url)
        except requests.HTTPError as e:
            print(f"  stopped on HTTP error: {e}")
            break

        if debug and page == 1:
            dump_debug(out_dir, page, html, soup)

        found = collect_images(soup, page_url)
        new = [(f, t) for (f, t) in found if f not in seen]
        if not new:
            if page == 1:
                print("  no gallery images found - check the cookie, or re-run "
                      "with --debug and inspect the saved HTML.")
            break
        for f, _ in new:
            seen.add(f)
        items.extend(new)
        time.sleep(delay)

    print(f"\nFound {len(items)} images across {page} page(s) checked.")
    return items


def main():
    ap = argparse.ArgumentParser(description="Download a Toyhouse character gallery.")
    ap.add_argument("gallery_url", help="e.g. https://toyhou.se/12345.character-name/gallery")
    ap.add_argument("--out", default="toyhouse_gallery")
    ap.add_argument("--cookie", default=None, help="Full Cookie header from a logged-in session")
    ap.add_argument("--delay", type=float, default=1.5, help="Seconds between requests")
    ap.add_argument("--max-pages", type=int, default=200)
    ap.add_argument("--thumbs", action="store_true",
                    help="Download the small thumbnail versions instead of full-size files")
    ap.add_argument("--debug", action="store_true", help="Dump page-1 HTML and what was parsed")
    args = ap.parse_args()

    session = make_session(args.cookie)
    base = normalize_gallery_url(args.gallery_url)
    os.makedirs(args.out, exist_ok=True)

    items = collect_all(session, base, args.delay, args.max_pages, args.debug, args.out)
    if not items:
        print("Nothing to download.")
        return

    count, failed = 0, 0
    for full, thumb in items:
        url = thumb if (args.thumbs and thumb) else full
        count += 1
        dest = os.path.join(args.out, filename_for(url, count))
        try:
            download(session, url, dest, args.delay)
            print(f"  saved {dest}")
        except Exception as e:
            failed += 1
            print(f"  FAILED {url}: {e}")

    print(f"\nDone. {count - failed} saved, {failed} failed -> {args.out}/")


if __name__ == "__main__":
    main()
