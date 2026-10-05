# Emergency check: results

Measured 5 Oct 2026. A missed emergency (false negative) is the costly error, so it comes first.

## What the app does

Eleven written rules run first, each quoting a published warning sign (MedlinePlus, CDC). If none fires, Qwen2.5-1.5B-Instruct is shown the full published list and asked whether the message describes any of those signs happening now. If either fires, the app shows "Seek emergency care now" and nothing else runs.

## Results

**Real posts:** 362 r/AskDocs posts from the PMR-Reddit test set, with urgency levels read off replies from verified clinicians. 38 are emergencies (level 1); 293 are ordinary (levels 4–6).

| Option | Missed emergencies (of 38) | Ordinary posts wrongly flagged (of 293) | Usable? |
|---|---|---|---|
| Rules alone | 26 (68%, 95% CI 51–82%) | 33 (11%) | Misses too many |
| **Rules plus Qwen (the app)** | **13 (34%, 95% CI 20–51%)** | **58 (20%)** | **Best balance** |
| Fine-tuned classifier, set to catch about 80% | 7 (18%) | 89 (30%) | Too many false alarms; flags nearly every short message |
| Fine-tuned classifier, set to catch about 90% | 3 (8%) | 142 (48%) | Flags half of everything |
| Simple classifier trained on a synthetic set | 8 (21%) | 103 (35%) | Flags any mention of a symptom |

**Cases we wrote:** 80 short messages in `data/synthetic/emergency_cases.csv`, 40 emergencies (15 direct, 25 paraphrased) and 40 non-emergencies.

| Option | Missed emergencies (of 40) | False alarms (of 40) |
|---|---|---|
| Rules alone | 25 (62%) | 4 (10%) |
| **Rules plus Qwen (the app)** | **1 (2%, 95% CI 0–13%)** | **4 (10%)** |

The rules catch all 15 direct wordings and none of the 25 paraphrases. All four false alarms are rules firing on past events. The real-post table is the honest one: we wrote these cases ourselves, with paraphrases chosen to avoid the rules' wording.

## Datasets we looked at for a trained classifier

We searched Hugging Face, Kaggle, PhysioNet, Zenodo, Mendeley and the research literature. No open dataset has enough real, patient-written text with emergency labels.

| Dataset | Access | Why it doesn't solve this |
|---|---|---|
| PMR-Reddit: 1,221 real r/AskDocs posts, 126 emergencies | Open (CC BY-NC 4.0) | Right kind of text, too few emergencies. Used as the real-post test above |
| MIMIC-IV-ED: about 425,000 real emergency-department stays | Restricted: ethics course and signed data use agreement | Could not be obtained in time; complaints are nurse shorthand, not patient language |
| Yale emergency department data: 560,486 real visits | Open | Complaints are yes/no flags, with no sentences; everyone in it had already gone to an emergency department |
| IDinsight maternal-health messages: 12,688 | Open (MIT) | Machine-written and about pregnancy; a classifier trained on it treats any symptom as urgent |
| Other triage sets on Hugging Face and Kaggle | Open | Machine-written textbook cases, or too small (1,267 records; 45 vignettes) |

## Why this is hard

- **Endless wording.** The same emergency can be written in countless ways, and each new phrasing needs a new rule.
- **Pattern, not words.** A clinician sends someone to the emergency department for a pattern (a swollen calf, pain moving to the lower right abdomen, a fall while on blood thinners). The same words appear in ordinary posts, and telling them apart is close to diagnosis.
- **Little labelled data.** The only open set of real patient text has 126 emergencies.
- **So trained models trade one error for the other.** To catch about 90% of real emergencies, ours had to flag half of all ordinary posts.

The check therefore catches clearly stated warning signs. It does not detect emergencies, and every screen says to call 911 in one.

## Notes

- The trained classifiers were one-off experiments and are not in the code: DistilRoBERTa fine-tuned on the other 859 PMR-Reddit posts (88 emergencies), and TF-IDF + logistic regression on the IDinsight set.
- 38 real emergencies is a small sample, so the intervals are wide.
- Reproduce the rules and Qwen rows with `python scripts/check_emergency.py --llm --real`. The Qwen check adds about 1 second per request and only runs when Qwen is loaded.
