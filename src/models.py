from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    title: str
    url: str
    summary: str       # abstract HF, selftext Reddit, description RSS
    source: str        # "huggingface" | "reddit" | "rss"
    date: datetime
    subreddit: str = field(default="")  # renseigné uniquement pour les articles Reddit
