"""Song -> artist rankers. Each version is one documented change on top of the last.

v0_baseline    exact genre-tag overlap only (a typical first version)
v1_normalised  + clean up messy tags (case, punctuation, synonyms)
v2_multisignal + mood, tempo, vocal and lyric-theme signals
v3_tuned       v2 with weights tuned on the DEV split only
"""
from __future__ import annotations

import math
import re

THEME_WORDS: dict[str, list[str]] = {}  # filled by load_theme_words()

SYNONYMS = {
    "hip hop": "hip-hop", "hiphop": "hip-hop", "rap": "hip-hop",
    "rnb": "r&b", "r and b": "r&b", "rhythm and blues": "r&b",
    "dnb": "drum and bass", "drum & bass": "drum and bass", "drum n bass": "drum and bass",
    "singer songwriter": "singer-songwriter", "singer/songwriter": "singer-songwriter",
    "electronica": "electronic", "indie-rock": "indie rock",
    "alternative rock": "alt rock", "alt-rock": "alt rock", "neo-soul": "neo soul",
    "latin": "latin pop", "afrobeat": "afrobeats", "afro pop": "afrobeats",
    "post punk": "post-punk", "dance-pop": "dance pop", "heavy metal": "metal",
    "country music": "country",
}


def norm_tag(tag: str) -> str:
    t = re.sub(r"\s+", " ", tag.strip().lower())
    return SYNONYMS.get(t, t)


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def _rank(scores: dict[str, float]) -> list[str]:
    # Stable tie-break by artist id so results are reproducible.
    return [aid for aid, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))]


def v0_baseline(song: dict, artists: list[dict], **_) -> list[str]:
    tags = set(song["genre_tags"])
    return _rank({a["id"]: jaccard(tags, set(a["genres"])) for a in artists})


def v1_normalised(song: dict, artists: list[dict], **_) -> list[str]:
    tags = {norm_tag(t) for t in song["genre_tags"]}
    return _rank({a["id"]: jaccard(tags, {norm_tag(g) for g in a["genres"]}) for a in artists})


DEFAULT_WEIGHTS = {"genre": 1.0, "mood": 1.0, "tempo": 1.0, "vocal": 1.0, "lyrics": 1.0}


def signal_scores(song: dict, artist: dict) -> dict[str, float]:
    genre = jaccard({norm_tag(t) for t in song["genre_tags"]}, {norm_tag(g) for g in artist["genres"]})
    mood = jaccard(set(song["mood_tags"]), set(artist["moods"]))
    tempo = math.exp(-((song["tempo_bpm"] - artist["tempo_bpm"]) ** 2) / (2 * 12 ** 2))
    vocal = 1.0 if song["vocal"] == artist["vocal"] else 0.0
    words = set(song["lyrics_excerpt"].lower().split())
    hits = sum(len(words & set(THEME_WORDS.get(t, []))) for t in artist["lyric_themes"])
    lyrics = min(hits / 4, 1.0)
    return {"genre": genre, "mood": mood, "tempo": tempo, "vocal": vocal, "lyrics": lyrics}


def v2_multisignal(song: dict, artists: list[dict], weights: dict | None = None, **_) -> list[str]:
    w = weights or DEFAULT_WEIGHTS
    return _rank({a["id"]: sum(w[k] * v for k, v in signal_scores(song, a).items()) for a in artists})


# Set by evaluate.py after tuning on DEV; kept here so the result is inspectable.
TUNED_WEIGHTS: dict[str, float] = dict(DEFAULT_WEIGHTS)


def v3_tuned(song: dict, artists: list[dict], **_) -> list[str]:
    return v2_multisignal(song, artists, weights=TUNED_WEIGHTS)
