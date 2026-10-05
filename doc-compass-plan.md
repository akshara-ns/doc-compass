# Doc Compass: project plan

**Project 1 · plan of record · v2, revised after the feasibility check on 27 Sep 2026 · updated 4 Oct 2026**

A specialist router. Describe a health concern in plain language and get told which kind of doctor to book. Routing, not diagnosis — which door to knock on, never what you have.

| Field | Value |
|---|---|
| Team | Akshara (`akshara-ns`) and Sohum (`ssg1`) |
| Deadlines | Presentation 5 Oct 2026; code and report 8 Oct 2026 |
| GUI | Gradio app, run from a Colab notebook that prints a public link and QR code (Gradio Spaces on Hugging Face now need a paid plan). Code and models: `ssg1/doc-compass` on Hugging Face |
| Model types | All three: from scratch, fine-tuned, off-the-shelf (the brief asks for at least two) |
| Focus | Routing. Redaction is out of scope for now: we assume users type relevant, non-identifying text. A simple rule-based scrub may be added for completeness, and full redaction later if time allows |
| Manual data | 600 labelled posts (400 train / 50 dev / 150 test) |
| Headline result | The routers against "always GP" and against each other on our own 150 test posts |
| Stage-1 data | Patient Comments and Specialist Types, a public set remapped to our labels. Used for stage-1 training only, never as the test set |
| Annotation effort | ≈ 7 person-hours across both of us; 60 of the 150 test posts are labelled by both of us for Cohen's κ |
| Completion estimate | ≈ 65% with this scope (the v1 scope was ≈ 25% in one week) |

Current figure: `docs/checkin/checkin_figure_v3.png` (4 Oct). The 27 Sep check-in figure, `docs/checkin/checkin_figure.png`, is kept as it was. Label set and public-data mapping: `docs/label-set.md`.

---

## Where things stand (4 Oct, evening)

**Built and working**

- **The app, end to end:** emergency rules → scrub → router → explanation, in a Gradio interface. It runs locally and from the Colab notebook `notebooks/doc_compass_app.ipynb`.
- **Emergency check, in two layers:** 11 written rules, each quoting a warning sign published by MedlinePlus (US National Library of Medicine) or the CDC. When no rule fires and Qwen is loaded, Qwen is shown the full published list and asked whether the message describes any of those signs happening now. Either one firing shows the emergency sign.
- **Emergency check, measured (5 Oct).** On 362 real r/AskDocs posts with clinician-derived urgency (PMR-Reddit), 38 of them emergencies: the rules alone miss 26 (68%); rules plus the Qwen check miss 13 (34%) and wrongly flag 20% of ordinary posts. On 80 short cases we wrote, rules plus Qwen miss 1 of 40. Real emergencies are mostly about a clinical pattern, not wording, so the check is described as catching clearly stated warning signs, not as detecting emergencies. We also tried trained classifiers; none was usable. Full tables and caveats: `docs/emergency-check-results.md`.
- **Stage 1 for all three routers,** trained on the public Patient Comments set and scored on the same 938 held-out comments from it:

  | Router | Type | Top-1 (95% CI) | Top-3 | Macro-F1 |
  |---|---|---|---|---|
  | TF-IDF + logistic regression | from scratch | 94.0% (92.3–95.5) | 98.6% | 0.902 |
  | DistilRoBERTa | fine-tuned | 94.3% (92.7–95.7) | 99.0% | 0.908 |
  | BiomedBERT | fine-tuned | 94.2% (92.6–95.6) | 98.8% | 0.904 |

  The intervals overlap, so the three are tied on public data. The comments are short and alike, so this is an easy score; our own 150 test posts are the real test.
- **Explanation:** Qwen2.5-1.5B-Instruct writes one sentence in a fixed pattern plus three questions. Its text is checked before it is shown, and fixed wording is the fallback.
- **Labelling:** the 734 posts to label are chosen (`data/manual/pool.ids.csv`) and the labelling tool is ready (`tools/annotate.py`).
- **Published:** the code and stage-1 routers are in a public Hugging Face repo, `ssg1/doc-compass`, which the notebook downloads.

**What stage 1 showed**

- Outside the public set's wording the routers can be confidently wrong: "my gums bleed when I brush" goes to Ob-Gyn at 94–96% on the fine-tuned routers, because the public set only files "bleeding" under Ob-Gyn.
- The fine-tuned routers give 98–99% on easy inputs, so the two-option "unsure" state rarely appears until the cutoffs are tuned on dev.

**Not done yet**

- Labelling the posts; stage 2 (training on our own posts); tuning the cutoffs; evaluation on our test posts; the data card and the report.

**Decisions made on 4 Oct**

- **Two-stage training.** Stage 1 on a public dataset of short patient comments; stage 2 on our own labelled posts. Stage 1 needs none of our labels, so the app works before labelling is finished.
- **600 posts, not 1,000.** 400 train / 50 dev / 150 test. The brief's text asks for at least 500.
- **Labelling.** Each post gets a primary label, an optional alternate, an urgency tier and an ambiguous tick. The 150 test posts are a plain random sample, and 60 of them are labelled by both of us for Cohen's κ.
- **Label set:** eleven specialties plus "Start with a GP". "Emergency" and "Skip" exist only while labelling. See `docs/label-set.md`.
- **Skips.** About 1 in 6 posts in a 60-post pilot was not a "which doctor" question, so the pool is larger than 600 and labelling has a Skip option.
- **Headline result:** the fine-tuned routers against "always GP" and against the from-scratch router on our own test posts. The human-baseline form is dropped.
- **MedRedQA is not used.** Its labels say who answered, not where to book.
- **Earlier (29 Sep – 3 Oct):** redaction on hold, clinician check and PII spans dropped, Qwen2.5-1.5B kept for the explanation.

---

## What changed in v2, and why

| v1 plan | Problem found | v2 plan |
|---|---|---|
| Train routers on posts scraped from specialty subreddits (distant supervision) | Reddit's Data API Terms §3.2 forbid "using User Content to train a machine learning or AI model without the express permission of rightsholders"; the Developer Terms §4.2 and User Agreement ban scraping. New API apps need manual approval since Nov 2025 (weeks). Six of the planned subreddits are for professionals only, r/ENT is an entheogen community, r/Urology doesn't exist, and the patient-facing replacements are condition subreddits whose posts name the answer. | Stage 1 on the public Patient Comments set, remapped to our labels; stage 2 on our own gold training split. MedRedQA is not used: its labels are weak and it would cost time we don't have. |
| Headline metric: self-routing baseline (subreddit chosen vs gold label) | Every MediQ_AskDocs post comes from one general forum, so there is nothing to compare. It also depended on the subreddit data above. | **Headline:** the fine-tuned routers against "always GP" and against the from-scratch router, on our own 150 test posts. A human baseline (students picking a doctor for the same posts) was planned and is dropped for lack of time. |
| Gold set fully held out; nothing trained on it | Without distant supervision there is no other routing training data. | Split the 600 by post: 400 train, 50 dev, 150 test. The test split is never trained on or tuned against. |
| Scrape iCliniq specialty sections as a fallback | iCliniq's Terms of Use forbid scraping "for commercial or any other purpose whatsoever"; HF copies have no specialty field. | Dropped. |
| ai4privacy for PII augmentation | Custom licence: redistribution and derivative works need written permission. A public model trained on it is a derivative. | Use `nvidia/Nemotron-PII` (CC BY 4.0) if full redaction comes back later. |
| "55,071 MediQ posts" | Rows repeat each post once per doctor question, and part of the repo is synthetic. | 10,366 unique real posts (checked 29 Sep). Deduplicate on post text and skip the `synthetic/` folder. |
| Free CPU Space | Gradio Spaces on Hugging Face now need a paid plan. | The app runs from a Colab notebook with a public link. |
| LLM via an external API | Text would leave our app and go to a third party. | `Qwen/Qwen2.5-1.5B-Instruct`, run locally and used as-is (not trained), with a template fallback. It sees only the concern text and the router's output. |
| Redact, then red-flag check | Our notes disagreed on the order. | Red-flag rules run first on the raw text, before anything else. |
| Redaction as a full second task (Presidio, CRF, PII spans on 300 posts, TAB benchmark) | Splits a one-week build across two problems; on real posts Presidio also tagged durations and drug names, which would strip routing signal. | Out of scope for now. Routing is the focus; at most a simple rule-based scrub. Full redaction returns only if time allows. |
| 1,000 posts × two full layers, 200 double-labelled, clinician on 100 | ≈ 40 person-hours before any modelling; no clinician recruited. | Routing labels on 600, 60 double-labelled, no PII spans. No clinician check: we have no expert to do one. |
| Ten or more models | Too many for one week. | Core set below; everything else is a stretch goal. |

---

## Decisions

- **Manual data.** We label existing public posts from MediQ_AskDocs: 600 of them, at least the 500 the brief asks for.
- **Training and testing.** The labelled posts are split by post into train / dev / test. Nothing is trained or tuned on the test split.
- **Hosting.** Gradio Spaces on Hugging Face now need a paid plan, so the app runs from a Colab notebook that prints a public link and QR code. The link is new on each run and works while the notebook is running.
- **Model types.** TF-IDF + logistic regression is the trained-from-scratch model.
- **Annotation.** No clinician check and no PII spans.
- **MedRedQA.** Not used.

**Decide later**

- **Human baseline.** Dropped for now: a form where international students pick a specialty for the same posts. It would be a good follow-up.
- Publishing the gold labels on HF as a labels-only dataset (labels + MediQ ids, no text): not required.
- Report format and length, and whether the GenAI log has a template.

---

## Project description

> We're both interested in healthcare navigation, and think a system that could take a plain-language description of a health concern and suggest which specialty to actually book would be pretty great. It's a routing tool rather than a diagnostic one — which door to knock on, not what you have — with "start with a GP" as a first-class answer and a hard escape hatch for emergency symptoms. A user will interact with it through a Gradio GUI: paste a concern and get back a ranked top-3 of specialties with confidence scores and a short rationale. We'll use 600 manually labelled patient posts from MediQ_AskDocs and all three model types — a TF-IDF classifier trained from scratch, a fine-tuned DistilRoBERTa, and an off-the-shelf instruct LLM — built with Hugging Face transformers, scikit-learn, and Gradio. We think there's about a 65% chance we'll complete this before the deadline.

---

## How a request moves through the system

1. **Red-flag check** — Eleven written rules scan the raw text first, each quoting a published warning sign (MedlinePlus, CDC). A plain negation ("no chest pain") cancels a match; past events ("I had chest pain last year") still fire. If no rule fires, Qwen gets a second look for wording the rules can't match. Either one firing short-circuits straight to "Seek emergency care now" and nothing else runs. *(Written rules first; an off-the-shelf model as the safety net)*
2. **Scrub (optional)** — Simple rules remove obvious identifiers (`u/` handles, emails, phone numbers, links) and show what was removed. We otherwise assume the input is relevant and non-identifying. *(Rules; full redaction is a later extension)*
3. **Route** — Top-3 bookable specialties with confidence. When the router is unsure (the top probability is below τ, or the top two are close), the app doesn't give one answer: it shows the top two as alternatives, says what separates them, and lets the user decide, with "Start with a GP" as the fallback. Both cutoffs are tuned on dev. *(TF-IDF + logistic regression · DistilRoBERTa vs BiomedBERT, fine-tuned in two stages)*
4. **Explain** — One sentence in a fixed pattern ("You described …, and Dermatology looks after …") and three questions to think about before the visit, written from the concern text and the chosen doctor only. The stated choice and its confidence always come from the router. The text is rejected if it diagnoses, guesses at a cause, uses numbers, names a medicine, or mentions a different kind of doctor; after one retry the app uses fixed wording. *(Qwen2.5-1.5B-Instruct, used as-is)*

No user text is stored.

---

## How each requirement is met

### Requirement 1 — Functional and useful

**Need:** International students arriving in the US meet a healthcare system where booking a specialist is the patient's job. Specialties are split more finely than many home systems (podiatry vs orthopaedics, dermatology vs allergy, optometry vs ophthalmology). Insurance directories list specialties but don't say which one fits your problem. Booking the wrong one costs a wasted copay, weeks on a waitlist, or a referral loop. Both of us have run into this. The system answers one narrow question, "which door do I knock on?", and never "what do I have?".

**Doing it well** means three things: on real posts it routes far better than always answering "Start with a GP"; it never delays an emergency; and it is fast enough to use.

**Measured by:**
- **Headline:** top-1 and top-3 accuracy and macro-F1 of the fine-tuned routers on our own 150 test posts, with exact intervals, against an "always GP" baseline and against the from-scratch router; also split clear vs ambiguous
- Missed emergencies on cases we wrote ourselves (the costly error, so reported first), then false alarms on those cases and on our labelled posts
- How often the unsure state fires, and top-2 accuracy within it (a hit counts if either option matches the primary or alternate label)
- Label quality: Cohen's κ on 60 double-labelled test posts
- Latency per request

### Requirement 2 — Manual dataset

- **Routing labels, 600 posts:** primary specialty plus an optional alternate, urgency tier, ambiguous flag. Split by post into 400 train / 50 dev / 150 test. Posts that aren't a "which doctor" question are skipped, so the pool is larger than 600.
- **Sampling:** the test posts are a plain random sample of the pool. Most train posts are chosen so that each specialty has enough examples; 100 are random. The 50 dev posts come from those random ones only, so the cutoffs tuned on dev see the same label mix as the test set. `data/manual/pool.ids.csv` records how each post was drawn.
- Public data (Patient Comments) and synthetic data (for example handwritten emergency cases for testing the red-flag rules) are stored apart from the manual labels and don't count toward them.

### Requirement 3 — Model types

All three. The from-scratch and fine-tuned routers are compared in an ablation; the off-the-shelf LLM writes the explanation. Details below.

### Requirement 4 — GUI

Gradio app: paste a concern, get the top-3 specialties with confidence and a rationale. A confident result leads with one specialty; an unsure one presents two options side by side for the user to choose between. The result is drawn as a sign: blue for one answer, amber for two options, red for an emergency. Rules run first, no input is retained, and the examples in the app are made up. It runs from `notebooks/doc_compass_app.ipynb` in Colab. The model card is on Hugging Face; the data card is still to write.

### Also in the brief — GenAI reflection

Keep a running log of GenAI use from day one rather than reconstructing it at the end.

---

## The three model types

| Type | Routing | Explanation |
|---|---|---|
| Trained from scratch | TF-IDF + logistic regression | — |
| Fine-tuned | `distilbert/distilroberta-base` vs `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext`, all weights trained, in two stages | — |
| Off-the-shelf | *Optional:* Qwen as a zero-shot router, for comparison | `Qwen/Qwen2.5-1.5B-Instruct`, used as-is (not trained); its text is checked, with fixed wording as the fallback |

The red-flag rules and the optional scrub are rules, not model types. The encoder comparison keeps the v1 research question: does a biomedical encoder, pretrained on biomedical research papers, lose to a general one on patient-written posts? On the public set the two are tied. It costs one extra run of the same script. BiomedBERT has 12 layers to DistilRoBERTa's 6, so size is a confound; say so, or add a 12-layer general encoder.

### Training in two stages

1. **Stage 1, public data (done).** Train the encoder on the Patient Comments set (6,252 unique comments after removing emoji and duplicates; 938 held out for scoring), remapped to our label set. No labels of ours are needed. Four epochs took 3 minutes for DistilRoBERTa and 5 for BiomedBERT on a laptop.
2. **Stage 2, our data.** Continue training the same model on our 400 gold training posts, so it adapts to our labels and to how real posts are written.
3. **Checks.** Both stages use one fixed label list, so the model's output layer never changes. On dev we compare three versions: gold only, public only, and public then gold. τ is tuned on dev. The test split is read once at the end.

TF-IDF + logistic regression has no second stage: it is trained on gold alone and on gold plus public, and the two are compared.

**Stretch goals:** full redaction (Presidio restricted to relevant entity types plus an age/sex recognizer, a CRF on Nemotron-PII + TAB, PII spans on 100–150 posts for evaluation), 1D-CNN router, `emilyalsentzer/Bio_ClinicalBERT`, all-MiniLM near-duplicate removal.

The ablation compares macro-F1, latency, cost per 1,000 posts and behaviour on rare specialties.

---

## Data sources

Checked on 27 Sep 2026 against the Hugging Face API, dataset files, papers and licence texts.

| Dataset | Size | What it is | Licence | Decision |
|---|---:|---|---|---|
| `stellalisy/MediQ_AskDocs` | 10,366 unique posts (20,000 / 3,210 / 620 rows in `original/`; 1,971 posts appear in more than one of MediQ's splits) | Real r/AskDocs posts 2013–2021, verbatim; chat format (`id, system, messages, context, question`); no subreddit, flair or specialty; some `u/` handles and image links | MIT on the card; Reddit origin | **Post pool for the 600.** Dedupe on text, skip `synthetic/`, ignore MediQ's splits. 1,309 posts carry more than one `id` root, so keep one id per post |
| Patient Comments and Specialist Types (Mendeley Data, DOI 10.17632/2twgjzpn82.2) | 5,906 + 2,535 rows; 6,252 unique comments after our mapping, emoji removal and dedupe | Short first-person comments (median 13 words) in 68 symptom categories, mapped to 29 specialist types by a fixed dictionary | CC BY 4.0 | **Stage-1 training data, kept apart from our manual labels.** The comments are short and alike, so results on it are a sanity check only. Remapped to our label set (`docs/label-set.md`). The label comes from the category, not the comment; 85% of comments contain emoji; 339 of its 2,535 test comments also appear in its train file, so we ignore its split |
| `ildpil/text-anonymization-benchmark` (TAB) | 1,268 ECHR court judgments | Character offsets, direct / quasi / no-mask, several annotators per document | MIT | **Only if full redaction comes back.** Schema, CRF training (train split), benchmark (test split). 1,014 / 127 / 127 documents; test documents have several annotators |
| `nvidia/Nemotron-PII` | 100k train + 100k test rows: 50k documents per split, each in a US and an international version (the card counts documents) | Synthetic documents in 50+ domains including healthcare, 55+ PII labels | CC BY 4.0 | **Only if full redaction comes back.** CRF training, in `data/synthetic`. Mostly structured records; 1,860 healthcare free-text documents in train |
| `bagga005/medredqa` (mirror of CSIRO MedRedQA) | ≈ 40.8k / 5.1k / 5.1k | Real r/AskDocs posts; `occupation` = flair of the answering doctor (e.g. "Physician - Dermatologist") | CC BY-NC-SA 4.0 upstream; download asks you to confirm ethics approval | **Not used (decided 4 Oct), to save time.** Weak labels: the flair says who answered, not where to book, and only ≈ 12.8k of 50,991 rows name a bookable specialty (38% of those dermatology). 707 MediQ posts appear in it word for word: dedupe against our dev and test splits |
| `ai4privacy/pii-masking-300k` | ≈ 30k English train rows | Synthetic forms and emails | Custom: academic, no derivative works without written permission | **Dropped** |
| Specialty subreddits (via API or Arctic Shift) | — | Where posters chose to ask | Reddit terms ban training without permission | **Dropped** |
| iCliniq (scrape or HF copies) | 7.3k (copies) | Patient Q&A | Terms ban scraping; copies have no specialty field | **Dropped** |
| `lavita/ChatDoctor-HealthCareMagic-100k` | 112k | Grammar-corrected patient questions, no specialty field | None on HF; upstream says research only | **Not used** |
| RedHOT | ≈ 22k | Condition subreddits | Text must be re-fetched via the Reddit API; IRB attestation | **Not used** |
| i2b2 / n2c2, PhysioNet de-id | — | Real clinical notes with PHI | Credentialed access + DUA | **Not used** — no real medical PII corpus is openly available |

**Annotation estimate:** ≈ 7 person-hours across both of us for the 600 posts, including a second pass on 60 test posts. No clinician check (needs an expert).

---

## Task plan, 4–8 Oct

### 4 Oct · Unblock labelling, get the app working
- [x] Label set and public-data mapping agreed (`docs/label-set.md`)
- [x] Data prep: load MediQ_AskDocs `original/`, dedupe on post text, strip `u/` handles and links, length-filter, draw a seeded pool
- [x] Labelling tool and the pool of posts to label
- [x] Stage 1: all three routers trained on the public set
- [x] Red-flag rules with a cited source per rule; scrub; fixed-wording explanation
- [x] Qwen2.5-1.5B explanation with its checks and the fallback
- [x] Gradio app running end to end, plus the Colab notebook that launches it with a public link and QR code
- [x] Code and stage-1 routers published to the Hugging Face Hub

### 5 Oct · Presentation
- [ ] Record the demo video from the working app
- [ ] Run the notebook 10–15 minutes before the talk and put that run's QR code on the demo slide
- [ ] Slides say plainly that the router shown has only seen public data

### 5–6 Oct · Label and fine-tune
- [ ] First-pass labels for the train and dev posts
- [ ] Both of us: label the train and dev posts and the 150 test posts; double-label 60
- [ ] Script that computes Cohen's κ on the 60 shared posts, merges them into one label each, and writes the train / dev / test splits
- [ ] Stage 2: DistilRoBERTa and BiomedBERT on our 400 training posts; tune the cutoffs on dev
- [ ] Republish the bundle with the stage-2 routers

### 7 Oct · Evaluate
- [ ] Routing on the 150-post test split: top-1, top-3, macro-F1, exact intervals, clear vs ambiguous, vs "always GP"
- [ ] Ablation: TF-IDF vs the two encoders; gold only vs public only vs public then gold; latency
- [x] Missed emergencies and false alarms on 80 cases we wrote (`data/synthetic/emergency_cases.csv`)
- [ ] False-alarm rate of the emergency check on the labelled posts
- [ ] Cohen's κ on the 60 double-labelled posts; error analysis

### 8 Oct · Ship and write
- [ ] Final app: disclaimer, "Start with a GP" always visible, made-up examples only, no input retained
- [ ] Data card (sources, licences, Reddit terms, labels + ids instead of text); update the model card with stage-2 results
- [ ] Report: need, measurement approach, κ, results, ablation, what we dropped and why, GenAI reflection

---

## Risks and what to do about them

| Risk | Mitigation |
|---|---|
| Annotation runs long | Keep at least 500 labelled posts that one of us has looked at: the 150 test posts plus 350 train and dev posts. Cut the double-labelled set before anything else. |
| The public set's labels are noisy and its style is unlike real posts (short, emoji, slang) | Strip emoji; treat it as stage 1 only; check on dev that public-then-gold beats gold alone, and drop stage 1 if it doesn't. |
| Qwen is unavailable, too slow, or writes something that fails its checks | The app falls back to fixed wording; the rest of the pipeline doesn't depend on Qwen. On 16 test inputs, 15 explanations passed. |
| When the router picks the wrong doctor, Qwen still writes a fluent sentence for it | The fixed sentence pattern puts what the user said next to what that doctor covers, so a mismatch is visible. Fixing the router (stage 2) is the real remedy. |
| The fine-tuned routers are over-confident, so the "unsure" state rarely fires | Tune both cutoffs on dev; if that isn't enough, rescale the confidences on dev before applying them. |
| Rare specialties get very few of the 150 random test posts | Report per-class counts and exact intervals; lead with overall and macro numbers; merge labels if a class is nearly empty. |
| "Start with a GP" dominates the labels | Report macro-F1 and an "always GP" baseline so a GP-only model can't look good. |
| Red-flag keywords may fire on non-emergency posts ("chest pain" appears in 281 of 10,366 MediQ posts; how many of those are real emergencies is unchecked) | Report the false-alarm rate as well as recall. Plain negation is handled; past events and other people's symptoms still fire, and we add rules for those only if false alarms are high. |
| If full redaction comes back: it strips routing signal (on 200 sampled posts, Presidio with `en_core_web_sm` tagged durations and drug names as PII and caught 3 of 44 age/sex mentions) | Restrict it to the entity types we need, add an age/sex recognizer, and report router accuracy on raw vs redacted text. |
| 12.5% of posts exceed the encoders' 512-token limit | Truncate the head (title plus opening), or head plus tail; tune on dev. |
| Colab gives no GPU | Kaggle notebooks; DistilRoBERTa on a few hundred posts also trains on a laptop in minutes. |
| Someone treats the output as medical advice | Rules-first red flags, top-3 instead of a verdict, visible disclaimer, "Start with a GP" always on screen. |
| Real posts are personal | Strip handles, never upload post text, release labels + ids only, paraphrase any post quoted in the report, made-up examples in the app. |

---

## Every healthcare idea we considered

| Idea | What it did | Outcome | Why |
|---|---|---|---|
| **Specialist router** | Health concern → which specialty to book | **Selected** | Navigation, not diagnosis; measurable against how people route themselves |
| **PII redaction** | Strip direct and quasi identifiers before routing | **Deferred** (29 Sep) | Routing is the focus; at most a simple rule-based scrub, full redaction if time allows |
| Doctor–patient transcription | Transcribe appointments | Ruled out | Collecting or synthesising speech is too costly; even text dialogues are expensive per sample |
| Medication label reader | Photo of a medicine box → dose, ingredients, duplicate-ingredient warning | Ruled out | Advice about medication; no public set of English medicine-box photos |
| Food label allergen checker | Photo of a label → check against personal dietary constraints | Ruled out | A missed allergen is a safety failure — too much accountability |
| Drug review miner | Aspects extracted from 215,063 Drugs.com reviews | Ruled out | Implies which drug will work for you |
| Acuity triage | Symptoms → ER, urgent care or wait | Ruled out | Samples would be self-written vignettes; public triage advice is a liability |
| Plain-language rewriter | Medical text → plain text | Ruled out | Writing 1,000 rewrite pairs is about 33 hours; thin public data |
| Medical bill decoder | Explain bills and benefit statements | Ruled out | No way to collect 500 real bills |
| Skin photo classifier, mental-health journaling | — | Ruled out | Clinical risk or a sensitive population on a public URL |
| Health claim checker | Claim → supported or not, with evidence (PUBHEALTH 12,258; SciFact) | Parked | Strong benchmarks, but not a weekly pain point for the team |
| Insurance coverage Q&A | "Is this covered?" over policy documents | Parked | Public data is generic insurance (27,987 rows); weak three-model story |
| Clinical trial matcher | Match eligibility criteria (chia, 2,000) | Parked | Real data, but not a pain point for the team |

**Non-healthcare fallback:** the job posting decoder has the strongest verified data of anything reviewed (EMSCAD 17,880 labelled postings; 449,028 postings with salaries) and no liability. Worth keeping in reserve if the router stalls.

---

*v2 facts were checked on 27 Sep 2026 against the Hugging Face API and dataset files, redditinc.com policy pages, icliniq.com terms, Hugging Face Spaces docs and PyPI. Unverified: details of Reddit's Responsible Builder Policy (help page returned 403; secondary sources) and the meaning of the MediQ `id` prefix. MediQ counts, Nemotron-PII sizes, TAB and MedRedQA were rechecked on 29 Sep against the downloaded files, and the Patient Comments set on 4 Oct.*
