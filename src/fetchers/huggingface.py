"""Fetcher pour HuggingFace Daily Papers via l'API JSON non-officielle."""

import logging
from datetime import datetime, timezone

import requests

from src.models import Article

logger = logging.getLogger(__name__)

_API_URL = "https://huggingface.co/api/daily_papers"
_BASE_URL = "https://huggingface.co/papers"
_TIMEOUT = 15  # secondes


def fetch() -> list[Article]:
    """Retourne les papers HuggingFace du jour.

    Raises:
        RuntimeError: Si l'API est inaccessible ou retourne une réponse invalide.
    """
    logger.info("HuggingFace : récupération des daily papers...")

    try:
        response = requests.get(_API_URL, timeout=_TIMEOUT, headers={"Accept": "application/json"})
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"HuggingFace API inaccessible : {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(f"HuggingFace : réponse JSON invalide : {exc}") from exc

    articles: list[Article] = []
    for item in data:
        try:
            paper = item.get("paper", {})
            paper_id = paper.get("id") or item.get("id", "")
            title = paper.get("title", "").strip()
            abstract = (paper.get("summary") or paper.get("abstract") or "").strip()

            if not title or not paper_id:
                continue

            # La date publiée est au format ISO 8601 (ex: "2026-03-25T00:00:00.000Z")
            published_at_raw = paper.get("publishedAt") or item.get("publishedAt", "")
            try:
                date = datetime.fromisoformat(published_at_raw.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                date = datetime.now(tz=timezone.utc)

            articles.append(
                Article(
                    title=title,
                    url=f"{_BASE_URL}/{paper_id}",
                    summary=abstract,
                    source="huggingface",
                    date=date,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("HuggingFace : item ignoré (%s)", exc)
            continue

    logger.info("HuggingFace : %d papers récupérés.", len(articles))
    return articles
