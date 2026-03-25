# 🧠 Agrégateur de Veille IA Personnel

Un script Python qui tourne chaque matin via GitHub Actions, collecte les dernières actualités IA depuis HuggingFace, et des flux RSS, les résume en français avec **Gemini 2.5 Flash**, et commit un fichier Markdown dans ce repo.

---

## Aperçu d'un digest généré

```markdown
# 🧠 Veille IA — 25 mars 2026

## 🌐 Résumé du jour (TL;DR)
- Un nouveau modèle de diffusion dépasse Stable Diffusion sur les benchmarks texte-image
- Meta publie une étude sur les LLM multi-agents capables de se corriger mutuellement
- Un modèle 7B open-source atteint des perfs inédites en inférence locale

## 📄 HuggingFace Daily Papers
**Diffusion Models Strike Back** — Un paper propose une architecture hybride...

## 📡 Flux RSS
**arXiv CS.AI** — 3 papers notables aujourd'hui sur le fine-tuning RLHF...

---
*Généré automatiquement par Gemini 2.5 Flash le 2026-03-25 à 07:02 UTC*
```

---

## Prérequis

- **Python 3.12+**
- **Clé Google AI Studio** (Gemini) — [aistudio.google.com](https://aistudio.google.com/app/apikey)

---

## Installation locale

```bash
git clone https://github.com/<votre-compte>/projet_veilleur_ia.git
cd projet_veilleur_ia

pip install -r requirements.txt

cp .env.example .env
# Ouvrir .env et remplir la variable GEMINI_API_KEY
```

Lancer une génération :

```bash
python -m src.main
# → crée digests/YYYY-MM-DD.md
```

---

## Configuration des secrets GitHub

Dans **Settings → Secrets and variables → Actions**, créer les secrets suivants :

| Secret | Description |
|---|---|
| `GEMINI_API_KEY` | Clé API Google AI Studio |

> `GITHUB_TOKEN` est fourni automatiquement par GitHub Actions — rien à configurer.

---

## Structure du repo

```
projet_veilleur_ia/
├── .github/
│   ├── prompts/               ← Fichiers de conception du projet
│   └── workflows/
│       └── daily_digest.yml   ← Cron 7h UTC (8h Paris CET)
├── digests/                   ← Digests générés au format YYYY-MM-DD.md
├── src/
│   ├── fetchers/
│   │   ├── huggingface.py     ← API JSON HuggingFace Daily Papers
│   │   └── rss.py             ← feedparser (arXiv CS.AI, The Gradient)
│   ├── models.py              ← Dataclass Article partagée
│   ├── summarizer.py          ← LangChain + Gemini 2.5 Flash
│   ├── formatter.py           ← Assemblage Markdown final
│   └── main.py                ← Orchestrateur (ThreadPoolExecutor)
├── requirements.txt
├── .env.example               ← Template de configuration locale
└── README.md
```

---

## Déclenchement manuel

Pour tester le workflow sans attendre le cron :

1. Aller dans **Actions** → **🧠 Daily AI Digest**
2. Cliquer **Run workflow** → **Run workflow**
3. Vérifier qu'un fichier apparaît dans `digests/` après ~1 minute

---

## Sources surveillées

| Source | Contenu |
|---|---|
| HuggingFace Daily Papers | Papers IA publiés le jour même |
| arXiv CS.AI | Derniers preprints en intelligence artificielle |
| The Gradient | Articles de fond sur la recherche en ML |
