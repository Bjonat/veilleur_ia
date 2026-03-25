"""Orchestrateur principal — collecte, résumé et génération du digest quotidien."""

import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# load_dotenv() DOIT être appelé avant tout import src.* car summarizer.py
# instancie le LLM au niveau module (qui lit GEMINI_API_KEY immédiatement).
load_dotenv()

from src.fetchers import huggingface, rss
from src.formatter import format_digest
from src.models import Article
from src.summarizer import summarize_global, summarize_source

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_DIGESTS_DIR = Path(__file__).parent.parent / "digests"

_FETCHER_CONFIG: list[dict] = [
    {"key": "huggingface", "label": "HuggingFace Daily Papers", "fn": huggingface.fetch},
    {"key": "rss",         "label": "Flux RSS",                 "fn": rss.fetch},
]


def _run_fetchers() -> dict[str, list[Article]]:
    """Lance les fetchers en parallèle. Les erreurs sont isolées par source."""
    results: dict[str, list[Article]] = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_cfg = {
            executor.submit(cfg["fn"]): cfg for cfg in _FETCHER_CONFIG
        }
        for future in as_completed(future_to_cfg):
            cfg = future_to_cfg[future]
            key, label = cfg["key"], cfg["label"]
            try:
                articles = future.result()
                results[key] = articles
                logger.info("✓ %s : %d articles récupérés.", label, len(articles))
            except Exception as exc:  # noqa: BLE001
                logger.warning("✗ %s : source ignorée (%s).", label, exc)
                results[key] = []

    return results


def _build_summaries(
    articles_by_source: dict[str, list[Article]],
) -> dict[str, str]:
    """Appelle summarize_source() pour chaque source ayant des articles."""
    summaries: dict[str, str] = {}

    label_map = {cfg["key"]: cfg["label"] for cfg in _FETCHER_CONFIG}

    for key, articles in articles_by_source.items():
        label = label_map.get(key, key)
        try:
            summaries[key] = summarize_source(articles, label)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Summarizer '%s' échoué : %s", label, exc)
            summaries[key] = f"*Résumé indisponible pour {label} ({exc}).*"

    return summaries


def main() -> None:
    today = datetime.now(tz=timezone.utc)
    date_str = today.strftime("%Y-%m-%d")
    output_path = _DIGESTS_DIR / f"{date_str}.md"

    logger.info("=== Démarrage du digest %s ===", date_str)

    # 1. Collecte en parallèle
    articles_by_source = _run_fetchers()

    total_articles = sum(len(a) for a in articles_by_source.values())
    if total_articles == 0:
        logger.error("Aucun article récupéré depuis aucune source. Abandon.")
        sys.exit(1)

    # 2. Résumé par source
    summaries = _build_summaries(articles_by_source)

    # 3. TL;DR global
    try:
        tldr = summarize_global(summaries)
    except Exception as exc:  # noqa: BLE001
        logger.warning("TL;DR global échoué : %s", exc)
        tldr = "- *TL;DR indisponible.*"

    # 4. Formatage Markdown
    digest_content = format_digest(date=today, tldr=tldr, summaries=summaries)

    # 5. Écriture du fichier
    _DIGESTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(digest_content, encoding="utf-8")
    logger.info("=== Digest écrit : %s ===", output_path)


if __name__ == "__main__":
    main()
