# Doc Compass

*Which doctor do I book?*

Describe a health concern in plain language. The app removes identifying details, checks for emergency symptoms, and suggests which kind of doctor to book (top 3, with "Start with a GP" as an option). It routes; it does not diagnose.

CMU 24-679 Project 1 · Akshara (`akshara-ns`) and Sohum (`ssg1`)

## Pipeline

1. **Red-flag check**: written rules; emergencies go straight to "Seek emergency care now"
2. **Redact**: Presidio, a CRF, and optionally DistilBERT
3. **Route**: TF-IDF + logistic regression, fine-tuned DistilRoBERTa vs BiomedBERT
4. **Explain**: Qwen2.5-1.5B-Instruct, using the redacted text only

Deployed as a Gradio app on a ZeroGPU Hugging Face Space (link to come).

## Data rules

- Never commit post text. Labelled data is shared as labels + MediQ ids only.
- Keep synthetic data in `data/synthetic/`, separate from our manual labels.
- Keep API keys and tokens out of the repo.

The full plan lives in `../which-doctor-do-i-book.md`.
