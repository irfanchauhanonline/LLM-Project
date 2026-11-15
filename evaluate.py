"""Run every ranker version, tune v3 on DEV, report on TEST with before/after.

Usage:
    python evaluate.py            # offline rankers only (free, ~1s)
    python evaluate.py --llm      # also run the optional Claude re-ranker (needs API key, costs money)
"""
from __future__ import annotations

import argparse
import itertools
import json
from datetime import date
from pathlib import Path

from matcher import rankers
from matcher.metrics import bootstrap_ci, hit_at_k, reciprocal_rank, summarise

ROOT = Path(__file__).resolve().parent
DATA, RESULTS = ROOT / "data", ROOT / "results"


def load():
    artists = json.loads((DATA / "artists.json").read_text())
    songs = json.loads((DATA / "songs.json").read_text())
    rankers.THEME_WORDS.update(json.loads((DATA / "theme_lexicon.json").read_text()))
    return artists, songs


def run(ranker, songs, artists, **kw) -> list[dict]:
    rows = []
    for s in songs:
        ranked = ranker(s, artists, **kw)
        gold = set(s["gold_artist_ids"])
        rows.append({
            "song": s["id"], "gold": sorted(gold), "top5": ranked[:5],
            "hit@1": hit_at_k(ranked, gold, 1), "hit@3": hit_at_k(ranked, gold, 3),
            "hit@5": hit_at_k(ranked, gold, 5), "rr": reciprocal_rank(ranked, gold),
        })
    return rows


def tune_weights(dev, artists) -> dict[str, float]:
    """Small grid search on DEV only, optimising MRR. TEST is never seen here."""
    grid = [0.0, 0.5, 1.0, 2.0]
    best, best_w = -1.0, None
    for g, m, t, v, l in itertools.product([1.0, 2.0, 3.0], grid, grid, grid, grid):
        w = {"genre": g, "mood": m, "tempo": t, "vocal": v, "lyrics": l}
        score = summarise(run(rankers.v2_multisignal, dev, artists, weights=w))["mrr"]
        if score > best:
            best, best_w = score, w
    return best_w


def verdict(fixed: int, broke: int) -> str:
    """Honest read of a change: a two-sided sign test on the songs that changed."""
    from math import comb
    n, k = fixed + broke, min(fixed, broke)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    if p < 0.05:
        return f" **Real improvement** (sign test p={p:.3f})." if fixed > broke else f" **Real regression** (p={p:.3f})."
    return f" _Not conclusive (p={p:.2f}); too few songs changed to claim a win._"


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true", help="also run the Claude re-ranker on TEST")
    args = ap.parse_args()

    artists, songs = load()
    dev = [s for s in songs if s["split"] == "dev"]
    test = [s for s in songs if s["split"] == "test"]

    rankers.TUNED_WEIGHTS.update(tune_weights(dev, artists))

    versions = [
        ("v0_baseline", "Exact genre-tag overlap (starting point)", rankers.v0_baseline),
        ("v1_normalised", "+ clean messy tags (case, synonyms)", rankers.v1_normalised),
        ("v2_multisignal", "+ mood, tempo, vocal, lyric themes (equal weights)", rankers.v2_multisignal),
        ("v3_tuned", "+ weights tuned on DEV split", rankers.v3_tuned),
    ]
    if args.llm:
        from matcher.llm_rerank import v4_llm_rerank
        versions.append(("v4_llm_rerank", "+ Claude re-ranks v3's top 10", v4_llm_rerank))

    RESULTS.mkdir(exist_ok=True)
    results = {}
    for name, desc, fn in versions:
        rows = run(fn, test, artists)
        results[name] = {"desc": desc, "summary": summarise(rows), "rows": rows,
                         "ci_hit3": bootstrap_ci([r["hit@3"] for r in rows]),
                         "ci_hit5": bootstrap_ci([r["hit@5"] for r in rows])}
        (RESULTS / f"{name}.json").write_text(json.dumps(rows, indent=2))

    # ---- Markdown report -------------------------------------------------
    out = [f"# Song → Artist Matching: Evaluation Report",
           f"_Generated {date.today()} by `python evaluate.py`. Synthetic demo data._", "",
           f"**Test set:** {len(test)} songs (held out; never used for tuning). "
           f"**Dev set:** {len(dev)} songs. **Artists:** {len(artists)}.", "",
           "A song is a **hit@k** if at least one suitable artist appears in the top k. "
           "**MRR** rewards putting the first suitable artist higher (1.0 = always rank 1).", "",
           "## Results on TEST", "",
           "| Version | Change | Hit@1 | Hit@3 | Hit@5 | MRR |", "|---|---|---|---|---|---|"]
    for name, r in results.items():
        s = r["summary"]
        out.append(f"| `{name}` | {r['desc']} | {pct(s['hit@1'])} | {pct(s['hit@3'])} | "
                   f"{pct(s['hit@5'])} | {s['mrr']:.3f} |")
    out += ["", "### 95% confidence intervals (bootstrap)", "",
            f"With only {len(test)} test songs, small differences can be noise. These ranges show how sure we can be.", "",
            "| Version | Hit@3 range | Hit@5 range |", "|---|---|---|"]
    for name, r in results.items():
        (a, b), (c, d) = r["ci_hit3"], r["ci_hit5"]
        out.append(f"| `{name}` | {pct(a)} – {pct(b)} | {pct(c)} – {pct(d)} |")

    out += ["", "## Before / after, step by step", ""]
    names = list(results)
    for prev, cur in zip(names, names[1:]):
        p = {r["song"]: r for r in results[prev]["rows"]}
        c = {r["song"]: r for r in results[cur]["rows"]}
        fixed = [sid for sid in c if c[sid]["hit@3"] > p[sid]["hit@3"]]
        broke = [sid for sid in c if c[sid]["hit@3"] < p[sid]["hit@3"]]
        d3 = results[cur]["summary"]["hit@3"] - results[prev]["summary"]["hit@3"]
        out.append(f"- **`{prev}` → `{cur}`**: Hit@3 {d3:+.1%}. "
                   f"Songs newly in top 3: {len(fixed)}. Songs that dropped out: {len(broke)}"
                   + (f" ({', '.join(broke)})" if broke else "") + "."
                   + verdict(len(fixed), len(broke)))

    out += ["", f"**Tuned weights (from DEV):** `{rankers.TUNED_WEIGHTS}`", "",
            "## Where the best offline version still fails (TEST)", "",
            "| Song | Suitable artist(s) | Our top 5 |", "|---|---|---|"]
    best = results["v3_tuned"]["rows"]
    names_by_id = {a["id"]: a["name"] for a in artists}
    for r in [r for r in best if not r["hit@3"]][:10]:
        out.append(f"| {r['song']} | {', '.join(names_by_id[g] for g in r['gold'])} | "
                   f"{', '.join(names_by_id[a] for a in r['top5'])} |")
    (RESULTS / "REPORT.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\nFull report: {RESULTS / 'REPORT.md'}")


if __name__ == "__main__":
    main()
