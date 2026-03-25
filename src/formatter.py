"""Formatter — assemblage du digest Markdown final."""

from datetime import datetime, timezone

_MOIS_FR = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril",
    5: "mai", 6: "juin", 7: "juillet", 8: "août",
    9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
}

_SOURCE_SECTIONS = {
    "huggingface": ("📄", "HuggingFace Daily Papers"),
    "rss":         ("📡", "Flux RSS"),
}


def _date_longue_fr(date: datetime) -> str:
    """Formate une date en français sans dépendance locale (ex: '25 mars 2026')."""
    return f"{date.day} {_MOIS_FR[date.month]} {date.year}"


def format_digest(date: datetime, tldr: str, summaries: dict[str, str]) -> str:
    """Assemble le digest Markdown complet.

    Args:
        date: Date du digest (utilisée pour le titre et le footer).
        tldr: TL;DR global généré par le summarizer.
        summaries: Dictionnaire {clé_source: texte_résumé}.
                   Clés attendues : "huggingface", "reddit", "rss".

    Returns:
        Contenu Markdown complet du digest, prêt à écrire dans un fichier.
    """
    now_utc = datetime.now(tz=timezone.utc)
    date_fr = _date_longue_fr(date)
    date_iso = date.strftime("%Y-%m-%d")
    heure_utc = now_utc.strftime("%H:%M")

    sections: list[str] = []

    # En-tête
    sections.append(f"# 🧠 Veille IA — {date_fr}\n")

    # TL;DR global
    sections.append("## 🌐 Résumé du jour (TL;DR)\n")
    sections.append(tldr)
    sections.append("\n---\n")

    # Sections par source (dans l'ordre défini)
    for source_key, (emoji, label) in _SOURCE_SECTIONS.items():
        content = summaries.get(source_key, "*Aucune donnée disponible pour cette source.*")
        sections.append(f"## {emoji} {label}\n")
        sections.append(content)
        sections.append("\n---\n")

    # Footer
    sections.append(
        f"*Généré automatiquement par Gemini 2.5 Flash le {date_iso} à {heure_utc} UTC*\n"
        "*Sources : HuggingFace Daily Papers · arXiv CS.AI · The Gradient*"
    )

    return "\n".join(sections)
