"""Routers: text in, one probability per label out (columns in LABELS order)."""

from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from .labels import LABEL2ID, LABELS


_FILLER = ENGLISH_STOP_WORDS | {"feel", "feeling", "feels", "felt", "like", "really", "just", "got", "getting", "having", "week", "weeks", "month", "months", "day", "days"}


class TfidfRouter:
    """The trained-from-scratch router: TF-IDF features and logistic regression."""

    def __init__(self, C: float = 10.0):
        self.pipeline = make_pipeline(
            TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, strip_accents="unicode"),
            LogisticRegression(C=C, max_iter=2000, class_weight="balanced"),
        )

    def fit(self, texts, labels, sample_weight=None) -> "TfidfRouter":
        ids = [LABEL2ID[label] for label in labels]
        self.pipeline.fit(list(texts), ids, logisticregression__sample_weight=sample_weight)
        return self

    def predict_proba(self, texts) -> np.ndarray:
        """Probabilities with one column per label, zero for any label unseen in training."""
        seen = self.pipeline.predict_proba(list(texts))
        proba = np.zeros((seen.shape[0], len(LABELS)))
        proba[:, self.pipeline.classes_] = seen
        return proba

    def evidence(self, text: str, label: str, k: int = 3) -> list[str]:
        """The words in the text that pushed hardest toward this label."""
        vectorizer, model = self.pipeline[0], self.pipeline[-1]
        classes = list(model.classes_)
        if LABEL2ID[label] not in classes:
            return []
        weighted = vectorizer.transform([text]).multiply(model.coef_[classes.index(LABEL2ID[label])]).tocoo()
        names = vectorizer.get_feature_names_out()
        words: list[str] = []
        for i in np.argsort(-weighted.data):
            if weighted.data[i] <= 0 or len(words) == k:
                break
            # Keep the meaningful words of the feature: "my ears" -> "ears"; skip pure filler.
            content = " ".join(w for w in names[weighted.col[i]].split() if len(w) > 2 and w not in _FILLER)
            if content and not any(content in seen or seen in content for seen in words):
                words.append(content)
        return words

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, path)

    @classmethod
    def load(cls, path: Path) -> "TfidfRouter":
        router = cls()
        router.pipeline = joblib.load(path)
        return router


class EncoderRouter:
    """A fine-tuned encoder router, loaded from a folder written by scripts/train_encoder.py."""

    def __init__(self, folder: Path, max_length: int = 512, batch_size: int = 32):
        import torch  # imported here so the from-scratch router works without PyTorch installed
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(folder)
        self.model = AutoModelForSequenceClassification.from_pretrained(folder).to(self.device).eval()
        if [self.model.config.id2label[i] for i in range(len(LABELS))] != LABELS:
            raise ValueError(f"{folder} was trained with a different label list.")
        self.max_length, self.batch_size = max_length, batch_size

    def predict_proba(self, texts) -> np.ndarray:
        texts = list(texts)
        chunks = []
        with self.torch.inference_mode():
            for start in range(0, len(texts), self.batch_size):
                batch = self.tokenizer(texts[start:start + self.batch_size], truncation=True, max_length=self.max_length,
                                       padding=True, return_tensors="pt").to(self.device)
                chunks.append(self.torch.softmax(self.model(**batch).logits, dim=-1).float().cpu().numpy())
        return np.concatenate(chunks)
