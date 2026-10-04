# Label set and public-data mapping

Agreed on 4 Oct 2026. This is the single label list the code uses.

## Router labels

Eleven specialties plus "Start with a GP". One fixed list; both the public data and our own labels are converted through it.

| Label | Covers |
|---|---|
| Dermatology | skin, hair, nails |
| Orthopedics | bones, joints, muscles, back and neck, sports injuries, foot and ankle (podiatry is an acceptable alternate) |
| ENT | ear, nose, throat, sinuses |
| Gastroenterology | stomach, bowel, digestion, liver |
| Neurology | headaches, numbness or tingling, seizures, memory |
| Urology | urinary problems, male sexual and reproductive health |
| Ob-Gyn | periods, pregnancy, female reproductive health |
| Mental health | mood, anxiety, eating, addiction (psychiatry or counselling) |
| Cardiology | heart, palpitations, blood pressure |
| Eye care | vision and eye problems (ophthalmology or optometry) |
| Dentistry | teeth, gums, mouth |
| Start with a GP | cause unclear, several body systems, common first-visit complaints, or a specialty normally reached by referral (lungs, hormones, blood, allergy, rheumatology) |

**When labelling only** (not router classes):

- **Emergency**: needs emergency care now. The red-flag rules handle these before the router runs, so these posts test the rules and are not used to train the router.
- **Skip**: not a "which doctor" question (medication questions, lab-result questions, general curiosity, already under a specialist's care for it).

Each post also gets an optional alternate label, an urgency tier (emergency / soon / routine) and an ambiguous tick. When unsure, label "Start with a GP" and tick ambiguous.

## Pilot on 60 real posts

60 MediQ_AskDocs posts, sampled with a fixed seed from the 9,118 unique posts of 25–400 words. The labels are a quick first pass on the first 85 words of each post and were not double-checked, so treat the counts as a rough guide.

| First-pass label | Posts |
|---|---:|
| Start with a GP | 20 |
| Skip | 10 |
| Orthopedics | 6 |
| ENT | 5 |
| Urology | 5 |
| Mental health | 4 |
| Neurology | 4 |
| Dermatology | 2 |
| Cardiology | 2 |
| Ob-Gyn | 1 |
| Dentistry | 1 |
| Gastroenterology, Eye care | 0 |

What this suggests:

- About 1 in 6 posts is a skip, so the pool must be larger than 600.
- "Start with a GP" is about 40% of usable posts. A purely random 600 would leave some specialties with very few examples.
- The 150 test posts stay a plain random sample. The train and dev posts are chosen so each specialty gets enough examples.

## Mapping the public Patient Comments set

Source: Patient Comments and Specialist Types (Mendeley Data, DOI 10.17632/2twgjzpn82.2, CC BY 4.0). Its 68 symptom categories are each mapped to one of our labels, to "Start with a GP", or dropped. Row counts are from its two files combined (8,441 rows).

**Mapped to a specialty**

| Our label | Public categories (rows) |
|---|---|
| Dermatology | Acne (330), Skin issue (275), Hair falling out (264), Changes in Skin (46), Nails issue (26) |
| Orthopedics | Knee pain (326), Joint pain (324), Shoulder pain (318), Muscle pain (290), Back pain (273), Neck pain (255), Injury from sports (239), Foot ache (233), Ankle pain (47), Foot pain (42), Arthralgia (29) |
| ENT | Ear ache (276) |
| Gastroenterology | Stomach ache (275), Liver issues (34) |
| Neurology | Head ache (279), Memory disturbance (101), Difficulty speaking (34), Seizures (32), Dementia (32), Brain tumors (28) |
| Urology | Urinary issue (33), Infertility in men (32) |
| Ob-Gyn | Pregnancy issues (32), Abnormal bleeding (31), Infertility (30) |
| Mental health | Emotional pain (242), mood swing (53), Behavioral issues (26), Addiction (25) |
| Cardiology | Heart hurts (288) |
| Eye care | Blurry vision (256), Eye Infection (26) |
| Dentistry | Bad breath (37), Toothache (35) |

**Mapped to "Start with a GP"**

| Public category | Rows | Why |
|---|---:|---|
| Cough | 302 | common first-visit complaint |
| Feeling dizzy | 295 | many possible causes |
| Feeling cold | 269 | many possible causes |
| Body feels weak | 247 | many possible causes |
| Hard to breath | 242 | GP or urgent care first; lung specialist by referral |
| Internal pain | 254 | location unclear |
| Infected wound | 310 | GP or urgent care handles wound care |
| diabetes | 54 | endocrinology by referral |
| Blood related | 48 | hematology by referral |
| Allergic reactions | 37 | allergist by referral |
| Asthma | 36 | GP manages first |
| Lower back or pelvic pain | 35 | could be orthopedic, urinary or gynecological |
| Autoimmune diseases | 34 | rheumatology by referral |
| Swelling | 28 | many possible causes |
| Unexplained Fever/ Bruising | 26 | many possible causes |
| Persistent fatigue | 25 | many possible causes |

**Dropped**

| Public category | Rows | Why |
|---|---:|---|
| Open wound | 217 | mixes in emergencies |
| vaccinations | 51 | about infants |
| growth issue | 50 | about children |
| Old age | 40 | about elderly patients |
| Spinal cord injuries | 37 | mixes in emergencies |
| Face deformation | 36 | plastic surgery, out of scope |
| Accidents | 34 | plastic surgery, out of scope |
| Neonatal infections | 34 | about newborns |
| Jaundice | 31 | about newborns |
| Premature birth | 31 | about newborns |
| Movement problems | 29 | about elderly patients |
| Cardiac issues in newborns | 28 | about newborns |
| Burns | 27 | burn care, out of scope |

**Result:** 645 rows dropped, 7,796 kept, 6,252 unique comments after removing emoji and duplicates (3 comments that sat under two conflicting labels are dropped too).

| Label | Unique comments |
|---|---:|
| Orthopedics | 1,867 |
| Start with a GP | 1,792 |
| Dermatology | 734 |
| Neurology | 451 |
| Mental health | 284 |
| Gastroenterology | 247 |
| Eye care | 220 |
| Cardiology | 215 |
| ENT | 212 |
| Ob-Gyn | 93 |
| Dentistry | 72 |
| Urology | 65 |

## Known limits

1. **Debatable mappings.** Cough, asthma, hard to breathe and allergic reactions go to "Start with a GP"; headache goes to Neurology; foot and ankle go to Orthopedics.
2. **Imbalance.** Orthopedics and "Start with a GP" make up 59% of the public set; Urology, Dentistry and Ob-Gyn are under 100 each. Our own labels need to cover those three well.
3. **Known noise.** The public labels come from the category, not from each comment, and some rows are mislabelled at source (a "Knee pain" row describes choking when coughing).
