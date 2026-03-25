# Plan : L'Agrégateur de Veille IA Personnel

## Concept

Un script Python tourne chaque matin via GitHub Actions, collecte les actualités IA depuis 3 types de sources, les résume en français avec Gemini 2.5 Flash via LangChain, et commit un fichier Markdown dans `digests/` du même repo.

---

## Architecture du projet

```
projet_veilleur_ia/
├── .github/workflows/daily_digest.yml   ← Automatisation cron (0 7 * * * UTC = 8h Paris CET)
├── digests/                              ← Digests générés (ex : 2026-03-25.md)
│   └── .gitkeep
├── src/
│   ├── __init__.py
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── huggingface.py               ← API JSON HF (https://huggingface.co/api/daily_papers)
│   │   ├── reddit.py                    ← PRAW OAuth (5 subreddits, top 5 posts/24h)
│   │   └── rss.py                       ← feedparser (arXiv CS.AI + The Gradient, filtre 24h)
│   ├── summarizer.py                    ← ChatGoogleGenerativeAI("gemini-2.5-flash") via LangChain
│   ├── formatter.py                     ← Assemblage Markdown structuré
│   └── main.py                          ← Orchestrateur (ThreadPoolExecutor, try/except par source)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Sources de données

| Source | Méthode | Paramètres |
|---|---|---|
| HuggingFace Daily Papers | `GET https://huggingface.co/api/daily_papers` (JSON) | Papers du jour |
| Reddit | PRAW OAuth | r/MachineLearning · r/LocalLLaMA · r/OpenAI · r/ChatGPT · r/Claude — top 5 posts/subreddit |
| arXiv CS.AI | feedparser RSS | `https://rss.arxiv.org/rss/cs.AI` — entrées des 24 dernières heures |
| The Gradient | feedparser RSS | `https://thegradientpub.substack.com/feed` — entrées des 24 dernières heures |

---

## Modèle de données interne

```python
@dataclass
class Article:
    title: str
    url: str
    summary: str       # abstract ou selftext brut
    source: str        # "huggingface" | "reddit" | "rss"
    date: datetime
```

---

## Couche IA (summarizer.py)

- **Package** : `langchain-google-genai>=4.2` → `ChatGoogleGenerativeAI(model="gemini-2.5-flash")`
- **Prompt 1 — résumé par source** : `ChatPromptTemplate` → résumé thématique en français de N articles
- **Prompt 2 — TL;DR global** : 3–5 bullets qui synthétisent l'ensemble du digest
- **Résilience** : chaque fetcher est dans un `try/except` indépendant — l'orchestrateur continue si une source échoue

---

## Format du digest Markdown généré

```markdown
# 🧠 Veille IA — 25 mars 2026

## 🌐 Résumé du jour (TL;DR)
- ...

## 📄 HuggingFace Daily Papers
...

## 💬 Reddit IA
...

## 📡 Flux RSS
...

---
*Généré par Gemini 2.5 Flash · 08:00 CET*
```

Chemin de sortie : `digests/YYYY-MM-DD.md`

---

## GitHub Actions (daily_digest.yml)

```yaml
on:
  schedule:
    - cron: '0 7 * * *'   # 7h UTC = 8h Paris (CET) / 9h (CEST)
  workflow_dispatch:        # déclenchement manuel pour les tests
```

Étapes : `actions/checkout@v4` → `setup-python@v5` (Python 3.12) → `pip install -r requirements.txt` → `python src/main.py` → `git add digests/ ; git commit -m "digest: YYYY-MM-DD" ; git push`

---

## Requirements (requirements.txt)

```
praw>=7.8
feedparser>=6.0
requests>=2.31
langchain>=0.3
langchain-google-genai>=4.2
google-genai>=1.6
python-dotenv>=1.0
```

---

## Secrets GitHub à configurer

| Secret | Description |
|---|---|
| `GEMINI_API_KEY` | Clé Google AI Studio |
| `REDDIT_CLIENT_ID` | App Reddit de type "script" |
| `REDDIT_CLIENT_SECRET` | Secret de l'app Reddit |
| `REDDIT_USERNAME` | Pseudo Reddit |
| `REDDIT_PASSWORD` | Mot de passe Reddit |
| `GITHUB_TOKEN` | Auto-fourni par GitHub Actions |

---

## Séquence d'implémentation

1. **Scaffolding** — `requirements.txt`, `.env.example`, `__init__.py`, `digests/.gitkeep`
2. **Fetchers** — `huggingface.py` → `reddit.py` → `rss.py` (chacun retourne `list[Article]`)
3. **Summarizer** — prompts LangChain, résumé par source + TL;DR global
4. **Formatter** — assemblage Markdown final avec header/footer
5. **Orchestrateur** — `main.py` avec `ThreadPoolExecutor`, écriture du fichier
6. **GitHub Actions** — workflow cron + commit auto
7. **README** — installation locale, secrets, aperçu d'un digest exemple

---

## Hors scope (MVP)

- Interface web ou dashboard
- Base de données / historique requêtable
- Notifications email ou Slack
- Déduplication cross-sources
- Extension Chrome
