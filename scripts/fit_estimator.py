"""Fit per-feature token weights (non-negative least squares) so a token count can be estimated without a tokenizer.

The features match estimateTokens() in the AICostBudget Token Calculator. Each category gets equal total weight
in the fit, so the 416 blog paragraphs do not drown out the 11 Chinese ones.

Usage: python scripts/fit_estimator.py [--encoding o200k_base] [--out results/estimator-weights-o200k_base.json]
"""
import argparse, json, re, unicodedata
from pathlib import Path
import numpy as np, tiktoken
from scipy.optimize import nnls

ROOT = Path(__file__).resolve().parent.parent
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af\uf900-\ufaff\u3000-\u303f\uff00-\uffef]")
LATIN = re.compile(r"[A-Za-z\u00c0-\u024f]+")
ASCII_PUNCT = re.compile(r"[!-/:-@\[-`{-~]")
NAMES = ["cjkChar", "otherScriptLetter", "latinWord", "longWordLetter", "digit", "asciiPunctuation",
         "otherSymbol", "whitespaceRun", "shortWord", "capitalizedWord", "camelBoundary"]


def is_letter_or_mark(ch):
    return unicodedata.category(ch)[0] in "LM"


def features(text):
    rest = CJK.sub("", text)
    words = LATIN.findall(rest)
    return [
        len(CJK.findall(text)),                                              # CJK characters
        sum(1 for ch in LATIN.sub("", rest) if is_letter_or_mark(ch)),       # Cyrillic, Greek, Arabic... letters
        len(words),                                                          # runs of Latin letters
        sum(max(0, len(w) - 10) for w in words),                             # letters past the 10th in one run
        sum(1 for ch in rest if unicodedata.category(ch) == "Nd"),           # digits
        len(ASCII_PUNCT.findall(rest)),                                      # ASCII punctuation
        sum(1 for ch in rest if not ch.isspace() and not is_letter_or_mark(ch)
            and unicodedata.category(ch) != "Nd" and not ASCII_PUNCT.match(ch)),  # emoji and other symbols
        len(re.findall(r"[ \t]{2,}", rest)),                                 # indentation runs
        sum(1 for w in words if len(w) <= 3),                                # short words
        sum(1 for w in words if w[0].isupper()),                             # capitalized words
        len(re.findall(r"[a-z][A-Z]", rest)),                                # camelCase boundaries
    ]


parser = argparse.ArgumentParser()
parser.add_argument("--encoding", default="o200k_base")
parser.add_argument("--out", default=None)
args = parser.parse_args()

enc = tiktoken.get_encoding(args.encoding)
samples = [json.loads(line) for line in open(ROOT / "data" / "samples.jsonl", encoding="utf8")]
X = np.array([features(s["text"]) for s in samples], float)
y = np.array([len(enc.encode(s["text"])) for s in samples], float)
cats = np.array([s["category"] for s in samples])
sw = np.sqrt(np.array([1.0 / y[cats == c].sum() for c in cats]))

weights = np.round(nnls(X * sw[:, None], y * sw)[0], 2)
pred = np.ceil(np.maximum(X @ weights, 1))
ratio = {c: round(float(pred[cats == c].sum() / y[cats == c].sum()), 3) for c in sorted(set(cats))}

even = np.arange(len(y)) % 2 == 0
half = nnls(X[even] * sw[even, None], y[even] * sw[even])[0]
odd_pred = X[~even] @ half
holdout = {c: round(float(odd_pred[cats[~even] == c].sum() / y[~even][cats[~even] == c].sum()), 3)
           for c in sorted(set(cats)) if (cats[~even] == c).any()}

out = {"encoding": args.encoding, "tiktoken": tiktoken.__version__, "weights": dict(zip(NAMES, weights.tolist())),
       "estimateOverActual": ratio, "holdoutEstimateOverActual": holdout}
target = Path(args.out) if args.out else ROOT / "results" / f"estimator-weights-{args.encoding}.json"
target.write_text(json.dumps(out, indent=2) + "\n", encoding="utf8")
print(json.dumps(out, indent=2))
