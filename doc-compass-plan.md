# Which Doctor Do I Book?

**Project 1 · plan of record · v2, revised after the feasibility check on 27 Sep 2026 · updated 4 Oct 2026**

A specialist router. Describe a health concern in plain language and get told which kind of doctor to book. Routing, not diagnosis — which door to knock on, never what you have.

| Field | Value |
|---|---|
| Team | Akshara (`akshara-ns`) and Sohum (`ssg1`) |
| Deadlines | Presentation 5 Oct 2026; code and report 8 Oct 2026 |
| GUI | Gradio app. Where it's hosted is decided later (Gradio Spaces on Hugging Face now need a paid plan) |
| Model types | All three: from scratch, fine-tuned, off-the-shelf (the brief asks for at least two) |
| Focus | Routing. Redaction is out of scope for now: we assume users type relevant, non-identifying text. A simple rule-based scrub may be added for completeness, and full redaction later if time allows |
| Manual data | 600 labelled posts (400 train / 50 dev / 150 test), plus a human-baseline form (placeholder) |
| Public data | Patient Comments and Specialist Types, remapped to our labels, for stage-1 training only |
| Annotation effort | ≈ 7 person-hours across both of us; 60 of the 150 test posts are labelled by both of us for Cohen's κ |
| Completion estimate | ≈ 65% with this scope (the v1 scope was ≈ 25% in one week) |

Current figure: `docs/checkin/checkin_figure_v3.png` (4 Oct). The 27 Sep check-in figure, `docs/checkin/checkin_figure.png`, is kept as it was. Label set and public-data mapping, for approval: `docs/label-set.md`.

---

## What's new on 4 Oct

For Akshara: the changes since the 27 Sep check-in, newest decisions first.

- **Two-stage training.** Stage 1 trains the encoder on a public dataset of short patient comments; stage 2 continues on our own labelled posts. Stage 1 needs none of our labels, so the app can work end to end before labelling is finished.
- **A public dataset close to our task exists:** Patient Comments and Specialist Types (Mendeley, CC BY 4.0). Its 68 symptom categories are remapped to our labels. It is training data only and is never the test set.
- **600 posts, not 1,000.** 400 train / 50 dev / 150 test. The brief's text asks for at least 500.
- **Labelling.** Each post gets a primary label, an optional alternate, an urgency tier and an ambiguous tick. The 150 test posts are a plain random sample, and 60 of them are labelled by both of us for Cohen's κ.
- **Label set:** eleven specialties plus "Start with a GP". "Emergency" and "Skip" exist only while labelling. See `docs/label-set.md`.
- **Skips.** About 1 in 6 posts in a 60-post pilot was not a "which doctor" question, so the pool is larger than 600 and labelling has a Skip option.
- **MedRedQA is not used.** Its labels say who answered, not where to book.
- **Encoders are fully fine-tuned** with the `transformers` Trainer, keeping the checkpoint that scores best on dev. τ is tuned on dev; the test split is read once.
- **Settled:** we label existing public posts from MediQ_AskDocs; TF-IDF + logistic regression is our from-scratch model; there is no expert annotation; the demo runs from a Colab link.
- **Earlier (29 Sep – 3 Oct):** redaction on hold, hosting deferred, clinician check and PII spans dropped, Qwen2.5-1.5B kept for the explanation.

---

## What changed in v2, and why

| v1 plan | Problem found | v2 plan |
|---|---|---|
| Train routers on posts scraped from specialty subreddits (distant supervision) | Reddit's Data API Terms §3.2 forbid "using User Content to train a machine learning or AI model without the express permission of rightsholders"; the Developer Terms §4.2 and User Agreement ban scraping. New API apps need manual approval since Nov 2025 (weeks). Six of the planned subreddits are for professionals only, r/ENT is an entheogen community, r/Urology doesn't exist, and the patient-facing replacements are condition subreddits whose posts name the answer. | Stage 1 on the public Patient Comments set, remapped to our labels; stage 2 on our own gold training split. MedRedQA is not used: its labels are weak and it would cost time we don't have. |
| Headline metric: self-routing baseline (subreddit chosen vs gold label) | Every MediQ_AskDocs post comes from one general forum, so there is nothing to compare. It also depended on the subreddit data above. | **Human baseline:** 10–15 international students each pick a doctor for 20 test posts. The model has to beat them. |
| Gold set fully held out; nothing trained on it | Without distant supervision there is no other routing training data. | Split the 600 by post: 400 train, 50 dev, 150 test. The test split is never trained on or tuned against. |
| Scrape iCliniq specialty sections as a fallback | iCliniq's Terms of Use forbid scraping "for commercial or any other purpose whatsoever"; HF copies have no specialty field. | Dropped. |
| ai4privacy for PII augmentation | Custom licence: redistribution and derivative works need written permission. A public model trained on it is a derivative. | Use `nvidia/Nemotron-PII` (CC BY 4.0) if full redaction comes back later. |
| "55,071 MediQ posts" | Rows repeat each post once per doctor question, and part of the repo is synthetic. | 10,366 unique real posts (checked 29 Sep). Deduplicate on post text and skip the `synthetic/` folder. |
| Free CPU Space | Gradio Spaces on Hugging Face now need a paid plan. | Hosting is decided later. |
| LLM via an external API | Text would leave our app and go to a third party. | `Qwen/Qwen2.5-1.5B-Instruct`, run locally and used as-is (not trained), with a template fallback. It sees only the concern text and the router's output. |
| Redact, then red-flag check | Our notes disagreed on the order. | Red-flag rules run first on the raw text, before anything else. |
| Redaction as a full second task (Presidio, CRF, PII spans on 300 posts, TAB benchmark) | Splits a one-week build across two problems; on real posts Presidio also tagged durations and drug names, which would strip routing signal. | Out of scope for now. Routing is the focus; at most a simple rule-based scrub. Full redaction returns only if time allows. |
| 1,000 posts × two full layers, 200 double-labelled, clinician on 100 | ≈ 40 person-hours before any modelling; no clinician recruited. | Routing labels on 600, 60 double-labelled, no PII spans. No clinician check: we have no expert to do one. |
| Ten or more models | Too many for one week. | Core set below; everything else is a stretch goal. |

---

## Decisions

- **Manual data.** We label existing public posts from MediQ_AskDocs: 600 of them, at least the 500 the brief asks for.
- **Training and testing.** The labelled posts are split by post into train / dev / test. Nothing is trained or tuned on the test split.
- **Hosting.** Gradio Spaces on Hugging Face now need a paid plan, so the demo runs from a Colab notebook. Other hosting is decided later.
- **Model types.** TF-IDF + logistic regression is the trained-from-scratch model.
- **Annotation.** No clinician check and no PII spans.
- **MedRedQA.** Not used.

**Decide later**

- **Human baseline.** A Google Form where 10–15 international students pick a specialty for 20 posts. Consent wording, and whether to show real posts or paraphrases, are still to be settled.
- Publishing the gold labels on HF as a labels-only dataset (labels + MediQ ids, no text): not required.
- Report format and length, and whether the GenAI log has a template.

---

## Project description

> We're both interested in healthcare navigation, and think a system that could take a plain-language description of a health concern and suggest which specialty to actually book would be pretty great. It's a routing tool rather than a diagnostic one — which door to knock on, not what you have — with "start with a GP" as a first-class answer and a hard escape hatch for emergency symptoms. A user will interact with it through a Gradio GUI: paste a concern and get back a ranked top-3 of specialties with confidence scores and a short rationale. We'll use 600 manually labelled patient posts from MediQ_AskDocs, a form in which international students route the same posts themselves, and all three model types — a TF-IDF classifier trained from scratch, a fine-tuned DistilRoBERTa, and an off-the-shelf instruct LLM — built with Hugging Face transformers, scikit-learn, and Gradio. We think there's about a 65% chance we'll complete this before the deadline.

---

## How a request moves through the system

1. **Red-flag check** — Written rules scan the raw text first. Emergency symptoms short-circuit straight to "Seek emergency care now" and nothing else runs. *(Rules, deliberately not learned)*
2. **Scrub (optional)** — Simple rules remove obvious identifiers (`u/` handles, emails, phone numbers, links) and show what was removed. We otherwise assume the input is relevant and non-identifying. *(Rules; full redaction is a later extension)*
3. **Route** — Top-3 bookable specialties with confidence. When the router is unsure (the top probability is below τ, or the top two are close), the app doesn't give one answer: it shows the top two as alternatives, says what separates them, and lets the user decide, with "Start with a GP" as the fallback. Both cutoffs are tuned on dev. *(TF-IDF + logistic regression · DistilRoBERTa vs BiomedBERT, fine-tuned in two stages)*
4. **Explain** — A plain rationale and a few questions worth bringing to the appointment, generated from the concern text and the router's output only. *(Qwen2.5-1.5B-Instruct, used as-is; template fallback)*

No user text is stored.

---

## How each requirement is met

### Requirement 1 — Functional and useful

**Need:** International students arriving in the US meet a healthcare system where booking a specialist is the patient's job. Specialties are split more finely than many home systems (podiatry vs orthopaedics, dermatology vs allergy, optometry vs ophthalmology). Insurance directories list specialties but don't say which one fits your problem. Booking the wrong one costs a wasted copay, weeks on a waitlist, or a referral loop. Both of us have run into this. The system answers one narrow question, "which door do I knock on?", and never "what do I have?".

**Doing it well** means three things: it routes correctly more often than our target users do on their own; it never delays an emergency; and it is fast enough to use.

**Measured by:**
- **Headline:** top-1 and top-3 accuracy of the model vs the human baseline (international students' picks) on the same test posts
- Top-1 / top-3 accuracy and macro-F1 on the 150-post test split, with exact intervals, split clear vs ambiguous, compared with an "always GP" baseline
- Emergency recall reported on its own line, targeting close to 100%
- How often the unsure state fires, and top-2 accuracy within it (a hit counts if either option matches the primary or alternate label)
- Label quality: Cohen's κ on 60 double-labelled test posts
- Latency per request

### Requirement 2 — Manual dataset

- **Routing labels, 600 posts:** primary specialty plus an optional alternate, urgency tier, ambiguous flag. Split by post into 400 train / 50 dev / 150 test. Posts that aren't a "which doctor" question are skipped, so the pool is larger than 600.
- **Sampling:** the test posts are a plain random sample of the pool; the train and dev posts are chosen so that each specialty has enough examples.
- **Human baseline:** 10–15 international students × 20 test posts, collected with a consent notice, following the class data exercise.
- Public data (Patient Comments) and synthetic data (for example handwritten emergency cases for testing the red-flag rules) are stored apart from the manual labels and don't count toward them.

### Requirement 3 — Model types

All three. The from-scratch and fine-tuned routers are compared in an ablation; the off-the-shelf LLM writes the explanation. Details below.

### Requirement 4 — GUI

Gradio app: paste a concern, get the top-3 specialties with confidence and a rationale. A confident result leads with one specialty; an unsure one presents two options side by side for the user to choose between. Rules run first, no input is retained, examples in the app are made up, and it ships with a model card and a data card. Hosting is decided later.

### Also in the brief — GenAI reflection

Keep a running log of GenAI use from day one rather than reconstructing it at the end.

---

## The three model types

| Type | Routing | Explanation |
|---|---|---|
| Trained from scratch | TF-IDF + logistic regression | — |
| Fine-tuned | `distilbert/distilroberta-base` vs `microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext`, all weights trained, in two stages | — |
| Off-the-shelf | *Optional:* Qwen as a zero-shot router, for comparison | `Qwen/Qwen2.5-1.5B-Instruct`, used as-is (not trained) |

The red-flag rules and the optional scrub are rules, not model types. The encoder comparison keeps the v1 research question: do biomedical encoders, pretrained on clinician-written text, lose to general ones on patient-written posts? It costs one extra run of the same script. BiomedBERT has 12 layers to DistilRoBERTa's 6, so size is a confound; say so, or add a 12-layer general encoder.

### Training in two stages

1. **Stage 1, public data.** Train the encoder on the Patient Comments set (6,252 unique comments after removing emoji and duplicates), remapped to our label set. No labels of ours are needed.
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
| Patient Comments and Specialist Types (Mendeley Data, DOI 10.17632/2twgjzpn82.2) | 5,906 + 2,535 rows; 6,252 unique comments after our mapping, emoji removal and dedupe | Short first-person comments (median 13 words) in 68 symptom categories, mapped to 29 specialist types by a fixed dictionary | CC BY 4.0 | **Stage-1 training data, kept apart from our manual labels.** Remapped to our label set (`docs/label-set.md`). The label comes from the category, not the comment; 85% of comments contain emoji; 339 of its 2,535 test comments also appear in its train file, so we ignore its split |
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
- [ ] Approve the label set and the public-data mapping (`docs/label-set.md`)
- [ ] Data prep: load MediQ_AskDocs `original/`, dedupe on post text, strip `u/` handles and links, length-filter, draw a seeded pool
- [ ] Labelling tool and the pool of posts to label
- [ ] Stage 1: TF-IDF router and encoder trained on the public set
- [ ] Red-flag rules with a cited source per rule; optional scrub; template explanation
- [ ] Gradio app running end to end, plus the notebook that launches it with a public link

### 5 Oct · Presentation
- [ ] Demo video from the working app; QR code to the Colab notebook
- [ ] Slides say plainly that the router shown is stage 1 (public data only) and that results on our own test posts follow on 8 Oct

### 5–6 Oct · Label and fine-tune
- [ ] Both of us: label the 450 train and dev posts and the 150 test posts; double-label 60
- [ ] Stage 2: DistilRoBERTa and BiomedBERT on our 400 training posts; tune τ on dev
- [ ] Qwen2.5-1.5B explanation with its checks and the template fallback
- [ ] Push the models and code bundle to the Hugging Face Hub

### 7 Oct · Evaluate
- [ ] Routing on the 150-post test split: top-1, top-3, macro-F1, exact intervals, clear vs ambiguous, vs "always GP"
- [ ] Ablation: TF-IDF vs the two encoders; gold only vs public only vs public then gold; latency
- [ ] Emergency recall on handwritten cases, plus the false-alarm rate on the labelled posts
- [ ] Cohen's κ on the 60 double-labelled posts; error analysis
- [ ] Human-baseline form, if there is time (placeholder)

### 8 Oct · Ship and write
- [ ] Final app: disclaimer, "Start with a GP" always visible, made-up examples only, no input retained
- [ ] Model card (English only, self-selected online posters, not clinically validated) and data card (sources, licences, Reddit terms, labels + ids instead of text)
- [ ] Report: need, measurement approach, κ, results, ablation, what we dropped and why, GenAI reflection

---

## Risks and what to do about them

| Risk | Mitigation |
|---|---|
| Annotation runs long | The floor is 500 posts (the brief's text). Cut the train posts first, never the hand-labelled test posts. |
| The public set's labels are noisy and its style is unlike real posts (short, emoji, slang) | Strip emoji; treat it as stage 1 only; check on dev that public-then-gold beats gold alone, and drop stage 1 if it doesn't. |
| The LLM we pick is unavailable or too slow | Template-only rationale; the rest of the pipeline doesn't depend on the LLM. |
| Rare specialties get very few of the 150 random test posts | Report per-class counts and exact intervals; lead with overall and macro numbers; merge labels if a class is nearly empty. |
| "Start with a GP" dominates the labels | Report macro-F1 and an "always GP" baseline so a GP-only model can't look good. |
| Red-flag keywords may fire on non-emergency posts ("chest pain" appears in 281 of 10,366 MediQ posts; how many of those are real emergencies is unchecked) | Report the false-alarm rate as well as recall; add simple context rules (negation, past tense) only if false alarms are high. |
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
