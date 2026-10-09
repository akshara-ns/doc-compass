# Report inputs from Sohum

Written 9 Oct 2026 for the Project 1 report. It holds what was only on Sohum's machine: his working log, the brief he saved, and the details of work that isn't in the repo. Numbers come from files, logs or runs; anything else is marked **Sohum to confirm**. It does not repeat `docs/plan.md` or `docs/routing-results.md`.

## 1. GenAI log

**Tools.** Claude Code (Anthropic's coding assistant) in VS Code, for almost everything below. Gemini was used early on to brainstorm the initial strategy; two of its suggestions on training were checked against the data before use. Qwen is part of the product, not a development aid. A Groq API key was set up and never used.

| Used for | What it did | How it went |
|---|---|---|
| Checking the plan | Downloaded every dataset and model the plan named and compared them with the plan | Found two wrong figures: 10,366 unique MediQ posts, not ≈13.5k; Nemotron-PII is 100k rows per split |
| Finding data | Searched Hugging Face, then Kaggle, PhysioNet, Zenodo and Mendeley, for a "which doctor" dataset and later for emergency data | First answer was "nothing usable exists"; Sohum pushed back with three names and one (Patient Comments) turned out to be usable. Lesson: it had only searched one site |
| Data mapping | Drafted the label set and the mapping of the 68 Patient Comments categories; both authors approved it | Worked. A first count of 6,716 unique comments was wrong; a stricter duplicate check gave 6,252 |
| Pilot labels | Gave 60 posts a first-pass label to size the problem (section 3) | Useful for planning only; never checked by a person |
| Code | The `doccompass` package, training and measuring scripts, the labelling tool, tests, the Colab notebook and the publish script, all on 4–5 Oct | Worked, with the bugs listed below |
| Figure and slides | Recovered the figure's build script from git history and adapted it; wrote the slide draft that Akshara turned into the deck | The slide draft had three overstatements that a re-check caught |
| Debugging | Each bug below | Most were caught by re-running against real data, not by reading the code |
| Review | On 9 Oct, re-scored the published stage-2 models against `docs/routing-results.md` | Every checked number matched |

**What went wrong or had to be redone**

- The first Hugging Face upload silently routed everything to "Start with a GP": the code could not find its models when read from the Hugging Face cache. Found only because the notebook's steps were re-run against the published copy.
- Qwen wrote diagnoses ("consistent with a ligament tear") until its output was forced into one sentence pattern and the checks were tightened. One check also misread "Neurology" as "Urology".
- The emergency rules missed common phrasings, and "I don't want to die from this" raised a false alarm. Akshara's review found these; her proposed negation fix would have silenced "I don't know why but I have chest pain", so a stricter rule was used.
- "left face stroke" was routed to Dermatology: the stroke rule matched signs but not the word itself.
- The 80 emergency cases the assistant wrote made the check look far better (1 of 40 missed) than real posts did (13 of 38 missed).
- Advice to skip reviewing train labels if time ran short was wrong: unreviewed labels are not manual data.
- The slide draft said three model types do routing (two do), "under a second" (about 3 seconds with Qwen), and that BiomedBERT was trained on clinicians' text (it is biomedical papers).

**For the reflection.** The assistant was fast and usually right about code, and confidently wrong about things it had not measured. Every correction above came from measuring on real data or from a person pushing back. The rule that helped most: no number goes in a document unless a run produced it.

**What `proj.txt` is.** A local copy of the Project 1 brief, the presentation guide and the report template, pasted from the course site. It is not in the repo. Its report requirements are in section 9.

## 2. What I built on 4–5 Oct and why

| Decision | Alternatives considered | Why this one |
|---|---|---|
| **Two-stage training:** stage 1 on public comments, stage 2 on our posts | Train on our posts only; use MedRedQA's answerer flair as labels; mix both sets in one run | Stage 1 needs none of our labels, so the whole app worked on 4 Oct, before any labelling. MedRedQA's flair says who answered, not where to book |
| **Remap Patient Comments to our labels:** 39 categories to a specialty, 16 to "Start with a GP", 13 dropped | Use its own 29 specialist types; skip the set | One label list for both stages, so the model's output layer never changes. Some source mappings were debatable (persistent fatigue → oncologist). Dropped categories were about infants or the elderly, or mixed in emergencies |
| **Qwen2.5-1.5B writes the explanation, with safeguards** | A hosted LLM API; free-form generation; fixed wording only | Runs locally, so no text leaves the app. Free-form text slipped in diagnoses, so the reason must follow one sentence pattern, and it is rejected if it diagnoses, guesses a cause, uses a number, names a medicine or names a doctor the router didn't pick. One retry, then fixed wording. The choice of doctor and its confidence always come from code |
| **A second emergency layer with Qwen** | More rules; a trained classifier (tried, see section 4); a smaller LLM (not tried) | Rules cannot match paraphrases. Qwen was already loaded, and no dataset supports a trained classifier |
| **App drawn as a wayfinding sign** (blue one answer, amber two options, red emergency) | Gradio's default label component, used in the first version | One loud element, the door to knock on; the top three stay quiet underneath. Two options when unsure, so the app never pretends to be sure |
| **Colab notebook with a public link** | A Hugging Face Space (now needs a paid plan); a link from a laptop; Streamlit Community Cloud (kept for later); Gradio-Lite (no longer maintained) | Free, runs all three model types, and the presentation guide accepts it. The code and models sit in a public Hugging Face repo because the GitHub repo is private |

Other pieces from those two days: the data prep (dedupe on text, one id per post), the choice of the 734 posts with a `draw` column, the labelling tool, the from-scratch and fine-tuned stage-1 routers, the measuring script for the emergency check, and 48 tests.

## 3. The 60-post pilot

- **What:** 60 MediQ_AskDocs posts, sampled with a fixed seed (24679) from the 9,118 unique posts of 25–400 words.
- **Who labelled:** the AI assistant (Claude Code), reading the first 85 words of each post. No person checked these labels, and they were never used as training or test labels.
- **Result:** 20 "Start with a GP", 10 Skip, 6 Orthopedics, 5 ENT, 5 Urology, 4 Mental health, 4 Neurology, 2 Dermatology, 2 Cardiology, 1 Ob-Gyn, 1 Dentistry, 0 Gastroenterology, 0 Eye care.
- **What changed because of it:**
  - A Skip option, since about 1 in 6 posts was not a "which doctor" question.
  - A pool of 734 posts, not 600, to leave room for skips.
  - Train posts picked so that each specialty gets examples, because a random sample would be about 40% GP. Test stayed a plain random sample.
  - Dentistry and Eye care were kept in the label set despite 0–1 pilot posts, because they are booked directly in the US.

## 4. Emergency-check experiments not in the repo

Both were one-off scripts run on 5 Oct on Sohum's laptop (Apple M4, PyTorch on MPS). **The code no longer exists:** it lived in a temporary folder and was deleted that day once we decided to keep rules plus Qwen only. The settings below are from the run logs.

**A. DistilRoBERTa fine-tuned on PMR-Reddit**

| | |
|---|---|
| Data | PMR-Reddit train and dev pool (`PortalPal-AI/PMR-Reddit-Train-Dev-Pool`): 859 posts, 88 emergencies (urgency level below 2) |
| Split | 80/20, stratified, seed 24679: 687 train posts (70 emergencies), 172 validation posts (18 emergencies) |
| Model | `distilbert/distilroberta-base` at revision `fb53ab88`, two classes, all weights trained |
| Settings | 6 epochs, learning rate 3e-5, weight decay 0.01, 25 warm-up steps, batch size 16, max length 384, loss weighted by class, best epoch by validation AUC. 343 seconds |
| Quality | Validation AUC 0.79, test AUC 0.82 |
| Operating points | The threshold is the lowest score that still catches about 90% (or 80%) of the validation emergencies: 0.006 and 0.008 |
| Test | The 362 PMR-Reddit test posts (38 emergencies, 293 at levels 4–6). At 90%: 3 missed, 142 flagged. At 80%: 7 missed, 89 flagged |
| On our 80 written cases | 0 of 40 missed, but 40 and 38 of the 40 non-emergencies flagged. It does not transfer to short messages |

**B. TF-IDF + logistic regression on the IDinsight set**

| | |
|---|---|
| Data | `IDinsight/urgency_detection_maternal_health_synthetic`: 12,688 unique machine-written messages, 9,629 urgent and 3,059 not urgent |
| Split | 85/15, stratified, seed 24679 |
| Settings | Word 1–2-grams, minimum document frequency 2, sublinear TF; logistic regression with C = 10 and balanced class weights; default threshold of 0.5 |
| Quality | 98.8% accuracy and AUC 0.999 on its own held-out messages |
| On real posts | 8 of 38 emergencies missed, 103 of 293 ordinary posts flagged, AUC 0.73 |
| On our 80 written cases | 7 of 40 missed, 16 of 40 false alarms |

**Also tried, not cited in the results doc:** the same TF-IDF model trained on the 859 PMR-Reddit posts. Threshold 0.09, set by 5-fold cross-validation to catch about 90%. Cross-validation AUC 0.78, test AUC 0.80; 3 of 38 missed with 179 of 293 flagged; on our written cases 9 of 40 missed and 20 of 40 false alarms.

## 5. The explanation check ("15 of 16")

- **Inputs:** 16 made-up concerns, written for the test. None is a real post.
  1. I've had an itchy red rash on both shins for about three weeks and creams from the pharmacy haven't helped.
  2. My right knee swells and hurts after I run, and it clicks when I climb stairs.
  3. I've been feeling very sad and anxious for weeks and I can't focus on anything.
  4. My ears have been ringing for a week and my throat is sore when I swallow.
  5. I get a burning feeling when I pee and I have to go all the time.
  6. My period is two weeks late and I have cramps
  7. I have a lump in my armpit that hasn't gone away and I'm scared
  8. My gums bleed when I brush
  9. My vision has been blurry when reading for a month
  10. I get heartburn after every meal
  11. I've been having heart palpitations when I lie down
  12. My lower back has hurt for months, worse when I sit
  13. I keep getting headaches behind my eyes every afternoon
  14. My tooth hurts when I drink cold water
  15. I feel tired all the time and I don't know why
  16. My skin is peeling on my hands and it stings
- **How it was run:** on 4 Oct, through the full pipeline with the stage-1 DistilRoBERTa router and Qwen on the laptop. For each input, one attempt with fixed (greedy) decoding, then one sampled retry if the checks failed. An input "passed" if the app showed Qwen's text and not the fixed wording.
- **Result:** 15 of 16 passed; median 3.1 seconds, slowest 6.3 seconds.
- **Which one failed:** not recorded in the final run. In an earlier run, before two checks were corrected, numbers 12 and 13 failed on the first attempt: 12 for the phrase "would be best suited" and 13 because the check misread "Neurology" as "Urology". Both checks were then fixed.
- **Caveat:** the retry uses sampling, so the count can differ from run to run. It was measured with the stage-1 router and has not been re-run with the stage-2 one.

## 6. Presentation (5 Oct)

- The slide deck was built by Akshara from the draft in `docs/history/2026-10-04_slides-draft-revised.txt`.
- Someone in the audience found a concern that should have been an emergency and was routed to a specialty. Sohum had found the same kind of miss that morning ("left face stroke" went to Dermatology). This led to the second emergency layer and the measurements in `docs/emergency-check-results.md`.
- Another question: some specialists can never be booked directly and must go through a GP, so what is the tool for? Sohum's answer: it is a self-help assistant. It makes you aware of the care path you are on, so you can tell whether you are being routed to the right destination.
- What the audience member typed for the missed emergency was not recorded.
- Demo video: Sohum planned to screen-record the app. Whether it exists and where it is: **Sohum to confirm.**

## 7. Contributions

- **In the repo:** 11 commits on 4–5 Oct, plus the merge of `sg` into `main`. They cover everything in section 2: the package, the stage-1 routers, the Qwen explanation, both emergency layers and their measurement, the app design, the Colab notebook and the first published bundle, the label set and mapping, the choice of posts, the 4 Oct system figure, and the slide draft.
- **Outside the repo:** the dataset checks and searches, the two emergency-classifier experiments, and on 9 Oct the check that the stage-2 results reproduce.

## 8. My reflection

A draft from the working log, for Sohum to edit.

- **Went well.** Getting the whole app working on public data before any labels existed meant the demo was real, and it showed exactly where public data breaks. Measuring missed emergencies on real, clinician-labelled posts changed what we claim: the check catches clearly stated warning signs, it does not detect emergencies.
- **Went poorly.** We trusted cases we wrote ourselves (1 of 40 emergencies missed) until real posts showed 13 of 38 missed. The emergency rules went to the presentation with gaps that someone in the audience found. Labelling started late, so the test set is 115 posts and three labels have one test post each.
- **Would do differently.** Label a small real test set in the first days, before building anything, and measure everything against it. Write the emergency test cases before the rules, and have someone else write them. Keep throwaway experiment code, since the report needed it.

## 9. Report requirements (from `proj.txt`)

- **Submission:** a PDF file upload, 50 points, "Due Friday by 11:59pm" (the file gives no date; **Sohum to confirm**). No page or word limit is stated except for the executive summary.
- **GenAI log:** no template. It is one question under "Reflection and Next Steps": how GenAI supported the work on the project itself (not what is built into the product), whether it worked well or poorly, and what was learned.

| Section | Points | What "excellent" asks for |
|---|---|---|
| Title page | 2 | Title, all names, date; clean formatting |
| Executive summary | 6 | Under 200 words: problem, approach, key result, impact |
| Introduction and motivation | 10 | The task, why it matters, the current workflow with its pains, and concrete success criteria with measurable targets |
| Design process | 20 | Prioritised success criteria with trade-offs; a clear, labelled end-to-end figure (data → models → interface); data collection, curation and augmentation (sources, size, splits, labelling, quality checks, ethics); trained vs off-the-shelf choices justified, with training details and selection criteria; interface design, key screens, states and error handling, and why the framework fits |
| User experience and workflow | 8 | Step-by-step walkthrough with screenshots; inputs, outputs, states and user decisions; tied back to the success criteria with evidence |
| Reflection and next steps | 4 | Candid limits, risks and failure modes; prioritised next steps with their expected effect on the success criteria |

The brief's four requirements: functional and useful, with the need and the way performance is measured both justified; at least 500 manually collected or curated samples, with synthetic or augmented data stored separately; at least two of the three model types (from scratch, fine-tuned, off-the-shelf); a public GUI if possible.
