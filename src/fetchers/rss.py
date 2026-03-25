"""Fetcher RSS via feedparser — arXiv CS.AI et The Gradient."""

import calendar
import logging
from datetime import datetime, timedelta, timezone

import feedparser

from src.models import Article

logger = logging.getLogger(__name__)

_FEEDS: list[dict[str, str]] = [
    {
        "name": "arXiv CS.AI",
        "url": "https://rss.arxiv.org/rss/cs.AI",
    },
    {
        "name": "The Gradient",
        "url": "https://thegradientpub.substack.com/feed",
    },
]
_LOOKBACK_HOURS = 24


def _parse_date(entry: feedparser.FeedParserDict) -> datetime:
    """Extrait et convertit la date d'une entrée RSS en datetime UTC."""
    # feedparser expose published_parsed ou updated_parsed (struct_time UTC)
    # calendar.timegm() traite le struct_time comme UTC (contrairement à time.mktime() qui utilise l'heure locale)
    struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if struct:
        return datetime.fromtimestamp(calendar.timegm(struct), tz=timezone.utc)
    return datetime.now(tz=timezone.utc)


def fetch() -> list[Article]:
    """Retourne les articles RSS des dernières 24 heures.

    Raises:
        RuntimeError: Si aucun feed n'a pu être parsé.
    """
    logger.info("RSS : récupération des flux (%d feeds)...", len(_FEEDS))

    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=_LOOKBACK_HOURS)
    articles: list[Article] = []
    successful_feeds = 0

    for feed_cfg in _FEEDS:
        feed_name = feed_cfg["name"]
        feed_url = feed_cfg["url"]
        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo and not feed.entries:
                logger.warning("RSS : feed '%s' mal formé ou inaccessible.", feed_name)
                continue

            successful_feeds += 1
            count_before = len(articles)

            for entry in feed.entries:
                entry_date = _parse_date(entry)
                if entry_date < cutoff:
                    continue

                title = (entry.get("title") or "").strip()
                link = entry.get("link") or entry.get("id") or ""
                # Préférer le summary/description, sinon le contenu
                summary_raw = (
                    entry.get("summary")
                    or entry.get("description")
                    or ""
                ).strip()
                summary = summary_raw[:800] if summary_raw else ""

                if not title or not link:
                    continue

                articles.append(
                    Article(
                        title=title,
                        url=link,
                        summary=summary,
                        source="rss",
                        date=entry_date,
                    )
                )

            logger.info(
                "RSS : '%s' → %d articles récupérés.",
                feed_name,
                len(articles) - count_before,
            )

        except Exception as exc:  # noqa: BLE001
            logger.warning("RSS : erreur sur '%s' (%s)", feed_name, exc)
            continue

    if successful_feeds == 0:
        raise RuntimeError("RSS : aucun feed n'a pu être récupéré.")

    logger.info("RSS : %d articles au total.", len(articles))
    return articles
