#!/usr/bin/env python3
"""
Scrapes gujaratsamachar.com and generates an RSS feed (feed.xml).

Since the site removed its native RSS feeds, this rebuilds one by
scraping article links off the homepage (or a category page) and
writing a standard RSS 2.0 XML file.

Run this on a schedule (e.g. via GitHub Actions) so feed.xml stays
fresh. Point your RSS reader at the hosted feed.xml (e.g. via GitHub
Pages or raw.githubusercontent.com).
"""

import re
import sys
import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# ---- CONFIG ---------------------------------------------------------
# Change this to a category page if you only want e.g. Sports or Business:
#   https://www.gujaratsamachar.com/category/sports/1
#   https://www.gujaratsamachar.com/category/business/1
SOURCE_URL = "https://www.gujaratsamachar.com/"
BASE_URL = "https://www.gujaratsamachar.com"
OUTPUT_FILE = "feed.xml"
MAX_ITEMS = 30
FEED_TITLE = "Gujarat Samachar (unofficial feed)"
FEED_SELF_URL = "https://YOUR-USERNAME.github.io/YOUR-REPO/feed.xml"  # update after hosting
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
# ----------------------------------------------------------------------

DATE_RE = re.compile(r"\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b")
ARTICLE_HREF_RE = re.compile(r"/news/[a-z0-9\-]+/[A-Za-z0-9\-]+-\d{5,}$")


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    return resp.text


def find_nearby_date(tag) -> str | None:
    """Look at the link's parent/siblings for a 'DD Mon YYYY' style date."""
    node = tag
    for _ in range(4):  # walk up a few levels
        if node is None:
            break
        text = node.get_text(" ", strip=True)
        m = DATE_RE.search(text)
        if m:
            return m.group(1)
        node = node.parent
    return None


def parse_articles(html: str, base_url: str):
    soup = BeautifulSoup(html, "html.parser")
    seen = {}

    for a in soup.find_all("a", href=True):
        href = a["href"]
        # normalize relative links
        full_url = urljoin(base_url, href)
        path = full_url.replace(base_url, "")

        if not ARTICLE_HREF_RE.search(path):
            continue

        title = a.get_text(strip=True)
        if not title or len(title) < 8:
            # sometimes the <a> wraps only an <img>; try the title attr
            title = a.get("title", "").strip()
        if not title or len(title) < 8:
            continue

        if full_url in seen:
            continue

        # try to find a category from the URL, e.g. /news/sports/...
        cat_match = re.search(r"/news/([a-z0-9\-]+)/", path)
        category = cat_match.group(1) if cat_match else None

        date_str = find_nearby_date(a)

        seen[full_url] = {
            "title": title,
            "link": full_url,
            "category": category,
            "date_str": date_str,
        }

    return list(seen.values())


def parse_date(date_str: str | None) -> datetime:
    if not date_str:
        return datetime.now(timezone.utc)
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def build_feed(articles):
    fg = FeedGenerator()
    fg.title(FEED_TITLE)
    fg.link(href=SOURCE_URL, rel="alternate")
    fg.link(href=FEED_SELF_URL, rel="self")
    fg.description("Unofficial auto-generated feed scraped from gujaratsamachar.com")
    fg.language("gu")

    for art in articles[:MAX_ITEMS]:
        fe = fg.add_entry()
        fe.title(art["title"])
        fe.link(href=art["link"])
        guid = hashlib.sha1(art["link"].encode("utf-8")).hexdigest()
        fe.guid(guid, permalink=False)
        if art["category"]:
            fe.category(term=art["category"])
        fe.pubDate(parse_date(art["date_str"]))

    return fg


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else SOURCE_URL
    html = fetch_html(url)
    articles = parse_articles(html, BASE_URL)

    if not articles:
        print("No articles found — the site's markup may have changed; "
              "inspect the HTML and adjust ARTICLE_HREF_RE.", file=sys.stderr)
        sys.exit(1)

    fg = build_feed(articles)
    fg.rss_file(OUTPUT_FILE, pretty=True)
    print(f"Wrote {len(articles[:MAX_ITEMS])} items to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
