# Labelling guide

How we split and label the 734 posts in `data/manual/pool.ids.csv`. The label set and what each label covers are in `docs/label-set.md`.

> **Decision, 8 Oct:** for the 8 Oct submission we use the AI-drafted first-pass labels in `data/manual/draft.labels.csv` as the gold labels, unreviewed (`python scripts/merge_labels.py --from-drafts`). The review process below is how the labels would be checked by us; it was not carried out for this submission.

## Who labels what

The pool already assigns every post. The tool shows you only your own posts, test posts first.

| | Akshara | Sohum |
|---|---:|---:|
| Test posts, labelled by both of us (for Cohen's κ) | 60 | 60 |
| Test posts, labelled by one of us | 65 | 65 |
| Train and dev posts | 272 | 272 |

Every post opens with a first-pass label drafted by an AI assistant (`data/manual/draft.labels.csv`), which you confirm or change. Test posts are the answer key, so check each draft properly against the guideline rather than accepting it: the tool records whether you changed it, and the report states how often we did. Don't compare notes on the 60 shared posts until both of us have finished them.

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
  - **Emergency**: the post describes one of the warning signs below, happening now (see "When a post is an emergency")
  - **Skip**: not a "which doctor" question (a medication or lab-result question, general curiosity, already under a specialist for it)
- **Also acceptable** (optional): a second label that would also be fine.
- **Urgency**: routine or soon. Use "emergency" only together with the Emergency label.
- **Ambiguous**: tick it if you couldn't really decide. When unsure, choose "Start with a GP" and tick ambiguous.

You can close the tool at any time; it resumes at your next unlabelled post. **Back** revisits the previous post.

### When a post is an emergency

Label a post **Emergency** only if it describes one of these warning signs **happening now**. They are the same signs the app's emergency check uses (`WARNING_SIGNS` in `doccompass/redflags.py`), so our labels test the check against the definition it is built on.

MedlinePlus, "Recognizing medical emergencies":

1. Bleeding that will not stop
2. Breathing problems (difficulty breathing, shortness of breath)
3. Change in mental status (such as unusual behavior, confusion, difficulty arousing)
4. Chest pain or discomfort lasting for two minutes or more
5. Choking
6. Coughing up or vomiting blood
7. Fainting or loss of consciousness
8. Feeling of committing suicide or murder
9. Head or spine injury
10. Inability to speak
11. Severe abdominal pain or pressure
12. Severe or persistent vomiting or diarrhea
13. Sudden injury from a motor vehicle accident, burns, smoke inhalation, near drowning, or a deep or large wound
14. Sudden, severe pain anywhere in the body
15. Sudden dizziness, weakness, or change in vision
16. Swallowing a poisonous substance
17. Swelling of the face, eyes, or tongue

CDC, "Signs and Symptoms of Stroke":

18. Sudden numbness or weakness in the face, arm, or leg, especially on one side
19. Sudden confusion, trouble speaking, or difficulty understanding speech
20. Sudden trouble seeing
21. Sudden trouble walking, dizziness, loss of balance, or lack of coordination
22. Sudden severe headache with no known cause

Rules of thumb:

- **Happening now, or still going on.** "I had chest pain last year" is not an emergency; "my chest has been tight for the last hour" is.
- **Judge the description, not the poster's worry.** A post that is frightened but describes none of these signs gets a specialty or "Start with a GP", with urgency "soon" if it shouldn't wait.
- **An emergency is always the Emergency label,** never a specialty with urgency "emergency". Emergency posts are kept out of the router's training data and used to test the emergency check instead.
- **Not sure whether it counts?** Choose Emergency and tick ambiguous. We go through those together.

## Save and share

Your labels go to `data/manual/<your name>.labels.csv`: ids and labels only, no post text. Commit and push it whenever you stop:

```bash
git add data/manual/sohum.labels.csv
git commit -m "Sohum's labels so far"
git push
```

## Merge and check agreement

Once both label files are pushed, either of us runs:

```bash
git pull
python scripts/merge_labels.py
```

It prints how often we agree on the shared posts (including Cohen's κ) and writes `data/manual/gold.labels.csv`, one label per post with its split. Where we disagree on a shared post, it adds the post to `data/manual/adjudicated.labels.csv` with both our labels. Talk those through, fill in the `primary` column (and `alternate`, `urgency` and `ambiguous` if you want), run the script again, and commit all three files.

The 50 or so dev posts are fixed in advance from the randomly drawn train posts, so the tool shows them right after the test posts.

## Time

About 20–40 seconds per post to check a draft, so roughly 2–3 hours each. The 60 shared posts come first. Once we've both finished them, compare a few disagreements to make sure we're reading the guideline the same way, before going on.
