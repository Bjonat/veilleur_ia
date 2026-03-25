# Sprint : Implémentation complète — Agrégateur de Veille IA

> **Contexte** : Implémenter le projet décrit dans [plan-veilleIaPersonnel.prompt.md](./plan-veilleIaPersonnel.prompt.md) de A à Z dans le dossier `d:\projet_veilleur_ia\`.
> Le projet collecte des actualités IA chaque matin depuis HuggingFace, Reddit et des flux RSS, les résume en français avec Gemini 2.5 Flash via LangChain, et commit un fichier Markdown dans `digests/`.

---

## Étape 1 — Scaffolding

Créer les fichiers suivants :

### `requirements.txt`
```
feedparser>=6.0
requests>=2.31
langchain>=0.3
langchain-google-genai>=4.2
google-genai>=1.6
python-dotenv>=1.0
```

### `.env.example`
```dotenv
# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here
```

### `digests/.gitkeep`
Fichier vide pour versionner le dossier `digests/`.

### `src/__init__.py` et `src/fetchers/__init__.py`
Fichiers vides.

> ⚠️ **Modification post-sprint** : Reddit supprimé du projet (pas de credentials requis). Le fetcher `src/fetchers/reddit.py` n'existe pas.

---

## Étape 2 — Modèle de données partagé (`src/models.py`)

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Article:
    title: str
    url: str
    summary: str       # abstract HF, selftext Reddit, description RSS
    source: str        # "huggingface" | "reddit" | "rss"
    date: datetime
    subreddit: str = ""  # renseigné uniquement pour les articles Reddit
```

---

## Étape 3 — Fetchers

### `src/fetchers/huggingface.py`

- `GET https://huggingface.co/api/daily_papers`
- Retourne `list[Article]` avec `source="huggingface"`
- Parser : `paper["paper"]["title"]`, `paper["paper"]["abstract"]`, `paper["id"]` → URL = `https://huggingface.co/papers/{id}`
- En cas d'erreur HTTP, lever une exception propre

### `src/fetchers/rss.py`

- Feeds à parser :
  - arXiv CS.AI : `https://rss.arxiv.org/rss/cs.AI`
  - The Gradient : `https://thegradientpub.substack.com/feed`
- Utiliser `feedparser.parse(url)`
- Filtrer les entrées dont `published_parsed` date de moins de 24h
- Retourne `list[Article]` avec `source="rss"`

---

## Étape 4 — Summarizer (`src/summarizer.py`)

Utiliser `langchain-google-genai` :

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
```

### Prompt 1 — Résumé par bloc de source

```
Tu es un assistant de veille technologique francophone spécialisé en IA.
Voici une liste d'articles/posts issus de {source_name}.
Rédige un résumé thématique en français, structuré en courtes sections,
qui capture les tendances importantes et les annonces notables.
Sois concis, précis et évite le jargon superflu.

Articles :
{articles_text}
```

### Prompt 2 — TL;DR global

```
Tu es un assistant de veille IA. Voici les résumés de plusieurs sources du jour.
Rédige un TL;DR en français sous forme de 3 à 5 bullet points.
Chaque bullet doit capturer une tendance ou annonce majeure à retenir absolument.

Résumés :
{summaries_text}
```

- Modèle : `ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)`
- Fonctions : `summarize_source(articles: list[Article], source_name: str) -> str` et `summarize_global(summaries: dict[str, str]) -> str`

---

## Étape 5 — Formatter (`src/formatter.py`)

Assembler le Markdown final selon ce format exact :

```markdown
# 🧠 Veille IA — {date_longue_fr}

## 🌐 Résumé du jour (TL;DR)
{tldr}

---

## 📄 HuggingFace Daily Papers
{résumé_hf}

---

## � Flux RSS
{résumé_rss}

---
*Généré automatiquement par Gemini 2.5 Flash le {date} à {heure} UTC*
*Sources : HuggingFace Daily Papers · arXiv CS.AI · The Gradient*
```

- Fonction : `format_digest(date: datetime, tldr: str, summaries: dict[str, str]) -> str`
- `date_longue_fr` : ex. `"25 mars 2026"` (locale `fr_FR` ou formatage manuel)

---

## Étape 6 — Orchestrateur (`src/main.py`)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
```

Logique :

1. Charger `.env` avec `python-dotenv`
2. Lancer les 2 fetchers en parallèle avec `ThreadPoolExecutor` (HuggingFace + RSS)
3. Chaque fetcher est wrappé dans un `try/except` — si une source échoue, logger l'erreur et continuer
4. Pour chaque source ayant retourné des articles, appeler `summarize_source()`
5. Appeler `summarize_global()` avec tous les résumés disponibles
6. Appeler `format_digest()` et écrire dans `digests/YYYY-MM-DD.md`
7. Logger le nombre d'articles traités par source et le chemin du fichier généré

---

## Étape 7 — GitHub Actions (`.github/workflows/daily_digest.yml`)

```yaml
name: 🧠 Daily AI Digest

on:
  schedule:
    - cron: '0 7 * * *'  # 7h UTC = 8h Paris (CET) / 9h (CEST)
  workflow_dispatch:       # déclenchement manuel

jobs:
  generate-digest:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Setup Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Generate digest
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python src/main.py

      - name: Commit and push digest
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add digests/
          git diff --staged --quiet || git commit -m "digest: $(date -u +%Y-%m-%d)"
          git push
```

---

## Étape 8 — README.md

Rédige un `README.md` à la racine du projet qui contient :

1. **Présentation** — ce que fait le projet, pourquoi, aperçu d'un digest exemple
2. **Prérequis** — Python 3.12+, compte Google AI Studio (clé Gemini)
3. **Installation locale** :
   ```bash
   git clone <repo>
   cd projet_veilleur_ia
   pip install -r requirements.txt
   cp .env.example .env
   # Remplir .env avec les vraies clés
   python src/main.py
   ```
4. **Configuration des secrets GitHub** — 1 seul secret à créer dans Settings > Secrets : `GEMINI_API_KEY`
5. **Structure du repo** — arborescence commentée
6. **Exemple de digest** — bloc Markdown montrant le format de sortie attendu

---

## Contraintes techniques à respecter

- Python 3.12 strict — pas de `typing.Union`, utiliser `X | Y`
- `python-dotenv` charge `.env` uniquement — les variables d'environnement système sont prioritaires (comportement par défaut)
- Ne jamais logguer les clés API, même partiellement
- Aucune dépendance à `google-generativeai` (ancien SDK déprécié) — utiliser uniquement `google-genai` et `langchain-google-genai`
- `digests/` est versionné mais les fichiers `.md` générés ne doivent pas être dans `.gitignore`
- Le script doit se terminer avec exit code 0 même si une source échoue (résilience partielle)

---

## Critères de validation

- [ ] `python src/main.py` s'exécute localement sans erreur avec un `.env` valide
- [ ] Un fichier `digests/YYYY-MM-DD.md` est créé avec les 3 sections (TL;DR + HuggingFace + RSS)
- [ ] Si une source est indisponible, le digest est quand même généré avec l'autre
- [ ] Le workflow GitHub Actions s'exécute manuellement (`workflow_dispatch`) et commit un fichier dans `digests/`
- [ ] Aucun secret n'apparaît dans les logs GitHub Actions
