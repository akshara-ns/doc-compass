"""Fine-tune an encoder router (all weights) with the transformers Trainer.

Stage 1 trains on the public Patient Comments set. The best epoch is chosen on a
validation share of that set, and the held-out share is scored once at the end.

Run:  python scripts/train_encoder.py --model distilroberta
      python scripts/train_encoder.py --model biomedbert
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import f1_score
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
                          Trainer, TrainingArguments)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doccompass import paths
from doccompass.labels import LABEL2ID, LABELS
from doccompass.metrics import describe, score
from doccompass.router import EncoderRouter
from doccompass.splits import SEED, public_split

ENCODERS = {  # revisions pinned so a rerun starts from the same weights
    "distilroberta": {"repo": "distilbert/distilroberta-base", "revision": "fb53ab8802853c8e4fbdbcd0529f21fc6f459b2b"},
    "biomedbert": {"repo": "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext", "revision": "e1354b7a3a09615f6aba48dfad4b7a613eef7062"},
}
MAX_LENGTH = {1: 64, 2: 512}  # stage 1 comments are one sentence; stage 2 posts are long


class TextDataset(torch.utils.data.Dataset):
    def __init__(self, frame, tokenizer, max_length):
        self.encodings = tokenizer(list(frame["text"]), truncation=True, max_length=max_length)
        self.labels = [LABEL2ID[label] for label in frame["label"]]

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, index):
        return {**{key: values[index] for key, values in self.encodings.items()}, "labels": self.labels[index]}


class WeightedTrainer(Trainer):
    """Cross-entropy weighted by class, so small specialties count as much as large ones."""

    def __init__(self, *args, class_weights, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        loss = torch.nn.functional.cross_entropy(outputs.logits, labels, weight=self.class_weights.to(outputs.logits.device))
        return (loss, outputs) if return_outputs else loss


def balanced_weights(frame) -> torch.Tensor:
    counts = frame["label"].map(LABEL2ID).value_counts().reindex(range(len(LABELS)), fill_value=0)
    weights = len(frame) / (len(LABELS) * counts.clip(lower=1))
    return torch.tensor(weights.to_numpy(), dtype=torch.float)


def validation_scores(prediction) -> dict:
    predicted = prediction.predictions.argmax(axis=1)
    return {"accuracy": float((predicted == prediction.label_ids).mean()),
            "macro_f1": float(f1_score(prediction.label_ids, predicted, labels=range(len(LABELS)), average="macro", zero_division=0))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", choices=ENCODERS, required=True)
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--lr", type=float, default=3e-5)
    args = parser.parse_args()
    stage = 1
    encoder = ENCODERS[args.model]
    train, val, held_out = public_split()

    tokenizer = AutoTokenizer.from_pretrained(encoder["repo"], revision=encoder["revision"])
    model = AutoModelForSequenceClassification.from_pretrained(
        encoder["repo"], revision=encoder["revision"], num_labels=len(LABELS),
        id2label=dict(enumerate(LABELS)), label2id=LABEL2ID)

    batch_size = 32
    steps = (len(train) // batch_size + 1) * args.epochs
    run_dir = paths.MODELS / f"{args.model}_stage{stage}_run"
    trainer = WeightedTrainer(
        model=model,
        args=TrainingArguments(
            output_dir=str(run_dir), num_train_epochs=args.epochs, learning_rate=args.lr, weight_decay=0.01,
            warmup_steps=int(0.1 * steps), per_device_train_batch_size=batch_size, per_device_eval_batch_size=64,
            eval_strategy="epoch", save_strategy="epoch", save_total_limit=1, load_best_model_at_end=True,
            metric_for_best_model="macro_f1", greater_is_better=True, logging_strategy="epoch",
            report_to="none", seed=SEED, dataloader_pin_memory=False),
        train_dataset=TextDataset(train, tokenizer, MAX_LENGTH[stage]),
        eval_dataset=TextDataset(val, tokenizer, MAX_LENGTH[stage]),
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=validation_scores,
        class_weights=balanced_weights(train),
    )
    started = time.time()
    trainer.train()
    seconds = time.time() - started
    val_scores = trainer.evaluate()

    out_dir = paths.MODELS / f"{args.model}_stage{stage}"
    trainer.save_model(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
    shutil.rmtree(run_dir, ignore_errors=True)

    # Score the saved model the same way the app will use it.
    router = EncoderRouter(out_dir, max_length=MAX_LENGTH[stage])
    result = score(router.predict_proba(held_out["text"]), held_out["label"].map(LABEL2ID).to_numpy())
    print(describe(f"{args.model} stage {stage}, public held-out", result))
    (out_dir / "metrics.json").write_text(json.dumps({
        "model": encoder, "stage": stage, "epochs": args.epochs, "learning_rate": args.lr, "seed": SEED,
        "train_rows": len(train), "val_rows": len(val), "fit_seconds": round(seconds),
        "val": {key: round(float(value), 4) for key, value in val_scores.items() if key in ("eval_accuracy", "eval_macro_f1")},
        "held_out": result, "device": router.device,
    }, indent=2))
    print(f"Saved {out_dir.relative_to(paths.ROOT)} ({seconds:.0f} s of training)")


if __name__ == "__main__":
    main()
