# Song → Artist Matching: Evaluation Report
_Generated 2026-11-15 by `python evaluate.py`. Synthetic demo data._

**Test set:** 60 songs (held out; never used for tuning). **Dev set:** 120 songs. **Artists:** 24.

A song is a **hit@k** if at least one suitable artist appears in the top k. **MRR** rewards putting the first suitable artist higher (1.0 = always rank 1).

## Results on TEST

| Version | Change | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---|---|---|---|---|
| `v0_baseline` | Exact genre-tag overlap (starting point) | 50.0% | 65.0% | 71.7% | 0.607 |
| `v1_normalised` | + clean messy tags (case, synonyms) | 56.7% | 73.3% | 78.3% | 0.673 |
| `v2_multisignal` | + mood, tempo, vocal, lyric themes (equal weights) | 86.7% | 96.7% | 100.0% | 0.921 |
| `v3_tuned` | + weights tuned on DEV split | 88.3% | 98.3% | 100.0% | 0.931 |

### 95% confidence intervals (bootstrap)

With only 60 test songs, small differences can be noise. These ranges show how sure we can be.

| Version | Hit@3 range | Hit@5 range |
|---|---|---|
| `v0_baseline` | 53.3% – 76.7% | 60.0% – 81.7% |
| `v1_normalised` | 61.7% – 85.0% | 66.7% – 88.3% |
| `v2_multisignal` | 91.7% – 100.0% | 100.0% – 100.0% |
| `v3_tuned` | 95.0% – 100.0% | 100.0% – 100.0% |

## Before / after, step by step

- **`v0_baseline` → `v1_normalised`**: Hit@3 +8.3%. Songs newly in top 3: 5. Songs that dropped out: 0. _Not conclusive (p=0.06); too few songs changed to claim a win._
- **`v1_normalised` → `v2_multisignal`**: Hit@3 +23.3%. Songs newly in top 3: 14. Songs that dropped out: 0. **Real improvement** (sign test p=0.000).
- **`v2_multisignal` → `v3_tuned`**: Hit@3 +1.7%. Songs newly in top 3: 1. Songs that dropped out: 0. _Not conclusive (p=1.00); too few songs changed to claim a win._

**Tuned weights (from DEV):** `{'genre': 1.0, 'mood': 0.5, 'tempo': 0.5, 'vocal': 1.0, 'lyrics': 1.0}`

## Where the best offline version still fails (TEST)

| Song | Suitable artist(s) | Our top 5 |
|---|---|---|
| s135 | Lena Marr | Juno Hart, Amber Lowe, Rue Delacroix, Velvet Hours, Lena Marr |
