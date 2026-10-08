"""Fine-tune an encoder router (all weights) with the transformers Trainer.

Stage 1 trains on the public Patient Comments set. The best epoch is chosen on a
validation share of that set, and the held-out share is scored once at the end.
Stage 2 continues from the stage-1 checkpoint on our own gold training posts and keeps the
epoch with the best macro-F1 on our dev posts. With --from-base it starts from the original
weights instead (gold only), for comparison. Our test posts are never used here.

Run:  python scripts/train_encoder.py --model distilroberta
      python scripts/train_encoder.py --model distilroberta --stage 2
      python scripts/train_encoder.py --model distilroberta --stage 2 --from-base
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
from doccompass.splits import SEED, gold_split, public_split

ENCODERS = {  # revisions pinned so a rerun starts from the same weights
    "distilroberta": {"repo": "distilbert/distilroberta-base", "revision": "fb53ab8802853c8e4fbdbcd0529f21fc6f459b2b"},
    "biomedbert": {"repo": "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext", "revision": "e1354b7a3a09615f6aba48dfad4b7a613eef7062"},
}
MAX_LENGTH = {1: 64, 2: 384}  # stage 1 comments are one sentence; 384 covers most posts and fits in a laptop's memory


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
    parser.add_argument("--stage", type=int, choices=(1, 2), default=1)
    parser.add_argument("--from-base", action="store_true", help="stage 2 only: start from the original weights (gold only)")
    parser.add_argument("--epochs", type=int, help="default 4 for stage 1, 6 for stage 2")
    parser.add_argument("--lr", type=float, help="default 3e-5 for stage 1, 2e-5 for stage 2")
    args = parser.parse_args()
    stage = args.stage
    epochs = args.epochs or (4 if stage == 1 else 6)
    lr = args.lr or (3e-5 if stage == 1 else 2e-5)
    encoder = ENCODERS[args.model]
    if stage == 1:
        train, val, held_out = public_split()
        name, start = f"{args.model}_stage1", {"pretrained_model_name_or_path": encoder["repo"], "revision": encoder["revision"]}
    else:
        gold = gold_split()
        train, val, held_out = gold["train"], gold["dev"], None
        if args.from_base:
            name, start = f"{args.model}_gold", {"pretrained_model_name_or_path": encoder["repo"], "revision": encoder["revision"]}
        else:
            name, start = f"{args.model}_stage2", {"pretrained_model_name_or_path": str(paths.MODELS / f"{args.model}_stage1")}

    tokenizer = AutoTokenizer.from_pretrained(**start)
    model = AutoModelForSequenceClassification.from_pretrained(
        **start, num_labels=len(LABELS), id2label=dict(enumerate(LABELS)), label2id=LABEL2ID)

    # Stage 2 posts are long: small batches, with gradients added up over 2 steps, keep memory low.
    batch_size, accumulate = (32, 1) if stage == 1 else (4, 2)
    steps = (len(train) // (batch_size * accumulate) + 1) * epochs
    run_dir = paths.MODELS / f"{name}_run"
    trainer = WeightedTrainer(
        model=model,
        args=TrainingArguments(
            output_dir=str(run_dir), num_train_epochs=epochs, learning_rate=lr, weight_decay=0.01,
            warmup_steps=int(0.1 * steps), per_device_train_batch_size=batch_size, gradient_accumulation_steps=accumulate, per_device_eval_batch_size=8,
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

    out_dir = paths.MODELS / name
    trainer.save_model(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
    shutil.rmtree(run_dir, ignore_errors=True)

    # Score the saved model the same way the app will use it: public held-out in stage 1, our dev posts in stage 2.
    router = EncoderRouter(out_dir, max_length=MAX_LENGTH[stage])
    scored, where = (held_out, "public held-out") if stage == 1 else (val, "our dev posts")
    result = score(router.predict_proba(scored["text"]), scored["label"].map(LABEL2ID).to_numpy())
    print(describe(f"{name}, {where}", result))
    (out_dir / "metrics.json").write_text(json.dumps({
        "model": encoder, "stage": stage, "from": "base" if stage == 1 or args.from_base else "stage1",
        "epochs": epochs, "learning_rate": lr, "seed": SEED,
        "train_rows": len(train), "val_rows": len(val), "fit_seconds": round(seconds),
        "val": {key: round(float(value), 4) for key, value in val_scores.items() if key in ("eval_accuracy", "eval_macro_f1")},
        "held_out" if stage == 1 else "dev": result, "device": router.device,
    }, indent=2))
    print(f"Saved {out_dir.relative_to(paths.ROOT)} ({seconds:.0f} s of training)")


if __name__ == "__main__":
    main()
