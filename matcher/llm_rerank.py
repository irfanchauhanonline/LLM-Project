"""v4: ask an LLM (Claude) to re-rank the top 10 candidates from v3.

Why re-rank only the top 10: the cheap offline scorer narrows 24 artists to 10,
so each LLM call is short (lower cost and latency) and the LLM only judges
close calls, where its understanding of lyrics and style adds most value.

Requires `pip install anthropic` and an ANTHROPIC_API_KEY. Responses are cached
in results/llm_cache.json so re-running the evaluation does not re-spend money.
"""
from __future__ import annotations

import json
from pathlib import Path

from matcher import rankers

CACHE = Path(__file__).resolve().parent.parent / "results" / "llm_cache.json"
MODEL = "claude-opus-5-5"
TOP_N = 10

SYSTEM = """You are an experienced A&R assistant. Given one song and a shortlist of artists, \
rank the artists from most to least suitable to record or release the song.

Judge on: genre and sub-genre fit, mood, tempo and energy, vocal type, and whether the \
lyric themes suit the artist's catalogue. Metadata may be incomplete or noisy (missing \
genre tags, tempo reported at half or double speed, speech-to-text errors in lyrics); \
use the other signals when one is unreliable. Return every artist id exactly once."""

SCHEMA = {
    "type": "object",
    "properties": {
        "ranked_artist_ids": {"type": "array", "items": {"type": "string"}},
        "reason_for_top_pick": {"type": "string"},
    },
    "required": ["ranked_artist_ids", "reason_for_top_pick"],
    "additionalProperties": False,
}


def _load_cache() -> dict:
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def _prompt(song: dict, shortlist: list[dict]) -> str:
    song_view = {k: song[k] for k in ("title", "genre_tags", "mood_tags", "tempo_bpm", "vocal", "lyrics_excerpt")}
    return (f"<song>\n{json.dumps(song_view, indent=2)}\n</song>\n\n"
            f"<artists>\n{json.dumps(shortlist, indent=2)}\n</artists>")


def v4_llm_rerank(song: dict, artists: list[dict], **_) -> list[str]:
    import anthropic  # imported here so the offline evaluation needs no extra install

    base = rankers.v3_tuned(song, artists)
    by_id = {a["id"]: a for a in artists}
    shortlist = [by_id[aid] for aid in base[:TOP_N]]

    cache = _load_cache()
    if song["id"] not in cache:
        client = anthropic.Anthropic()
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM,
            messages=[{"role": "user", "content": _prompt(song, shortlist)}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            # If the request is declined by a safety filter, retry on a fallback model in the same call.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            return base  # keep the offline ranking rather than fail
        text = next(b.text for b in response.content if b.type == "text")
        cache[song["id"]] = {
            **json.loads(text),
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(cache, indent=2))

    llm_order = [aid for aid in cache[song["id"]]["ranked_artist_ids"] if aid in by_id]
    # Guard against a malformed answer: keep any shortlisted artist the LLM dropped, then the rest.
    seen = list(dict.fromkeys(llm_order + base[:TOP_N]))
    return seen + [aid for aid in base if aid not in seen]
