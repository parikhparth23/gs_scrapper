# Gujarat Samachar → RSS (self-hosted, free)

Gujarat Samachar dropped its native RSS feeds, so this scrapes the site
and rebuilds a `feed.xml` on a schedule using GitHub Actions (free for
public repos), then serves it via GitHub Pages. No rss.app subscription
needed.

## 1. First, test it locally (recommended)

```bash
pip install -r requirements.txt
python scrape_gujaratsamachar.py
```

This writes `feed.xml`. Open it and check the titles/links look right.
If `parse_articles` finds 0 articles, the site's markup has likely
changed — open the page's HTML in your browser's dev tools, find how
article links look (should still contain `/news/<category>/<slug>-<digits>`),
and adjust `ARTICLE_HREF_RE` in `scrape_gujaratsamachar.py` accordingly.

To scrape only one category instead of the homepage, run e.g.:

```bash
python scrape_gujaratsamachar.py https://www.gujaratsamachar.com/category/sports/1
```

(or edit `SOURCE_URL` at the top of the script to make it permanent).

## 2. Put this on GitHub

1. Create a new **public** GitHub repo (Pages' free tier needs public,
   unless you have GitHub Pro/Team for private Pages).
2. Push all these files (`scrape_gujaratsamachar.py`, `requirements.txt`,
   `.github/workflows/update-feed.yml`, this README) to the repo.
3. In the repo, go to **Settings → Actions → General → Workflow
   permissions** and select "Read and write permissions" (needed so the
   workflow can commit the updated `feed.xml`).
4. Go to **Settings → Pages** and set the source to "Deploy from a
   branch" → `main` → `/ (root)`.
5. Go to the **Actions** tab and manually run "Update Gujarat Samachar
   RSS feed" once (via "Run workflow") to generate the first `feed.xml`
   and confirm it works.

After that it'll auto-run every 30 minutes (edit the cron line in
`update-feed.yml` to change frequency).

## 3. Your feed URL

Once GitHub Pages is live, your feed will be at:

```
https://YOUR-USERNAME.github.io/YOUR-REPO/feed.xml
```

Update `FEED_SELF_URL` in `scrape_gujaratsamachar.py` to match, then
point your RSS reader at that URL.

## Notes

- GitHub Actions free tier gives 2,000 minutes/month for public repos —
  this job takes seconds per run, so running every 30 min is nowhere
  near the limit.
- If Gujarat Samachar changes their page markup in the future, the
  regex-based selectors may need a small tweak — the script is written
  so that's a one-line change (`ARTICLE_HREF_RE` / `find_nearby_date`).
