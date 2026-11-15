# Draft reply to the client (edit before sending)

> Fill in the [brackets]. Do not claim past client projects you have not done; the sample
> below is real work you can show and explain line by line.

Hi [Name],

Thank you for the clear brief. Measuring accuracy before changing anything is exactly how I
like to work, and I've built a small sample to show my approach.

**1. Examples of similar work**

- **Song → artist matching evaluation (sample built for this application):** [GitHub link].
  It builds a labelled test set, measures Hit@3, Hit@5 and MRR, and improves a matcher in
  steps, each with before/after numbers on a held-out test set. It includes an LLM re-ranking
  step with structured output and cached responses to control cost. The data is synthetic
  (I haven't seen yours), but it imitates real problems: missing tags, tempo errors,
  speech-to-text noise and similar-looking artists. Current result on the sample: Hit@3 went
  from 65% (baseline) to 98%, and the report flags which gains are statistically solid and
  which are too small to claim.
- **[Second example: your real project, e.g. a search/recommendation/LLM feature you built,
  with one line on what you measured and the result. If you don't have one, say plainly what
  you have done that is closest.]**

**2. How I would measure whether the matching is getting better**

- Agree with you what a "suitable artist" is, then label a fixed set of real songs (start with
  100–200; several suitable artists per song is fine). Keep part of it held back for final
  reporting only.
- Run the current system unchanged to get the baseline: Hit@3, Hit@5, Hit@1 and MRR.
- Change one thing at a time (prompt, inputs from lyrics/audio, model, ranking logic) and
  re-run. For each change, report the numbers, the songs it fixed and the songs it broke, plus
  cost per song and response time.
- With a small test set, a 2–3% change can be noise, so I'd state when a result is not
  conclusive rather than claim it.

**3. Rate, availability, time zone**

[£X/hour] · [N hours/week] · [time zone, and the UK hours I can cover]

**4. Questions**

- Who decides the "correct" artists for a song today, and could they label a test set with me?
- Roughly how many artists and songs are in the system?
- Is the matching mainly an LLM prompt, embeddings/similarity, or rules? Which AI and
  speech-to-text providers are used?
- Do you log real matches or user feedback (e.g. which suggestions were accepted)?
- Is there a cost or speed limit per match I should stay within?

Best regards,
[Your name]
