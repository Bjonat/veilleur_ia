# Instructions Copilot — Agrégateur de Veille IA

## Contexte du projet

Script Python automatisé qui tourne chaque matin via GitHub Actions.  
Il collecte les dernières actualités IA depuis HuggingFace et des flux RSS, les résume **en français** avec **Gemini 2.5 Flash** via LangChain, et commit un fichier Markdown daté dans `digests/`.

## Commandes essentielles

```bash
# Installation
pip install -r requirements.txt
cp .env.example .env          # remplir GEMINI_API_KEY

# Lancer une génération locale
python -m src.main            # → écrit digests/YYYY-MM-DD.md
```

Aucune étape de build ou de test automatisé pour l'instant.  
Le CI (GitHub Actions) est entièrement géré par [.github/workflows/daily_digest.yml](.github/workflows/daily_digest.yml).

## Architecture

```
src/
├── main.py          ← orchestrateur (ThreadPoolExecutor → summarize → format → write)
├── models.py        ← dataclass Article partagée
├── summarizer.py    ← deux chaînes LangChain : par source + TL;DR global
├── formatter.py     ← assemblage Markdown final (date FR sans locale)
└── fetchers/
    ├── huggingface.py  ← GET https://huggingface.co/api/daily_papers
    └── rss.py          ← feedparser sur arXiv CS.AI + The Gradient (filtre 24 h)
```

**Flux de données :** fetchers → `list[Article]` → summarizer → formatter → `digests/YYYY-MM-DD.md`

## Conventions du projet

### Langue
Tout est **en français** : prompts LLM, messages de log, commentaires, sorties Markdown.

### Gestion des erreurs
Chaque appel fetcher et summarizer est enveloppé dans un `try/except`.  
Un source qui échoue produit une liste vide ou un message de fallback — le pipeline ne s'arrête jamais pour une source isolée.  
Les catches larges intentionnels sont annotés `# noqa: BLE001`.

### Parallélisme
Les fetchers tournent en parallèle via `ThreadPoolExecutor(max_workers=3)` avec `as_completed()`.

### LLM
- Modèle : `gemini-2.5-flash`, `temperature=0.3`
- Les instances LLM et les chaînes sont créées **une seule fois au chargement du module** dans `summarizer.py`.
- Ne pas changer le modèle sans mettre à jour le nom dans `summarizer.py`.

### Formatage des dates
Le dictionnaire `_MOIS_FR` dans `formatter.py` gère la conversion mois → français sans dépendance à la locale OS. Ne pas utiliser `locale.setlocale()`.

### Troncature des résumés
- Abstracts HuggingFace : 600 caractères max (dans `summarizer.py`, fonction `_format_articles`)
- Résumés RSS : 800 caractères max (dans `rss.py`)

## Variable d'environnement requise

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Clé API Google AI Studio ([aistudio.google.com](https://aistudio.google.com/app/apikey)) |

## Secret GitHub Actions

Seul `GEMINI_API_KEY` est nécessaire dans **Settings → Secrets and variables → Actions**.  
`GITHUB_TOKEN` est fourni automatiquement par GitHub.

## Fichiers de référence

- Plan d'architecture : [.github/prompts/plan-veilleIaPersonnel.prompt.md](.github/prompts/plan-veilleIaPersonnel.prompt.md)
- Sprint d'implémentation : [.github/prompts/sprint.prompt.md](.github/prompts/sprint.prompt.md)
- Workflow CI : [.github/workflows/daily_digest.yml](.github/workflows/daily_digest.yml)
