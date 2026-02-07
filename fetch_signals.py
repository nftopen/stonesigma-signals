import feedparser
import json
from datetime import datetime, timezone

SOURCES = {
    "FCA (UK)": "https://www.fca.org.uk/news/rss.xml",
    "PRA / BoE (UK)": "https://www.bankofengland.co.uk/rss/news",
    "SEC (US)": "https://www.sec.gov/rss/press-release.xml",
    "EBA (EU)": "https://www.eba.europa.eu/rss.xml",
    "ESMA (EU)": "https://www.esma.europa.eu/rss.xml",
    "BCBS (BIS)": "https://www.bis.org/rss/bcbs.xml",
    "FSB": "https://www.fsb.org/feed/",
    "IOSCO": "https://www.iosco.org/news/rss.xml",
}

INCLUDE = [
    "consultation",
    "guidance",
    "supervis",
    "implementation",
    "enforcement",
    "policy",
    "statement",
    "final report",
    "discussion paper",
    "cp",
]

EXCLUDE = [
    "speech",
    "conference",
    "webinar",
    "podcast",
    "event",
    "award",
]

def parse_dt(entry) -> str:
    # Try common RSS date fields; fall back to empty.
    for key in ("published", "updated"):
        if key in entry and entry.get(key):
            return entry.get(key)
    return ""

def dt_sort_key(dt_str: str) -> int:
    # Convert to a sortable integer timestamp (best-effort).
    try:
        # feedparser may provide parsed struct_time
        return int(datetime(*entry_published_parsed[:6], tzinfo=timezone.utc).timestamp())
    except Exception:
        return 0

items = []

for source, url in SOURCES.items():
    feed = feedparser.parse(url)
    for entry in feed.entries[:25]:
        title = (entry.get("title") or "").strip()
        t = title.lower()

        if not title:
            continue

        if any(k in t for k in EXCLUDE):
            continue

        if not any(k in t for k in INCLUDE):
            continue

        link = entry.get("link") or ""
        date_str = parse_dt(entry)

        # Prefer parsed dates when available
        ts = 0
        if entry.get("published_parsed"):
            try:
                ts = int(datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).timestamp())
            except Exception:
                ts = 0
        elif entry.get("updated_parsed"):
            try:
                ts = int(datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).timestamp())
            except Exception:
                ts = 0

        items.append({
            "source": source,
            "title": title,
            "date": date_str,
            "url": link,
            "ts": ts,
        })

# Sort newest first, drop duplicates by URL/title
items.sort(key=lambda x: x.get("ts", 0), reverse=True)

seen = set()
deduped = []
for it in items:
    key = (it["url"] or it["title"]).strip().lower()
    if key in seen:
        continue
    seen.add(key)
    deduped.append(it)
    if len(deduped) >= 7:
        break

# Remove internal field
for it in deduped:
    it.pop("ts", None)

with open("signals.json", "w", encoding="utf-8") as f:
    json.dump(deduped, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(deduped)} items to signals.json")
