"""Summarizer IA — résumé des articles par source et TL;DR global via Gemini 2.5 Flash."""

import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.models import Article

logger = logging.getLogger(__name__)

_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

_SOURCE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            (
                "Tu es un assistant de veille technologique francophone spécialisé en IA.\n"
                "Voici une liste d'articles/posts issus de {source_name}.\n"
                "Rédige un résumé thématique en français, structuré en courtes sections,\n"
                "qui capture les tendances importantes et les annonces notables.\n"
                "Sois concis, précis et évite le jargon superflu.\n\n"
                "Articles :\n{articles_text}"
            ),
        )
    ]
)

_GLOBAL_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            (
                "Tu es un assistant de veille IA. Voici les résumés de plusieurs sources du jour.\n"
                "Rédige un TL;DR en français sous forme de 3 à 5 bullet points.\n"
                "Chaque bullet doit capturer une tendance ou annonce majeure à retenir absolument.\n\n"
                "Résumés :\n{summaries_text}"
            ),
        )
    ]
)

_source_chain = _SOURCE_PROMPT | _llm
_global_chain = _GLOBAL_PROMPT | _llm


def _format_articles(articles: list[Article]) -> str:
    """Sérialise une liste d'Article en texte structuré pour le prompt."""
    lines: list[str] = []
    for i, article in enumerate(articles, start=1):
        lines.append(f"[{i}] {article.title}")
        lines.append(f"    URL : {article.url}")
        if article.summary:
            lines.append(f"    Résumé : {article.summary[:600]}")
        lines.append("")
    return "\n".join(lines)


def summarize_source(articles: list[Article], source_name: str) -> str:
    """Génère un résumé thématique en français pour un bloc de source donné.

    Args:
        articles: Liste d'articles issus d'une même source.
        source_name: Nom lisible de la source (ex: "HuggingFace Daily Papers").

    Returns:
        Résumé Markdown en français.

    Raises:
        RuntimeError: En cas d'erreur d'appel à l'API Gemini.
    """
    if not articles:
        return f"*Aucun article disponible pour {source_name} aujourd'hui.*"

    articles_text = _format_articles(articles)
    logger.info("Summarizer : résumé de '%s' (%d articles)...", source_name, len(articles))

    try:
        response = _source_chain.invoke(
            {"source_name": source_name, "articles_text": articles_text}
        )
        return response.content.strip()
    except Exception as exc:
        raise RuntimeError(f"Summarizer : erreur sur '{source_name}' : {exc}") from exc


def summarize_global(summaries: dict[str, str]) -> str:
    """Génère un TL;DR global (3–5 bullets) à partir de tous les résumés par source.

    Args:
        summaries: Dictionnaire {nom_source: résumé_texte}.

    Returns:
        TL;DR en Markdown (liste de bullets).

    Raises:
        RuntimeError: En cas d'erreur d'appel à l'API Gemini.
    """
    if not summaries:
        return "- *Aucune source disponible aujourd'hui.*"

    summaries_text = "\n\n".join(
        f"### {source}\n{text}" for source, text in summaries.items()
    )
    logger.info("Summarizer : génération du TL;DR global (%d sources)...", len(summaries))

    try:
        response = _global_chain.invoke({"summaries_text": summaries_text})
        return response.content.strip()
    except Exception as exc:
        raise RuntimeError(f"Summarizer : erreur TL;DR global : {exc}") from exc
