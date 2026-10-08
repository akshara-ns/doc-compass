# Labelling guide

How we split and label the 734 posts in `data/manual/pool.ids.csv`. The label set and what each label covers are in `docs/label-set.md`.

## Who labels what

The pool already assigns every post. The tool shows you only your own posts, test posts first.

| | Akshara | Sohum |
|---|---:|---:|
| Test posts, labelled by both of us (for Cohen's κ) | 60 | 60 |
| Test posts, labelled by one of us | 65 | 65 |
| Train and dev posts | 272 | 272 |

Test posts are labelled from scratch, with nothing pre-filled. They are the answer key, so they must be our own judgement. Don't compare notes on the 60 shared posts until both of us have finished them.

## Targets

We need at least 500 labelled posts that one of us has looked at. About 1 in 6 posts is a Skip, so:

1. **All 125 of your test posts.** Never cut these.
2. **At least 210 of your train and dev posts.**

If time runs out, stop there. Don't skip test posts to get through train posts faster.

## Set up (once)

Needs Python 3.11 or newer.

```bash
git pull
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/prepare_data.py
```

`prepare_data.py` downloads the posts and writes `data/manual/pool.csv` with their text. That file stays on your laptop; git ignores it.

## Label

```bash
python tools/annotate.py --annotator sohum      # or akshara
```

The tool opens in your browser and shows one post at a time. For each post:

- **Which kind of doctor should this person book?** One of the 12 labels, or:
  - **Emergency**: needs emergency care now
  - **Skip**: not a "which doctor" question (a medication or lab-result question, general curiosity, already under a specialist for it)
- **Also acceptable** (optional): a second label that would also be fine.
- **Urgency**: routine, soon or emergency.
- **Ambiguous**: tick it if you couldn't really decide. When unsure, choose "Start with a GP" and tick ambiguous.

You can close the tool at any time; it resumes at your next unlabelled post. **Back** revisits the previous post.

## Save and share

Your labels go to `data/manual/<your name>.labels.csv`: ids and labels only, no post text. Commit and push it whenever you stop:

```bash
git add data/manual/sohum.labels.csv
git commit -m "Sohum's labels so far"
git push
```

## Time

About a minute per test post and less for train posts, so roughly 3–4 hours each. The 60 shared posts come first. Once we've both finished them, compare a few disagreements to make sure we're reading the guideline the same way, before going on.
