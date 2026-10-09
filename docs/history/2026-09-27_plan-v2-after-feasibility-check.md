# Doc Compass

*Which doctor do I book?* · repo: `project1/doc-compass/`

**Project 1 · plan of record · v2, revised after the feasibility check on 27 Sep 2026**

A privacy-preserving specialist router. Describe a health concern in plain language, have the identifying details stripped out, and get told which kind of doctor to book. Routing, not diagnosis — which door to knock on, never what you have.

| Field | Value |
|---|---|
| Team | Akshara (`akshara-ns`) and Sohum (`ssg1`) |
| Build window | One working week (course week 6), presentations and final deliverables in week 7 |
| Deploy target | Gradio app on a **ZeroGPU** Hugging Face Space (free CPU Spaces now need PRO) |
| Model types | All three: from scratch, fine-tuned, off-the-shelf |
| Manual data | 1,000 labelled posts (routing layer), 300 of them with PII spans, plus a human-baseline form |
| Annotation effort | ≈ 25 person-hours |
| Completion estimate | ≈ 65% with this scope (the v1 scope was ≈ 25% in one week) |

Check-in figure: `project1/checkin/checkin_figure.png` (source: `checkin/build_figure.py`).

---

## What changed in v2, and why

| v1 plan | Problem found | v2 plan |
|---|---|---|
| Train routers on posts scraped from specialty subreddits (distant supervision) | Reddit's Data API Terms §3.2 forbid "using User Content to train a machine learning or AI model without the express permission of rightsholders"; the Developer Terms §4.2 and User Agreement ban scraping. New API apps need manual approval since Nov 2025 (weeks). Six of the planned subreddits are for professionals only, r/ENT is an entheogen community, r/Urology doesn't exist, and the patient-facing replacements are condition subreddits whose posts name the answer. | Train on our own 600-post training split. |
| Headline metric: self-routing baseline (subreddit chosen vs gold label) | Every MediQ_AskDocs post comes from one general forum, so there is nothing to compare. It also depended on the subreddit data above. | **Human baseline:** 10–15 international students each pick a doctor for 20 redacted test posts. The model has to beat them. |
| Gold set fully held out; nothing trained on it | Without distant supervision there is no other routing training data. | Split the 1,000 by post: 600 train, 100 dev, 300 test. The test split is never trained on or tuned against. |
| Scrape iCliniq specialty sections as a fallback | iCliniq's Terms of Use forbid scraping "for commercial or any other purpose whatsoever"; HF copies have no specialty field. | Dropped. |
| ai4privacy for PII augmentation | Custom licence: redistribution and derivative works need written permission. A public model trained on it is a derivative. | Use `nvidia/Nemotron-PII` (CC BY 4.0, includes healthcare documents). |
| "55,071 MediQ posts" | Rows repeat each post once per doctor question, and part of the repo is synthetic. | ≈ 13.5k unique real posts. Deduplicate on post text and skip the `synthetic/` folder. |
| Free CPU Space | Creating a Gradio Space on free CPU now returns 402 (we hit this in HW3). | ZeroGPU Space: free for accounts older than 30 days, up to 2 Spaces. Both accounts qualify (akshara-ns Jan 2026, ssg1 Nov 2024). |
| LLM via an external API (Gemini used in HW3) | Redacted text would leave HF; Gemini's free tier may use prompts to improve Google's products. | `Qwen/Qwen2.5-1.5B-Instruct` on the Space's ZeroGPU, with a template fallback. No text leaves the Space. |
| Redact, then red-flag check | Our notes disagreed on the order. | Red-flag rules run first on the raw text, inside the Space. Nothing leaves the Space either way, and a missed redaction cannot hide an emergency. |
| 1,000 posts × two full layers, 200 double-labelled, clinician on 100 | ≈ 40 person-hours before any modelling; no clinician recruited. | Routing labels on 1,000, PII spans on 300, 150 double-labelled. Clinician check is optional. |
| Ten or more models | Too many for one week. | Core set below; everything else is a stretch goal. |

---

## Open questions (check-in meeting)

In priority order for a 10-minute meeting. The Q numbers match the badges on the figure.

**Blocking — ask first**

1. **(Q1) Manual data.** Is the floor 500 or 1,000 samples (the brief says both)? Does labelling existing public posts from `stellalisy/MediQ_AskDocs` count as "manually collected/curated", or do samples need to be authored by us?
2. **(Q2) Reddit-derived data.** Reddit's current terms forbid training models on its content without permission. We won't scrape or use the API, but MediQ_AskDocs (and MedRedQA) are Reddit posts redistributed by researchers. Is training and evaluating on them acceptable for a class project if we never republish the text?
3. **(Q4) Hosting.** Free CPU Spaces now require PRO. Is a free ZeroGPU Space acceptable for the "public, working GUI on Hugging Face Spaces" requirement, or should we submit a Colab link as in HW3?
4. **(Q6) Training on the manual set.** Can we train the router on 600 of our 1,000 labelled posts, as long as the 300-post test split is never trained or tuned on?

**Important — ask if time allows**

5. **(Q3) MedRedQA.** Its download page asks users to confirm they have ethics approval from their institution. Does a course project cover that, or should we leave it out?
6. **(Q5) Human baseline.** Is a Google Form where 10–15 international students pick a specialty for 20 redacted posts an acceptable way to collect data? What consent wording do you expect? Should we show the redacted real posts or paraphrases?
7. **(Q7) Model types.** Does TF-IDF + logistic regression (or a CRF) count as "trained from scratch", or does it need to be a neural network?
8. **Scope.** Is redaction plus routing too much for the time left? Would you rather we went deep on one of them?

**Quick yes/no if there is a minute left**

9. Is LLM-assisted annotation (a model suggests labels, we correct them) allowed if disclosed? We currently plan not to use it.
10. Is the clinician check expected, or a nice-to-have?
11. Should the gold labels be published on HF as a labels-only dataset (labels + MediQ ids, no text)?
12. Week 7 deliverables: report format and length, presentation length, and whether the GenAI log has a template.

---

## Project description

> We're both interested in healthcare navigation and privacy-preserving NLP, and think a system that could take a plain-language description of a health concern, strip the identifying details out of it, and then suggest which specialty to actually book would be pretty great. It's a routing tool rather than a diagnostic one — which door to knock on, not what you have — with "start with a GP" as a first-class answer and a hard escape hatch for emergency symptoms. A user will interact with it through a Gradio GUI hosted on Hugging Face Spaces: paste a concern, see exactly what got redacted before anything is sent onward, and get back a ranked top-3 of specialties with confidence scores and a short rationale. We'll use 1,000 manually labelled patient posts from MediQ_AskDocs (specialty labels on all, PII spans on 300), a form in which international students route the same posts themselves, the Text Anonymization Benchmark and synthetic Nemotron-PII for redaction, and all three model types — a TF-IDF classifier and a CRF trained from scratch, a fine-tuned DistilRoBERTa, and off-the-shelf Presidio plus a small instruct LLM — built with Hugging Face transformers, scikit-learn, and Gradio. We think there's about a 65% chance we'll complete this before the deadline.

---

## How a request moves through the system

1. **Red-flag check** — Written rules scan the raw text inside the Space. Emergency symptoms short-circuit straight to "Seek emergency care now" and nothing else runs. *(Rules, deliberately not learned)*
2. **Redact** — Names, places, dates, employers and quasi-identifiers like "17F with PCOS" are removed, and the user sees the highlighted spans. *(Presidio · CRF · DistilBERT as a stretch goal)*
3. **Route** — Top-3 bookable specialties with confidence. If the top probability is below τ, the answer is "Start with a GP". *(TF-IDF + logistic regression · fine-tuned DistilRoBERTa vs BiomedBERT)*
4. **Explain** — A plain rationale and a few questions worth bringing to the appointment, generated from redacted text only. *(Qwen2.5-1.5B-Instruct on ZeroGPU, template fallback)*

No user text is stored, and no text leaves the Space.

---

## How each requirement is met

### Requirement 1 — Functional and useful

**Need:** International students arriving in the US meet a healthcare system where booking a specialist is the patient's job. Specialties are split more finely than many home systems (podiatry vs orthopaedics, dermatology vs allergy, optometry vs ophthalmology). Insurance directories list specialties but don't say which one fits your problem. Booking the wrong one costs a wasted copay, weeks on a waitlist, or a referral loop. Both of us have run into this. The system answers one narrow question, "which door do I knock on?", and never "what do I have?".

**Doing it well** means four things: it routes correctly more often than our target users do on their own; it never delays an emergency; it doesn't expose identifying details; and it is fast enough to use.

**Measured by:**
- **Headline:** top-1 and top-3 accuracy of the model vs the human baseline (international students' picks) on the same test posts
- Top-1 / top-3 accuracy and macro-F1 on the 300-post test split, split clear vs ambiguous, compared with an "always GP" baseline
- Emergency recall reported on its own line, targeting close to 100%
- Redaction span recall on our 300 PII-labelled posts and on the TAB test split
- Label quality: Cohen's κ on 150 double-labelled posts; clinician agreement if we find one
- Latency per request on the Space

### Requirement 2 — Manual dataset

- **Routing layer, 1,000 posts:** primary specialty plus acceptable alternates, urgency tier, ambiguous flag. Split by post into 600 train / 100 dev / 300 test.
- **Privacy layer, 300 of those posts:** PII spans using TAB's direct / quasi schema. Used only for evaluation.
- **Human baseline:** 10–15 international students × 20 redacted test posts, collected with a consent notice, following the class data exercise.
- Synthetic PII corpora live in `data/synthetic` and count for nothing.

### Requirement 3 — Model types

All three, each on the task it suits, compared in an ablation. Details below.

### Requirement 4 — GUI on HF Spaces

Gradio app on a ZeroGPU Space: paste a concern, see what was redacted (`gr.HighlightedText`), get the top-3 specialties with confidence and a rationale. Rules run first, no text leaves the Space, no input is retained, examples in the Space are made up, and it ships with a model card and a data card.

### Also in the brief — GenAI reflection

Keep a running log of GenAI use from day one rather than reconstructing it at the end.

---

## The three model types

| Type | Redaction | Routing | Explanation |
|---|---|---|---|
| Trained from scratch | CRF (sklearn-crfsuite) on Nemotron-PII + TAB train | TF-IDF + logistic regression | — |
| Fine-tuned | *Stretch:* DistilBERT token classification | `distilbert/distilroberta-base` vs `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext` | — |
| Off-the-shelf | Presidio with `en_core_web_sm` | — | `Qwen/Qwen2.5-1.5B-Instruct` |

Regex rules are the **baseline floor** for redaction, and the red-flag rules are not a model type. The encoder comparison keeps the v1 research question: do biomedical encoders, pretrained on clinician-written text, lose to general ones on patient-written posts? It costs one extra run of the same script.

**Stretch goals:** 1D-CNN router, `emilyalsentzer/Bio_ClinicalBERT`, DistilBERT redaction, all-MiniLM near-duplicate removal, MedRedQA as extra training data.

The ablation compares macro-F1, latency, cost per 1,000 posts and behaviour on rare specialties.

---

## Data sources

Checked on 27 Sep 2026 against the Hugging Face API, dataset files, papers and licence texts.

| Dataset | Size | What it is | Licence | Decision |
|---|---:|---|---|---|
| `stellalisy/MediQ_AskDocs` | ≈ 13.5k unique posts (20k / 3.2k / 620 rows in `original/`) | Real r/AskDocs posts 2013–2021, verbatim; chat format (`id, system, messages, context, question`); no subreddit, flair or specialty; some `u/` handles and image links | MIT on the card; Reddit origin | **Post pool for the 1,000.** Dedupe on text, skip `synthetic/`, key on the MediQ `id` |
| `ildpil/text-anonymization-benchmark` (TAB) | 1,268 ECHR court judgments | Character offsets, direct / quasi / no-mask, several annotators per document | MIT | **Redaction schema, CRF training (train split), benchmark (test split).** Pick one annotator or merge |
| `nvidia/Nemotron-PII` | 100k+ (card and viewer disagree) | Synthetic documents in 50+ domains including healthcare, 55+ PII labels | CC BY 4.0 | **CRF training / augmentation,** in `data/synthetic` |
| `bagga005/medredqa` (mirror of CSIRO MedRedQA) | ≈ 40.8k / 5.1k / 5.1k | Real r/AskDocs posts; `occupation` = flair of the answering doctor (e.g. "Physician - Dermatologist") | CC BY-NC-SA 4.0 upstream; download asks you to confirm ethics approval | **Optional extra training data (Q3).** Overlaps MediQ: dedupe against our test split. Heavy dermatology skew from one prolific answerer; split by responder |
| `ai4privacy/pii-masking-300k` | ≈ 30k English train rows | Synthetic forms and emails | Custom: academic, no derivative works without written permission | **Dropped** |
| Specialty subreddits (via API or Arctic Shift) | — | Where posters chose to ask | Reddit terms ban training without permission | **Dropped** |
| iCliniq (scrape or HF copies) | 7.3k (copies) | Patient Q&A | Terms ban scraping; copies have no specialty field | **Dropped** |
| `lavita/ChatDoctor-HealthCareMagic-100k` | 112k | Grammar-corrected patient questions, no specialty field | None on HF; upstream says research only | **Not used** |
| RedHOT | ≈ 22k | Condition subreddits | Text must be re-fetched via the Reddit API; IRB attestation | **Not used** |
| i2b2 / n2c2, PhysioNet de-id | — | Real clinical notes with PHI | Credentialed access + DUA | **Not used** — no real medical PII corpus is openly available |

**Annotation estimate:** routing labels ≈ 75 s per post × 1,000 ≈ 21 h, spread across both of us. PII spans on 300 posts ≈ 2.5 h. Double-labelling 150 posts ≈ 3 h. Pilot ≈ 1 h. Total ≈ 25 person-hours, about 12–13 hours each. If the floor is confirmed at 500, halve it.

---

## One-week task plan

### Day 1 · Decide and set up
- [ ] Settle the open questions above and record the decisions in this doc
- [ ] Create the ZeroGPU Space on whichever account has a free slot; deploy a hello-world Gradio app to confirm it works
- [ ] Fix the label set: 8–10 bookable specialties plus "Start with a GP" and "Emergency"
- [ ] Write the annotation guideline from public rubrics (NHS "which service" guidance, specialty scope-of-practice pages) with worked ambiguous examples
- [ ] Load MediQ_AskDocs `original/`, dedupe on post text, strip `u/` handles and links, length-filter, sample 1,000 with a fixed seed
- [ ] Set up the annotation sheet (routing) and a span tool for PII (Label Studio or doccano locally)
- [ ] Set up the repo with `data/manual`, `data/public`, `data/synthetic`; start the GenAI log
- [ ] Pilot 50 posts together, revise the guideline, discard the pilot labels

### Days 2–4 · Label and build in parallel
- [ ] **Annotator (mostly one of us):** 1,000 routing labels; PII spans on 300; the other person double-labels 150 → Cohen's κ
- [ ] **Builder (the other):** red-flag rules with a cited source per rule; Presidio with `en_core_web_sm`; regex floor; Space skeleton with `gr.HighlightedText`
- [ ] Builder: CRF on Nemotron-PII + TAB train; TF-IDF + logistic regression as soon as the first 600 labels exist
- [ ] Day 4: send the human-baseline form (consent notice first; redacted posts from the test split)

### Day 5 · Fine-tune
- [ ] DistilRoBERTa and BiomedBERT on the 600-post train split (Colab, Kaggle as backup); tune τ and settings on the 100-post dev split only
- [ ] Qwen2.5-1.5B rationale inside `@spaces.GPU(duration=30)`, with a template fallback

### Day 6 · Evaluate
- [ ] Routing on the 300-post test split: top-1, top-3, macro-F1, clear vs ambiguous, vs "always GP", vs the human baseline
- [ ] Emergency recall on its own line
- [ ] Redaction recall (then precision and F1) on our 300 PII posts and on the TAB test split
- [ ] Ablation table: macro-F1, latency, cost per 1,000 posts, rare specialties

### Day 7 · Ship and write
- [ ] Final Space: disclaimer, "Start with a GP" always visible, made-up examples only, no input retained
- [ ] Model card (English only, self-selected online posters, not clinically validated) and data card (sources, licences, Reddit terms, labels + ids instead of text)
- [ ] Report: need, measurement approach, κ, results, ablation, what we dropped and why, GenAI reflection

---

## Risks and what to do about them

| Risk | Mitigation |
|---|---|
| Annotating MediQ posts doesn't count as manual data | Switch the manual set to vignettes we write ourselves, based on the rubric categories, and keep MediQ as a public evaluation set. Decide on day 1. |
| Reddit-derived data can't be used at all | Same fallback: self-written vignettes for training and testing, with the human-baseline form on those vignettes. |
| Annotation runs long | Label routing first; cut PII spans to 200; drop to 500 posts if the floor allows. |
| ZeroGPU Space doesn't work or the quota is too small | Template-only rationale on CPU logic; fall back to a Colab link as in HW3. |
| Rare specialties get fewer than 20 test posts | Cap the label set at 8–10, merge rare ones, report per-class counts. |
| "Start with a GP" dominates the labels | Report macro-F1 and an "always GP" baseline so a GP-only model can't look good. |
| Redaction models trained on synthetic and legal text transfer badly to Reddit prose | That's a finding; report it. Presidio is the default in the Space if the CRF loses. |
| Colab gives no GPU | Kaggle notebooks; DistilRoBERTa on 600 posts also trains on CPU in minutes. |
| Someone treats the output as medical advice | Rules-first red flags, top-3 instead of a verdict, visible disclaimer, "Start with a GP" always on screen. |
| Real posts are personal | Strip handles, never upload post text, release labels + ids only, paraphrase any post quoted in the report, made-up examples in the Space. |
| Presidio pre-highlighting biases the PII labels | Don't pre-highlight; if we must, say so and don't report Presidio's recall as unbiased. |

---

## Every healthcare idea we considered

| Idea | What it did | Outcome | Why |
|---|---|---|---|
| **Specialist router** | Health concern → which specialty to book | **Selected** | Navigation, not diagnosis; measurable against how people route themselves |
| **PII redaction** | Strip direct and quasi identifiers before routing | **Added feature** | Labelling needs no clinical expertise; real benchmark in TAB |
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

*v2 facts were checked on 27 Sep 2026 against the Hugging Face API and dataset files, redditinc.com policy pages, icliniq.com terms, Hugging Face Spaces docs and PyPI. Unverified: details of Reddit's Responsible Builder Policy (help page returned 403; secondary sources), the meaning of the MediQ `id` prefix, and exact Nemotron-PII split sizes.*
